"""File utilities for the exporter-agent."""
import os
from typing import Dict, List
from pathlib import Path

from logging_utils import get_logger

logger = get_logger()

def load_existing_exporter(path: str) -> Dict[str, str]:
    """
    Load existing exporter code files.
    
    Args:
        path: Path to the exporter code directory
        
    Returns:
        Dictionary mapping file paths to file contents
    """
    files = {}
    if not os.path.exists(path):
        logger.warning(f"Exporter path {path} does not exist")
        return files
        
    if os.path.isdir(path):
        for root, _, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith('.go'):
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, path)
                    try:
                        with open(file_path, 'r') as f:
                            files[rel_path] = f.read()
                            logger.debug(f"Loaded file: {rel_path}")
                    except Exception as e:
                        logger.error(f"Failed to read file {file_path}: {str(e)}")
    else:
        logger.warning(f"Exporter path {path} is not a directory")
        
    logger.info(f"Loaded {len(files)} Go files from {path}")
    return files


def analyze_exporter_structure(files: Dict[str, str]) -> Dict[str, any]:
    """
    Analyze the structure of an existing exporter.
    
    Args:
        files: Dictionary mapping file paths to file contents
        
    Returns:
        Dictionary with analysis results
    """
    # Initial empty analysis
    analysis = {
        "main_file": None,
        "collector_files": [],
        "package_name": None,
        "metrics": [],
        "imports": set(),
    }
    
    # Check each file
    for file_path, content in files.items():
        # Look for main function to identify main file
        if "func main(" in content:
            analysis["main_file"] = file_path
            
        # Look for collector files (contain metrics)
        if "prometheus.NewGauge" in content or "prometheus.NewCounter" in content:
            analysis["collector_files"].append(file_path)
            
        # Extract package name from first line
        if content.strip().startswith("package "):
            pkg_line = content.strip().split("\n")[0]
            pkg_name = pkg_line.replace("package ", "").strip()
            if analysis["package_name"] is None:
                analysis["package_name"] = pkg_name
                
        # Look for imports
        if "import (" in content:
            import_block = content.split("import (")[1].split(")")[0]
            for line in import_block.split("\n"):
                imp = line.strip().strip('"')
                if imp and not imp.startswith("//"):
                    analysis["imports"].add(imp)
    
    logger.info(f"Exporter analysis: found main file={analysis['main_file']}, " 
               f"{len(analysis['collector_files'])} collector files")
    return analysis