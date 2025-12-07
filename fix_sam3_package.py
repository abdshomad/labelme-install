#!/usr/bin/env python3
"""
Fix SAM3 package installation by copying missing modules.

This script fixes the incomplete SAM3 package installation by copying
missing submodules that aren't included in the package configuration.
"""

import os
import shutil
import sys
from pathlib import Path

def find_sam3_source():
    """Find the SAM3 source directory."""
    # Check common locations
    locations = [
        "/tmp/sam3",
        os.path.expanduser("~/sam3"),
        os.path.join(os.path.dirname(__file__), "sam3"),
    ]
    
    for loc in locations:
        if os.path.exists(os.path.join(loc, "sam3", "__init__.py")):
            return loc
    
    # Try to find it in the git cache
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            git_root = result.stdout.strip()
            sam3_path = os.path.join(git_root, "sam3")
            if os.path.exists(sam3_path):
                return git_root
    except:
        pass
    
    return None

def find_sam3_installed():
    """Find the installed SAM3 package location."""
    import site
    for site_packages in site.getsitepackages():
        sam3_path = os.path.join(site_packages, "sam3")
        if os.path.exists(sam3_path):
            return sam3_path
    
    # Also check in virtual environment
    venv_path = os.path.join(os.path.dirname(__file__), ".venv", "lib", "python3.9", "site-packages", "sam3")
    if os.path.exists(venv_path):
        return venv_path
    
    return None

def copy_missing_modules(source_dir, target_dir):
    """Copy missing SAM3 modules from source to installed location."""
    modules_to_copy = ["sam", "train", "perflib", "eval", "agent"]
    
    # Also copy model/utils subdirectory
    model_utils_source = os.path.join(source_dir, "sam3", "model", "utils")
    model_utils_target = os.path.join(target_dir, "model", "utils")
    if os.path.exists(model_utils_source):
        try:
            shutil.copytree(model_utils_source, model_utils_target, dirs_exist_ok=True)
            print(f"✓ Copied model/utils module")
        except Exception as e:
            print(f"⚠ Failed to copy model/utils: {e}")
    
    # Copy assets directory
    assets_source = os.path.join(source_dir, "assets")
    assets_target = os.path.join(os.path.dirname(target_dir), "assets")
    if os.path.exists(assets_source):
        try:
            shutil.copytree(assets_source, assets_target, dirs_exist_ok=True)
            print(f"✓ Copied assets directory")
        except Exception as e:
            print(f"⚠ Failed to copy assets: {e}")
    
    source_sam3 = os.path.join(source_dir, "sam3")
    if not os.path.exists(source_sam3):
        print(f"Error: Source sam3 directory not found at {source_sam3}")
        return False
    
    copied = []
    for module in modules_to_copy:
        source_module = os.path.join(source_sam3, module)
        target_module = os.path.join(target_dir, module)
        
        if os.path.exists(source_module) and not os.path.exists(target_module):
            try:
                shutil.copytree(source_module, target_module, dirs_exist_ok=True)
                copied.append(module)
                print(f"✓ Copied {module} module")
            except Exception as e:
                print(f"⚠ Failed to copy {module}: {e}")
        elif os.path.exists(target_module):
            print(f"⊘ {module} already exists")
    
    return len(copied) > 0

def main():
    print("SAM3 Package Fix Script")
    print("=" * 50)
    
    source_dir = find_sam3_source()
    if not source_dir:
        print("Error: Could not find SAM3 source directory")
        print("Please ensure SAM3 is cloned at /tmp/sam3 or in the project directory")
        return 1
    
    print(f"Source directory: {source_dir}")
    
    target_dir = find_sam3_installed()
    if not target_dir:
        print("Error: Could not find installed SAM3 package")
        return 1
    
    print(f"Target directory: {target_dir}")
    print()
    
    if copy_missing_modules(source_dir, target_dir):
        print()
        print("✓ SAM3 package fixed successfully!")
        return 0
    else:
        print()
        print("⚠ No modules were copied (they may already exist)")
        return 0

if __name__ == "__main__":
    sys.exit(main())

