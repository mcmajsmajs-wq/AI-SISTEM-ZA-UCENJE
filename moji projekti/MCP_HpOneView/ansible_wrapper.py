#!/usr/bin/env python3
"""
Ansible Wrapper for MCP_HpOneView Extended
Provides Ansible playbook execution capabilities with security and validation
"""

import os
import sys
import json
import yaml
import subprocess
import tempfile
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
from script_executor import ScriptExecutor, ExecutionResult
from security_manager import SecurityManager, SecurityLevel

class AnsibleWrapper:
    """Wrapper for Ansible playbook execution"""
    
    def __init__(self, security_manager: SecurityManager):
        self.security = security_manager
        self.executor = ScriptExecutor("mcp_ansible.log")
        self.logger = logging.getLogger("AnsibleWrapper")
        
        # Ansible paths
        self.ansible_paths = {
            "playbooks": "scripts/ansible/playbooks",
            "inventory": "scripts/ansible/inventory",
            "group_vars": "scripts/ansible/group_vars",
            "roles": "scripts/ansible/roles"
        }
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        for path in self.ansible_paths.values():
            Path(path).mkdir(parents=True, exist_ok=True)
    
    def execute_playbook(self, playbook_name: str,
                        inventory: Optional[str] = None,
                        extra_vars: Optional[Dict[str, Any]] = None,
                        limit: Optional[str] = None,
                        tags: Optional[List[str]] = None,
                        check_mode: bool = False,
                        security_level: SecurityLevel = SecurityLevel.MEDIUM) -> ExecutionResult:
        """Execute Ansible playbook with security validation"""
        
        self.logger.info(f"Executing Ansible playbook: {playbook_name}")
        
        # Security validation
        if not self.security.validate_script_execution(
            f"{self.ansible_paths['playbooks']}/{playbook_name}", 
            security_level
        ):
            return ExecutionResult(
                success=False,
                stdout="",
                stderr="Security validation failed",
                return_code=-1,
                execution_time=0
            )
        
        # Build command
        cmd = ["ansible-playbook"]
        
        # Add inventory
        inv_path = inventory or f"{self.ansible_paths['inventory']}/hosts"
        if os.path.exists(inv_path):
            cmd.extend(["-i", inv_path])
        
        # Add check mode
        if check_mode:
            cmd.append("--check")
        
        # Add limit
        if limit:
            cmd.extend(["--limit", limit])
        
        # Add tags
        if tags:
            cmd.extend(["--tags", ",".join(tags)])
        
        # Add extra variables
        if extra_vars:
            extra_vars_file = self._create_extra_vars_file(extra_vars)
            cmd.extend(["-e", f"@{extra_vars_file}"])
        
        # Add playbook path
        playbook_path = f"{self.ansible_paths['playbooks']}/{playbook_name}"
        cmd.append(playbook_path)
        
        # Execute with security context
        env_vars = self._get_secure_env_vars()
        
        return self.executor.execute_command(cmd, env_vars)
    
    def execute_firmware_update(self, server_name: str,
                               spp_version: str,
                               update_mode: str = "firmware_only",
                               check_mode: bool = False) -> ExecutionResult:
        """Execute firmware update playbook"""
        
        self.logger.info(f"Executing firmware update for server: {server_name}")
        
        extra_vars = {
            "server_name": server_name,
            "spp_version": spp_version,
            "update_mode": update_mode,
            "execution_timestamp": datetime.utcnow().isoformat()
        }
        
        return self.execute_playbook(
            playbook_name="firmware_update.yml",
            extra_vars=extra_vars,
            limit=server_name,
            check_mode=check_mode,
            security_level=SecurityLevel.HIGH
        )
    
    def execute_profile_compliance(self, profile_name: str,
                                  compliance_type: str = "full",
                                  remediate: bool = False) -> ExecutionResult:
        """Execute profile compliance check"""
        
        self.logger.info(f"Checking compliance for profile: {profile_name}")
        
        extra_vars = {
            "profile_name": profile_name,
            "compliance_type": compliance_type,
            "remediate": remediate,
            "check_timestamp": datetime.utcnow().isoformat()
        }
        
        tags = ["compliance"]
        if remediate:
            tags.append("remediate")
        
        return self.execute_playbook(
            playbook_name="profile_compliance.yml",
            extra_vars=extra_vars,
            tags=tags,
            check_mode=not remediate,
            security_level=SecurityLevel.MEDIUM
        )
    
    def execute_server_management(self, action: str,
                                 server_name: str,
                                 parameters: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """Execute server management operations"""
        
        self.logger.info(f"Executing server management: {action} on {server_name}")
        
        extra_vars = {
            "action": action,
            "server_name": server_name,
            "parameters": parameters or {},
            "execution_timestamp": datetime.utcnow().isoformat()
        }
        
        return self.execute_playbook(
            playbook_name="server_management.yml",
            extra_vars=extra_vars,
            limit=server_name,
            tags=[action],
            security_level=SecurityLevel.MEDIUM
        )
    
    def list_available_playbooks(self) -> List[Dict[str, Any]]:
        """List all available Ansible playbooks"""
        playbooks = []
        playbook_dir = Path(self.ansible_paths["playbooks"])
        
        for playbook_file in playbook_dir.glob("*.yml"):
            try:
                # Parse playbook metadata
                metadata = self._parse_playbook_metadata(playbook_file)
                playbooks.append({
                    "name": playbook_file.name,
                    "path": str(playbook_file),
                    "metadata": metadata
                })
            except Exception as e:
                self.logger.warning(f"Error parsing playbook {playbook_file}: {e}")
                playbooks.append({
                    "name": playbook_file.name,
                    "path": str(playbook_file),
                    "metadata": {"error": str(e)}
                })
        
        return playbooks
    
    def _parse_playbook_metadata(self, playbook_path: Path) -> Dict[str, Any]:
        """Parse metadata from playbook file"""
        try:
            with open(playbook_path, 'r') as f:
                content = yaml.safe_load(f)
            
            # Extract metadata from playbook
            metadata = {
                "description": "No description available",
                "author": "Unknown",
                "version": "1.0",
                "tags": [],
                "parameters": []
            }
            
            # Look for vars section with metadata
            if isinstance(content, list) and len(content) > 0:
                play = content[0]
                if "vars" in play:
                    vars_data = play["vars"]
                    metadata.update({
                        k: v for k, v in vars_data.items() 
                        if k in ["description", "author", "version", "tags"]
                    })
            
            return metadata
            
        except Exception as e:
            return {"error": f"Failed to parse metadata: {str(e)}"}
    
    def _create_extra_vars_file(self, extra_vars: Dict[str, Any]) -> str:
        """Create temporary extra variables file"""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            prefix='ansible_extra_vars_',
            delete=False
        )
        
        json.dump(extra_vars, temp_file, indent=2)
        temp_file.close()
        
        return temp_file.name
    
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
    
    def validate_playbook(self, playbook_name: str) -> Dict[str, Any]:
        """Validate Ansible playbook syntax and structure"""
        self.logger.info(f"Validating playbook: {playbook_name}")
        
        playbook_path = f"{self.ansible_paths['playbooks']}/{playbook_name}"
        
        if not os.path.exists(playbook_path):
            return {
                "valid": False,
                "error": f"Playbook not found: {playbook_path}"
            }
        
        # Syntax check
        try:
            cmd = ["ansible-playbook", "--syntax-check", playbook_path]
            result = self.executor.execute_command(cmd)
            
            if result.success:
                return {
                    "valid": True,
                    "message": "Playbook syntax is valid"
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
    
    def create_inventory_file(self, inventory_name: str,
                             hosts: Dict[str, Dict[str, Any]],
                             groups: Optional[Dict[str, List[str]]] = None) -> str:
        """Create Ansible inventory file"""
        
        inventory_path = f"{self.ansible_paths['inventory']}/{inventory_name}"
        
        inventory_content = []
        
        # Add groups and hosts
        if groups:
            for group_name, host_list in groups.items():
                inventory_content.append(f"[{group_name}]")
                for host in host_list:
                    if host in hosts:
                        host_vars = hosts[host]
                        host_line = host
                        if host_vars:
                            for key, value in host_vars.items():
                                host_line += f" {key}={value}"
                        inventory_content.append(host_line)
                inventory_content.append("")  # Empty line
        
        # Add ungrouped hosts
        ungrouped = set(hosts.keys())
        if groups:
            for host_list in groups.values():
                ungrouped -= set(host_list)
        
        if ungrouped:
            inventory_content.append("[ungrouped]")
            for host in ungrouped:
                inventory_content.append(host)
        
        # Write inventory file
        with open(inventory_path, 'w') as f:
            f.write('\n'.join(inventory_content))
        
        self.logger.info(f"Created inventory file: {inventory_path}")
        return inventory_path
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        # Clean up extra vars files
        temp_dir = tempfile.gettempdir()
        for file in os.listdir(temp_dir):
            if file.startswith("ansible_extra_vars_"):
                try:
                    os.remove(os.path.join(temp_dir, file))
                except Exception as e:
                    self.logger.warning(f"Error cleaning temp file {file}: {e}")

# Example usage
if __name__ == "__main__":
    # Initialize security manager
    security = SecurityManager()
    
    # Store some test credentials
    security.store_credential("oneview_username", "administrator", "oneview")
    security.store_credential("oneview_password", "password123", "oneview")
    
    # Initialize Ansible wrapper
    ansible = AnsibleWrapper(security)
    
    # Test firmware update
    result = ansible.execute_firmware_update(
        server_name="test-server",
        spp_version="2023.09.0",
        check_mode=True
    )
    
    print(f"Execution successful: {result.success}")
    print(f"Output: {result.stdout}")
    if result.stderr:
        print(f"Errors: {result.stderr}")
    
    # List available playbooks
    playbooks = ansible.list_available_playbooks()
    print(f"Available playbooks: {len(playbooks)}")
    for playbook in playbooks:
        print(f"  - {playbook['name']}")
    
    # Cleanup
    ansible.cleanup_temp_files()
    security.cleanup()