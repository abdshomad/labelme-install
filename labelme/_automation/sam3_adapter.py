"""
SAM3 Adapter for labelme.

This module provides an adapter that makes SAM3 compatible with the osam interface,
allowing SAM3 to be used directly in labelme without waiting for osam to support it.
"""

from __future__ import annotations

import os
from typing import Any, Literal, Optional

import numpy as np
import numpy.typing as npt
import torch
from loguru import logger

try:
    from sam3 import build_sam3_image_model
    from sam3.model.sam1_task_predictor import SAM3InteractiveImagePredictor
    SAM3_AVAILABLE = True
except ImportError:
    SAM3_AVAILABLE = False
    logger.warning("SAM3 not available. Install with: pip install git+https://github.com/facebookresearch/sam3.git")


# Mock osam types for compatibility
class BoundingBox:
    """Bounding box compatible with osam.types.BoundingBox."""
    def __init__(self, xmin: float, ymin: float, xmax: float, ymax: float):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax


class Annotation:
    """Annotation compatible with osam.types.Annotation."""
    def __init__(self, mask: npt.NDArray[np.bool_], bounding_box: Optional[BoundingBox] = None, score: float = 1.0):
        self.mask = mask
        self.bounding_box = bounding_box
        self.score = score


class GenerateResponse:
    """Response compatible with osam.types.GenerateResponse."""
    def __init__(self, annotations: list[Annotation]):
        self.annotations = annotations


class ImageEmbedding:
    """Image embedding wrapper for SAM3."""
    def __init__(self, predictor: SAM3InteractiveImagePredictor, image: np.ndarray):
        self.predictor = predictor
        self.image = image
        # Set image in predictor (this encodes the image)
        self.predictor.set_image(image)


class SAM3Model:
    """
    SAM3 model adapter that implements the osam.types.Model interface.
    """
    
    def __init__(self, model_name: str, device: Optional[str] = None):
        """
        Initialize SAM3 model.
        
        Args:
            model_name: Model name like 'sam3:small', 'sam3:latest', 'sam3:large'
            device: Device to run on ('cuda' or 'cpu'). Auto-detects if None.
        """
        self.name = model_name
        
        # Determine model variant
        if ":small" in model_name:
            variant = "small"
        elif ":large" in model_name:
            variant = "large"
        else:  # default to latest/medium
            variant = "latest"
        
        # Set device
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        logger.info(f"Loading SAM3 model: {variant} on {device}")
        
        # Build SAM3 model
        try:
            # build_sam3_image_model doesn't take model_type parameter
            # It builds a fixed model architecture. Model variants are determined by checkpoint.
            # For now, we'll use the default model. In the future, we can add checkpoint selection.
            # Enable inst_interactivity to get the interactive predictor
            self.model = build_sam3_image_model(
                device=device,
                eval_mode=True,
                enable_segmentation=True,
                enable_inst_interactivity=True,  # This creates inst_interactive_predictor
            )
            # SAM3Image model doesn't have image_size attribute directly
            # The predictor expects it, so we set a default or get it from the model
            # Default SAM3 image size is typically 1008
            if not hasattr(self.model, 'image_size'):
                self.model.image_size = 1008
            
            # Use the inst_interactive_predictor if available
            # However, the tracker built by build_sam3_image_model doesn't have a backbone
            # We need to create our own predictor with a backbone
            # Let's create a tracker with backbone and use that
            from sam3.model_builder import build_tracker
            from sam3.model.sam3_tracker_base import Sam3TrackerBase
            
            # Build tracker with backbone for the interactive predictor
            tracker = build_tracker(apply_temporal_disambiguation=False, with_backbone=True)
            # Share the backbone weights from the main model if possible
            if hasattr(tracker, 'backbone') and tracker.backbone is not None:
                # The tracker now has its own backbone, which is fine
                pass
            self.predictor = SAM3InteractiveImagePredictor(tracker)
            logger.info("Created SAM3InteractiveImagePredictor with backbone")
            
            logger.info(f"SAM3 model {variant} loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load SAM3 model: {e}")
            raise
    
    def encode_image(self, image: np.ndarray) -> ImageEmbedding:
        """
        Encode image and return embedding.
        
        Args:
            image: RGB image as numpy array (H, W, 3)
            
        Returns:
            ImageEmbedding object
        """
        # Convert to RGB if needed
        if image.dtype != np.uint8:
            image = (image * 255).astype(np.uint8)
        
        # Ensure RGB format
        if len(image.shape) == 3 and image.shape[2] == 3:
            pass  # Already RGB
        elif len(image.shape) == 2:
            # Grayscale to RGB
            image = np.stack([image] * 3, axis=-1)
        else:
            raise ValueError(f"Unsupported image shape: {image.shape}")
        
        # Use the model's interactive predictor (already created)
        # The predictor is shared, so we need to reset it for each new image
        self.predictor.reset_predictor()
        return ImageEmbedding(self.predictor, image)
    
    def generate(
        self,
        request: Any,  # osam.types.GenerateRequest
    ) -> GenerateResponse:
        """
        Generate masks from prompts.
        
        Args:
            request: GenerateRequest with image_embedding and prompt
            
        Returns:
            GenerateResponse with annotations
        """
        image_embedding: ImageEmbedding = request.image_embedding
        prompt = request.prompt
        
        # Get points from prompt
        if hasattr(prompt, 'points') and prompt.points is not None:
            points = prompt.points
            point_labels = getattr(prompt, 'point_labels', None)
        else:
            raise ValueError("Prompt must contain points")
        
        # Convert points to format expected by SAM3
        # SAM3 expects points as (N, 2) array in (x, y) format
        if len(points.shape) == 2 and points.shape[1] == 2:
            input_points = points
        else:
            raise ValueError(f"Unexpected points shape: {points.shape}")
        
        # Convert point labels (1 = foreground, 0 = background)
        if point_labels is not None:
            input_labels = point_labels.astype(np.int32)
        else:
            input_labels = np.ones(len(points), dtype=np.int32)
        
        # Run prediction
        try:
            # SAM3 predict returns (masks, iou_predictions, low_res_masks)
            # masks is in CxHxW format where C is number of masks
            masks, scores, _ = image_embedding.predictor.predict(
                point_coords=input_points,
                point_labels=input_labels,
                multimask_output=False,  # Return single best mask
                normalize_coords=False,  # Points are already in pixel coordinates
            )
            
            # Get the best mask (highest score)
            # masks shape: (C, H, W) where C=1 when multimask_output=False
            if masks.shape[0] > 0:
                best_idx = np.argmax(scores) if len(scores) > 0 else 0
                mask = masks[best_idx].astype(bool)
                score = float(scores[best_idx]) if len(scores) > 0 else 1.0
                
                # Compute bounding box from mask
                if np.any(mask):
                    rows = np.any(mask, axis=1)
                    cols = np.any(mask, axis=0)
                    if np.any(rows) and np.any(cols):
                        ymin, ymax = np.where(rows)[0][[0, -1]]
                        xmin, xmax = np.where(cols)[0][[0, -1]]
                        bbox = BoundingBox(float(xmin), float(ymin), float(xmax), float(ymax))
                    else:
                        bbox = None
                else:
                    bbox = None
                
                annotation = Annotation(mask=mask, bounding_box=bbox, score=score)
                return GenerateResponse(annotations=[annotation])
            else:
                logger.warning("No masks returned by SAM3")
                return GenerateResponse(annotations=[])
                
        except Exception as e:
            logger.error(f"SAM3 prediction failed: {e}")
            raise


def get_sam3_model_type(model_name: str):
    """
    Get SAM3 model type (factory function compatible with osam.apis.get_model_type_by_name).
    
    Args:
        model_name: Model name like 'sam3:small', 'sam3:latest', 'sam3:large'
        
    Returns:
        Model class that can be instantiated
    """
    if not SAM3_AVAILABLE:
        raise ImportError("SAM3 is not available. Install with: pip install git+https://github.com/facebookresearch/sam3.git")
    
    if not model_name.startswith("sam3:"):
        raise ValueError(f"Not a SAM3 model: {model_name}")
    
    class SAM3ModelType:
        """Model type factory for SAM3."""
        def __init__(self, name: str):
            self.name = name
        
        def __call__(self, *args, **kwargs):
            return SAM3Model(self.name, *args, **kwargs)
        
        @staticmethod
        def get_size():
            """Return model size in bytes (None = not downloaded, needs download)."""
            # SAM3 models are downloaded on first use via huggingface_hub
            # Return None to indicate they need to be downloaded
            return None
        
        def pull(self):
            """Download model (called by download_ai_model)."""
            # Models are downloaded automatically on first use
            # This is a no-op, but we could pre-download here if needed
            pass
    
    return SAM3ModelType(model_name)

