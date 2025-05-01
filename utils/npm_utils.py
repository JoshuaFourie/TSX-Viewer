"""
NPM utility functions for TSX Component Manager
"""
import subprocess
import platform
import logging
import os
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)

def is_npm_installed() -> bool:
    """
    Check if npm is installed
    
    Returns:
        True if npm is installed, False otherwise
    """
    try:
        is_windows = platform.system() == 'Windows'
        cmd = "npm --version" if is_windows else ["npm", "--version"]
        subprocess.check_output(cmd, shell=is_windows)
        return True
    except:
        return False

def is_node_installed() -> bool:
    """
    Check if Node.js is installed
    
    Returns:
        True if Node.js is installed, False otherwise
    """
    try:
        is_windows = platform.system() == 'Windows'
        cmd = "node --version" if is_windows else ["node", "--version"]
        subprocess.check_output(cmd, shell=is_windows)
        return True
    except:
        return False

def run_npm_command(command: str, cwd: str) -> Tuple[bool, str]:
    """
    Run an npm command in a specified directory
    
    Args:
        command: npm command to run
        cwd: Directory to run the command in
        
    Returns:
        Tuple of (success, output)
    """
    try:
        is_windows = platform.system() == 'Windows'
        full_cmd = f"npm {command}" if is_windows else ["npm"] + command.split()
        
        process = subprocess.Popen(
            full_cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=is_windows
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error running npm {command}: {stderr.decode('utf-8')}")
            return False, stderr.decode('utf-8')
        
        return True, stdout.decode('utf-8')
    except Exception as e:
        logger.error(f"Exception running npm {command}: {e}")
        return False, str(e)

def install_dependencies(directory: str, callback: Optional[callable] = None) -> bool:
    """
    Install npm dependencies in a directory
    
    Args:
        directory: Directory containing package.json
        callback: Optional callback function to report progress
        
    Returns:
        True if successful, False otherwise
    """
    try:
        is_windows = platform.system() == 'Windows'
        process = subprocess.Popen(
            "npm install" if is_windows else ["npm", "install"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=is_windows
        )
        
        # Monitor the installation progress
        while True:
            output = process.stdout.readline()
            if not output and process.poll() is not None:
                break
                
            if output and callback:
                callback(output.decode('utf-8').strip())
        
        if process.returncode != 0:
            error = process.stderr.read().decode('utf-8')
            logger.error(f"Error during npm install: {error}")
            if callback:
                callback(f"Error: {error}")
            return False
            
        return True
    
    except Exception as e:
        logger.error(f"Exception during npm install: {e}")
        if callback:
            callback(f"Error: {str(e)}")
        return False