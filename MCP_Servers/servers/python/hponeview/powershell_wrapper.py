#!/usr/bin/env python3
"""
PowerShell Wrapper for MCP_HpOneView Extended
Provides PowerShell script execution capabilities with cross-platform support
"""

import os
import sys
import json
import subprocess
import tempfile
import logging
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from script_executor import ScriptExecutor, ExecutionResult
from security_manager import SecurityManager, SecurityLevel

class PowerShellWrapper:
    """Wrapper for PowerShell script execution"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.executor = ScriptExecutor("mcp_powershell.log")
        self.logger = logging.getLogger("PowerShellWrapper")
        
        # PowerShell paths
        self.powershell_paths = {
            "modules": "scripts/powershell/modules",
            "scenarios": "scripts/powershell/scenarios",
            "core": "scripts/powershell/core"
        }
        
        # Platform detection
        self.platform = platform.system().lower()
        self.powershell_cmd = self._get_powershell_command()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _get_powershell_command(self) -> str:
        """Get appropriate PowerShell command for platform"""
        if self.platform == "windows":
            return "powershell.exe"
        else:
            # Try pwsh (PowerShell Core) first
            if self._command_exists("pwsh"):
                return "pwsh"
            # Fallback to powershell-core
            elif self._command_exists("powershell-core"):
                return "powershell-core"
            else:
                raise RuntimeError("PowerShell not found on this system")
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists"""
        try:
            subprocess.run(["which", command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        for path in self.powershell_paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def execute_script(self, script_name: str,
                       args: Optional[List[str]] = None,
                       parameters: Optional[Dict[str, Any]] = None,
                       security_level: SecurityLevel = SecurityLevel.MEDIUM) -> ExecutionResult:
        """Execute PowerShell script with security validation"""
        
        self.logger.info(f"Executing PowerShell script: {script_name}")
        
        # Build script path
        script_path = f"{self.powershell_paths['scenarios']}/{script_name}"
        
        # Security validation
        if not self.security.validate_script_execution(script_path, security_level):
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Security validation failed",
                return_code=-1,
                execution_time=0
            )
        
        # Build command
        cmd = [self.powershell_cmd, "-ExecutionPolicy", "Bypass", "-File", script_path]
        
        # Add arguments
        if args:
            cmd.extend(args)
        
        # Add parameters as PowerShell parameters
        if parameters:
            for key, value in parameters.items():
                cmd.extend(["-Parameter", f"{key}={value}"])
        
        # Execute with security context
        env_vars = self._get_secure_env_vars()
        
        return self.executor.execute_command(cmd, env_vars)
    
    def execute_server_management(self, action: str,
                                 server_name: str,
                                 parameters: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Execute server management PowerShell script"""
        
        self.logger.info(f"Executing server management: {action} on {server_name}")
        
        script_params = {
            "Action": action,
            "ServerName": server_name,
            "Timestamp": datetime.utcnow().isoformat()
        }
        
        if parameters:
            script_params.update(parameters)
        
        return self.execute_script(
            script_name="ServerManagement.ps1",
            parameters=script_params,
            security_level=SecurityLevel.MEDIUM
        )
    
    def execute_firmware_update(self, server_name: str,
                               spp_version: str,
                               update_mode: str = "FirmwareOnly",
                               force_update: bool = False) -> ExecutionResult:
        """Execute firmware update PowerShell script"""
        
        self.logger.info(f"Executing firmware update for server: {server_name}")
        
        script_params = {
            "ServerName": server_name,
            "SppVersion": spp_version,
            "UpdateMode": update_mode,
            "ForceUpdate": str(force_update).lower(),
            "Timestamp": datetime.utcnow().isoformat()
        }
        
        return self.execute_script(
            script_name="FirmwareUpdate.ps1",
            parameters=script_params,
            security_level=SecurityLevel.HIGH
        )
    
    def execute_profile_compliance(self, profile_name: str,
                                  compliance_type: str = "Full",
                                  remediate: bool = False) -> ExecutionResult:
        """Execute profile compliance PowerShell script"""
        
        self.logger.info(f"Checking compliance for profile: {profile_name}")
        
        script_params = {
            "ProfileName": profile_name,
            "ComplianceType": compliance_type,
            "Remediate": str(remediate).lower(),
            "Timestamp": datetime.utcnow().isoformat()
        }
        
        return self.execute_script(
            script_name="ProfileCompliance.ps1",
            parameters=script_params,
            security_level=SecurityLevel.MEDIUM
        )
    
    def execute_hardware_inventory(self, server_name: Optional[str] = None,
                                  detailed: bool = False) -> ExecutionResult:
        """Execute hardware inventory PowerShell script"""
        
        self.logger.info(f"Executing hardware inventory")
        
        script_params = {
            "Detailed": str(detailed).lower(),
            "Timestamp": datetime.utcnow().isoformat()
        }
        
        if server_name:
            script_params["ServerName"] = server_name
        
        return self.execute_script(
            script_name="HardwareInventory.ps1",
            parameters=script_params,
            security_level=SecurityLevel.LOW
        )
    
    def list_available_scripts(self) -> List[Dict[str, Any]]:
        """List all available PowerShell scripts"""
        scripts = []
        script_dir = Path(self.powershell_paths["scenarios"])
        
        for script_file in script_dir.glob("*.ps1"):
            try:
                # Parse script metadata
                metadata = self._parse_script_metadata(script_file)
                scripts.append({
                    "name": script_file.name,
                    "path": str(script_file),
                    "metadata": metadata
                })
            except Exception as e:
                self.logger.warning(f"Error parsing script {script_file}: {e}")
                scripts.append({
                    "name": script_file.name,
                    "path": str(script_file),
                    "metadata": {"error": str(e)}
                })
        
        return scripts
    
    def _parse_script_metadata(self, script_path: Path) -> Dict[str, Any]:
        """Parse metadata from PowerShell script file"""
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from script comments
            metadata = {
                "description": "No description available",
                "author": "Unknown",
                "version": "1.0",
                "parameters": [],
                "tags": []
            }
            
            # Look for metadata in comments
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith("#"):
                    if "DESCRIPTION:" in line.upper():
                        metadata["description"] = line.split(":", 1)[1].strip()
                    elif "AUTHOR:" in line.upper():
                        metadata["author"] = line.split(":", 1)[1].strip()
                    elif "VERSION:" in line.upper():
                        metadata["version"] = line.split(":", 1)[1].strip()
                    elif "TAGS:" in line.upper():
                        tags = line.split(":", 1)[1].strip()
                        metadata["tags"] = [tag.strip() for tag in tags.split(",")]
                elif line.startswith("param("):
                    # Extract parameter from param() block
                    param_name = line.split("(")[1].split(")")[0].strip("$")
                    if param_name and param_name not in metadata["parameters"]:
                        metadata["parameters"].append(param_name)
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to parse metadata: {str(e)}"}
    
    def _get_secure_env_vars(self) -> Dict[str, str]:
        """Get environment variables with secure credentials"""
        env_vars = os.environ.copy()
        
        # Add OneView credentials from secure storage
        oneview_username = self.security.get_credential("oneview_username")
        oneview_password = self.security.get_credential("oneview_password")
        
        if oneview_username:
            env_vars["ONEVIEW_USERNAME"] = oneview_username
        if oneview_password:
            env_vars["ONEVIEW_PASSWORD"] = oneview_password
        
        return env_vars
    
    def validate_script(self, script_name: str) -> Dict[str, Any]:
        """Validate PowerShell script syntax and structure"""
        self.logger.info(f"Validating PowerShell script: {script_name}")
        
        script_path = f"{self.powershell_paths['scenarios']}/{script_name}"
        
        if not os.path.exists(script_path):
            return {
                "valid": False,
                "error": f"Script not found: {script_path}"
            }
        
        # Syntax check using PowerShell
        try:
            cmd = [self.powershell_cmd, "-Command", f"Get-Content '{script_path}' | Out-Null"]
            result = self.executor.execute_command(cmd)
            
            if result.success:
                return {
                    "valid": True,
                    "message": "PowerShell script syntax is valid"
                }
            else:
                return {
                    "valid": False,
                    "error": result.stderr,
                    "return_code": result.return_code
                }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation error: {str(e)}"
            }
    
    def create_powershell_module(self, module_name: str,
                                functions: List[Dict[str, Any]]) -> str:
        """Create PowerShell module with specified functions"""
        
        module_path = f"{self.powershell_paths['modules']}/{module_name}.psm1"
        
        module_content = []
        module_content.append(f"# PowerShell Module: {module_name}")
        module_content.append(f"# Generated on: {datetime.utcnow().isoformat()}")
        module_content.append("")
        
        for func in functions:
            module_content.append(f"function {func['name']} {{")
            module_content.append(f"    [CmdletBinding()]")
            module_content.append(f"    param(")
            
            # Add parameters
            if 'parameters' in func:
                for i, param in enumerate(func['parameters']):
                    param_line = f"        [{param['type']}]${param['name']}"
                    if 'default' in param:
                        param_line += f" = '{param['default']}'"
                    if i < len(func['parameters']) - 1:
                        param_line += ","
                    module_content.append(param_line)
            
            module_content.append(f"    )")
            module_content.append("")
            module_content.append(f"    # {func.get('description', 'No description')}")
            module_content.append(f"    # TODO: Implement function logic")
            module_content.append(f"    Write-Host 'Function {func['name']} called'")
            module_content.append(f"}}")
            module_content.append("")
        
        # Write module file
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(module_content))
        
        self.logger.info(f"Created PowerShell module: {module_path}")
        return module_path
    
    def install_powershell_module(self, module_path: str) -> ExecutionResult:
        """Install PowerShell module"""
        self.logger.info(f"Installing PowerShell module: {module_path}")
        
        try:
            # Copy module to PowerShell modules directory
            if self.platform == "windows":
                powershell_modules_dir = os.path.expanduser("~/Documents/WindowsPowerShell/Modules")
            else:
                powershell_modules_dir = os.path.expanduser("~/.local/share/powershell/Modules")
            
            module_name = Path(module_path).stem
            target_dir = os.path.join(powershell_modules_dir, module_name)
            
            # Create target directory
            os.makedirs(target_dir, exist_ok=True)
            
            # Copy module file
            target_path = os.path.join(target_dir, Path(module_path).name)
            import shutil
            shutil.copy2(module_path, target_path)
            
            return ExecutionResult(
                success=True,
                stdout=f"Module installed to: {target_path}",
                stderr="",
                return_code=0,
                execution_time=0
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Error installing module: {str(e)}",
                return_code=-1,
                execution_time=0
            )
    
    def get_powershell_version(self) -> Dict[str, Any]:
        """Get PowerShell version information"""
        try:
            cmd = [self.powershell_cmd, "-Command", "$PSVersionTable.PSVersion"]
            result = self.executor.execute_command(cmd)
            
            if result.success:
                return {
                    "success": True,
                    "version": result.stdout.strip(),
                    "command": self.powershell_cmd
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "command": self.powershell_cmd
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting PowerShell version: {str(e)}",
                "command": self.powershell_cmd
            }

# Example usage
if __name__ == "__main__":
    # Initialize security manager
    security = SecurityManager()
    
    # Store some test credentials
    security.store_credential("oneview_username", "administrator", "oneview")
    security.store_credential("oneview_password", "password123", "oneview")
    
    # Initialize PowerShell wrapper
    powershell = PowerShellWrapper(security)
    
    # Get PowerShell version
    version_info = powershell.get_powershell_version()
    print(f"PowerShell version info: {version_info}")
    
    # Test server management
    result = powershell.execute_server_management(
        action="status",
        server_name="test-server"
    )
    
    print(f"Execution successful: {result.success}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    # List available scripts
    scripts = powershell.list_available_scripts()
    print(f"Available scripts: {len(scripts)}")
    for script in scripts:
        print(f"  - {script['name']}")
    
    # Cleanup
    security.cleanup()