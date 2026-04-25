#!/usr/bin/env python3
"""
Script Execution Engine for MCP_HpOneView Extended
Provides universal script execution capabilities for Ansible and PowerShell
"""

import os
import sys
import subprocess
import logging
import json
import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from enum import Enum

class ScriptType(Enum):
    """Supported script types"""
    PYTHON = "python"
    ANSIBLE = "ansible"
    POWERSHELL = "powershell"
    BASH = "bash"

class ExecutionResult:
    """Result of script execution"""
    def __init__(self, success: bool, stdout: str, stderr: str, 
                 return_code: int, execution_time: float):
        self.success = success
        self.stdout = stdout
        self.stderr = stderr
        self.return_code = return_code
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow().isoformat()

class ScriptExecutor:
    """Universal script execution engine"""
    
    def __init__(self, log_file: str = "mcp_script_executor.log"):
        self.logger = self._setup_logging(log_file)
        self.temp_dir = tempfile.mkdtemp(prefix="mcp_script_")
        self.logger.info(f"ScriptExecutor initialized with temp_dir: {self.temp_dir}")
    
    def _setup_logging(self, log_file: str) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("ScriptExecutor")
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger
    
    def execute_python_script(self, script_path: str, 
                             args: Optional[List[str]] = None,
                             env_vars: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Execute Python script"""
        self.logger.info(f"Executing Python script: {script_path}")
        
        cmd = [sys.executable, script_path]
        if args:
            cmd.extend(args)
        
        return self._execute_command(cmd, env_vars)
    
    def execute_ansible_playbook(self, playbook_path: str,
                                inventory: Optional[str] = None,
                                extra_vars: Optional[Dict[str, Any]] = None,
                                limit: Optional[str] = None,
                                tags: Optional[List[str]] = None,
                                check_mode: bool = False) -> ExecutionResult:
        """Execute Ansible playbook"""
        self.logger.info(f"Executing Ansible playbook: {playbook_path}")
        
        cmd = ["ansible-playbook", playbook_path]
        
        if inventory:
            cmd.extend(["-i", inventory])
        
        if check_mode:
            cmd.append("--check")
        
        if limit:
            cmd.extend(["--limit", limit])
        
        if tags:
            cmd.extend(["--tags", ",".join(tags)])
        
        if extra_vars:
            extra_vars_file = self._create_temp_vars_file(extra_vars)
            cmd.extend(["-e", f"@{extra_vars_file}"])
        
        return self._execute_command(cmd)
    
    def execute_powershell_script(self, script_path: str,
                                  args: Optional[List[str]] = None,
                                  env_vars: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Execute PowerShell script"""
        self.logger.info(f"Executing PowerShell script: {script_path}")
        
        # Determine PowerShell command based on platform
        if sys.platform == "win32":
            ps_cmd = ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File"]
        else:
            # Linux/macOS - use pwsh if available, fallback to powershell-core
            ps_cmd = ["pwsh", "-ExecutionPolicy", "Bypass", "-File"]
            if not self._command_exists("pwsh"):
                ps_cmd = ["powershell-core", "-ExecutionPolicy", "Bypass", "-File"]
        
        cmd = ps_cmd + [script_path]
        if args:
            cmd.extend(args)
        
        return self._execute_command(cmd, env_vars)
    
    def execute_bash_script(self, script_path: str,
                           args: Optional[List[str]] = None,
                           env_vars: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Execute Bash script"""
        self.logger.info(f"Executing Bash script: {script_path}")
        
        cmd = ["bash", script_path]
        if args:
            cmd.extend(args)
        
        return self._execute_command(cmd, env_vars)
    
    def _execute_command(self, cmd: List[str], 
                         env_vars: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Execute command and return result"""
        start_time = datetime.utcnow()
        
        try:
            # Prepare environment
            env = os.environ.copy()
            if env_vars:
                env.update(env_vars)
            
            self.logger.debug(f"Executing command: {' '.join(cmd)}")
            
            # Execute command
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=self.temp_dir
            )
            
            stdout, stderr = process.communicate()
            return_code = process.returncode
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            # Create result
            result = ExecutionResult(
                success=return_code == 0,
                stdout=stdout,
                stderr=stderr,
                return_code=return_code,
                execution_time=execution_time
            )
            
            # Log result
            if result.success:
                self.logger.info(f"Command executed successfully in {execution_time:.2f}s")
            else:
                self.logger.error(f"Command failed with return code {return_code}")
                self.logger.error(f"STDERR: {stderr}")
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()
            
            self.logger.error(f"Exception during command execution: {str(e)}")
            
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                return_code=-1,
                execution_time=execution_time
            )
    
    def _create_temp_vars_file(self, vars_dict: Dict[str, Any]) -> str:
        """Create temporary variables file for Ansible"""
        temp_file = os.path.join(self.temp_dir, f"extra_vars_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(temp_file, 'w') as f:
            json.dump(vars_dict, f, indent=2)
        
        return temp_file
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH"""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def validate_script_path(self, script_path: str, script_type: ScriptType) -> bool:
        """Validate script path and type"""
        if not os.path.exists(script_path):
            self.logger.error(f"Script not found: {script_path}")
            return False
        
        # Check file extension based on type
        extensions = {
            ScriptType.PYTHON: ['.py'],
            ScriptType.ANSIBLE: ['.yml', '.yaml'],
            ScriptType.POWERSHELL: ['.ps1', '.psm1'],
            ScriptType.BASH: ['.sh']
        }
        
        file_ext = Path(script_path).suffix.lower()
        if script_type in extensions and file_ext not in extensions[script_type]:
            self.logger.warning(f"File extension {file_ext} may not match script type {script_type.value}")
        
        return True
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            self.logger.info(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            self.logger.error(f"Error cleaning up temp directory: {str(e)}")
    
    def __del__(self):
        """Destructor - ensure cleanup"""
        self.cleanup()

# Example usage and testing
if __name__ == "__main__":
    executor = ScriptExecutor()
    
    # Test Python execution
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        if executor.validate_script_path(script_path, ScriptType.PYTHON):
            result = executor.execute_python_script(script_path)
            print(f"Success: {result.success}")
            print(f"Output: {result.stdout}")
            if result.stderr:
                print(f"Error: {result.stderr}")
    
    executor.cleanup()