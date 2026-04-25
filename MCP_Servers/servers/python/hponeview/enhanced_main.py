#!/usr/bin/env python3
"""
Enhanced Main MCP Server for HP OneView Extended
Supports Python, Ansible, and PowerShell script execution
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import existing modules
try:
    from mcp.server.fastmcp import FastMCP
    from tools_compute import proveri_servere, uporedi_profil
except ImportError as e:
    print(f"Error importing existing modules: {e}")
    sys.exit(1)

# Import new extended modules
try:
    from script_executor import ScriptExecutor, ExecutionResult
    from security_manager import SecurityManager, SecurityLevel
    from ansible_wrapper import AnsibleWrapper
    from powershell_wrapper import PowerShellWrapper
except ImportError as e:
    print(f"Error importing extended modules: {e}")
    print("Please ensure all dependencies are installed.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server_extended.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("mcp_server_extended")

class EnhancedMCPServer(FastMCP):
    """Enhanced MCP Server with multi-script support"""
    
    def __init__(self):
        super().__init__("mcp-hp-oneview-extended", "1.0.0")
        
        # Initialize components
        self.security_manager = SecurityManager()
        self.script_executor = ScriptExecutor()
        self.ansible_wrapper = AnsibleWrapper(self.security_manager)
        self.powershell_wrapper = PowerShellWrapper(self.security_manager)
        
        logger.info("Enhanced MCP Server initialized")
    
    async def setup(self) -> None:
        """Setup the enhanced server"""
        logger.info("Setting up enhanced MCP server...")
        
        # Register existing Python tools
        await self.register_tool("proveri_servere", self.proveri_servere)
        await self.register_tool("uporedi_profil", self.uporedi_profil)
        
        # Register new Ansible tools
        await self.register_tool("ansible_firmware_update", self.ansible_firmware_update)
        await self.register_tool("ansible_profile_compliance", self.ansible_profile_compliance)
        await self.register_tool("ansible_server_management", self.ansible_server_management)
        
        # Register new PowerShell tools
        await self.register_tool("powershell_server_management", self.powershell_server_management)
        await self.register_tool("powershell_firmware_update", self.powershell_firmware_update)
        await self.register_tool("powershell_profile_compliance", self.powershell_profile_compliance)
        await self.register_tool("powershell_hardware_inventory", self.powershell_hardware_inventory)
        
        # Register utility tools
        await self.register_tool("list_available_scripts", self.list_available_scripts)
        await self.register_tool("validate_script", self.validate_script)
        await self.register_tool("get_system_status", self.get_system_status)
        
        logger.info("Enhanced MCP server setup completed")
    
    # Existing Python tools
    async def proveri_servere(self) -> str:
        """List all server hardware from OneView"""
        try:
            logger.info("Getting server list from OneView")
            
            # Use existing tools_compute functionality
            result = proveri_servere()
            return result
            
        except Exception as e:
            logger.error(f"Error getting server list: {e}")
            return f"Error: {str(e)}"
    
    async def uporedi_profil(self, profile_name: str) -> str:
        """Compare server profile with template"""
        try:
            logger.info(f"Comparing profile: {profile_name}")
            
            # Use existing tools_compute functionality
            result = uporedi_profil(profile_name)
            return result
            
        except Exception as e:
            logger.error(f"Error comparing profile: {e}")
            return f"Error: {str(e)}"
    
    # New Ansible tools
    async def ansible_firmware_update(self, server_name: str, spp_version: str, 
                               update_mode: str = "FirmwareOnly", force_update: bool = False) -> str:
        """Execute firmware update using Ansible"""
        try:
            logger.info(f"Executing Ansible firmware update for server: {server_name}")
            
            result = self.ansible_wrapper.execute_firmware_update(
                server_name=server_name,
                spp_version=spp_version,
                update_mode=update_mode,
                force_update=force_update,
                security_level=SecurityLevel.HIGH
            )
            
            if result.success:
                return f"Ansible firmware update completed successfully. Server: {server_name}, SPP: {spp_version}, Mode: {update_mode}, Force: {force_update}"
            else:
                return f"Ansible firmware update failed. Server: {server_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in Ansible firmware update: {e}")
            return f"Error: {str(e)}"
    
    async def ansible_profile_compliance(self, profile_name: str, compliance_type: str = "full", 
                                  remediate: bool = False) -> str:
        """Check profile compliance using Ansible"""
        try:
            logger.info(f"Checking profile compliance using Ansible: {profile_name}")
            
            result = self.ansible_wrapper.execute_profile_compliance(
                profile_name=profile_name,
                compliance_type=compliance_type,
                remediate=remediate,
                security_level=SecurityLevel.MEDIUM
            )
            
            if result.success:
                return f"Ansible profile compliance check completed. Profile: {profile_name}, Type: {compliance_type}, Remediated: {remediate}"
            else:
                return f"Ansible profile compliance check failed. Profile: {profile_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in Ansible profile compliance: {e}")
            return f"Error: {str(e)}"
    
    async def ansible_server_management(self, action: str, server_name: str, 
                                 parameters: Optional[Dict[str, Any]] = None) -> str:
        """Manage servers using Ansible"""
        try:
            logger.info(f"Managing server using Ansible: {action} on {server_name}")
            
            result = self.ansible_wrapper.execute_server_management(
                action=action,
                server_name=server_name,
                parameters=parameters or {},
                security_level=SecurityLevel.MEDIUM
            )
            
            if result.success:
                return f"Ansible server management completed. Action: {action}, Server: {server_name}"
            else:
                return f"Ansible server management failed. Action: {action}, Server: {server_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in Ansible server management: {e}")
            return f"Error: {str(e)}"
    
    # New PowerShell tools
    async def powershell_server_management(self, action: str, server_name: str, 
                                     parameters: Optional[Dict[str, Any]] = None) -> str:
        """Manage servers using PowerShell"""
        try:
            logger.info(f"Managing server using PowerShell: {action} on {server_name}")
            
            result = self.powershell_wrapper.execute_server_management(
                action=action,
                server_name=server_name,
                parameters=parameters or {},
                security_level=SecurityLevel.MEDIUM
            )
            
            if result.success:
                return f"PowerShell server management completed. Action: {action}, Server: {server_name}"
            else:
                return f"PowerShell server management failed. Action: {action}, Server: {server_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in PowerShell server management: {e}")
            return f"Error: {str(e)}"
    
    async def powershell_firmware_update(self, server_name: str, spp_version: str, 
                                   update_mode: str = "FirmwareOnly", force_update: bool = False) -> str:
        """Update firmware using PowerShell"""
        try:
            logger.info(f"Updating firmware using PowerShell: {server_name}")
            
            result = self.powershell_wrapper.execute_firmware_update(
                server_name=server_name,
                spp_version=spp_version,
                update_mode=update_mode,
                force_update=force_update,
                security_level=SecurityLevel.HIGH
            )
            
            if result.success:
                return f"PowerShell firmware update completed. Server: {server_name}, SPP: {spp_version}, Mode: {update_mode}, Force: {force_update}"
            else:
                return f"PowerShell firmware update failed. Server: {server_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in PowerShell firmware update: {e}")
            return f"Error: {str(e)}"
    
    async def powershell_profile_compliance(self, profile_name: str, compliance_type: str = "full", 
                                      remediate: bool = False) -> str:
        """Check profile compliance using PowerShell"""
        try:
            logger.info(f"Checking profile compliance using PowerShell: {profile_name}")
            
            result = self.powershell_wrapper.execute_profile_compliance(
                profile_name=profile_name,
                compliance_type=compliance_type,
                remediate=remediate,
                security_level=SecurityLevel.MEDIUM
            )
            
            if result.success:
                return f"PowerShell profile compliance check completed. Profile: {profile_name}, Type: {compliance_type}, Remediated: {remediate}"
            else:
                return f"PowerShell profile compliance check failed. Profile: {profile_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in PowerShell profile compliance: {e}")
            return f"Error: {str(e)}"
    
    async def powershell_hardware_inventory(self, server_name: str = "all", detailed: bool = False) -> str:
        """Get hardware inventory using PowerShell"""
        try:
            logger.info(f"Getting hardware inventory using PowerShell: {server_name}")
            
            result = self.powershell_wrapper.execute_hardware_inventory(
                server_name=server_name,
                detailed=detailed,
                security_level=SecurityLevel.LOW
            )
            
            if result.success:
                return f"PowerShell hardware inventory completed. Server: {server_name}, Detailed: {detailed}"
            else:
                return f"PowerShell hardware inventory failed. Server: {server_name}, Error: {result.stderr}"
                
        except Exception as e:
            logger.error(f"Error in PowerShell hardware inventory: {e}")
            return f"Error: {str(e)}"
    
    # Utility tools
    async def list_available_scripts(self) -> str:
        """List all available scripts"""
        try:
            logger.info("Listing available scripts")
            
            # Get Ansible playbooks
            ansible_playbooks = self.ansible_wrapper.list_available_playbooks()
            
            # Get PowerShell scripts
            powershell_scripts = self.powershell_list_available_scripts()
            
            result = {
                "ansible_playbooks": ansible_playbooks,
                "powershell_scripts": powershell_scripts,
                "total_scripts": len(ansible_playbooks) + len(powershell_scripts)
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error listing scripts: {e}")
            return f"Error: {str(e)}"
    
    async def validate_script(self, script_type: str, script_name: str) -> str:
        """Validate script syntax and structure"""
        try:
            logger.info(f"Validating {script_type} script: {script_name}")
            
            if script_type == "ansible":
                result = self.ansible_wrapper.validate_playbook(script_name)
            elif script_type == "powershell":
                result = self.powershell_wrapper.validate_script(script_name)
            else:
                return f"Error: Unknown script type: {script_type}"
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error validating script: {e}")
            return f"Error: {str(e)}"
    
    async def get_system_status(self) -> str:
        """Get system status and health"""
        try:
            logger.info("Getting system status")
            
            status = {
                "server": "mcp-hp-oneview-extended",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "python": "OK",
                    "ansible": "OK" if self.ansible_wrapper else "Not Available",
                    "powershell": "OK" if self.powershell_wrapper else "Not Available",
                    "security": "OK",
                    "script_executor": "OK"
                },
                "available_scripts": {
                    "ansible_playbooks": len(self.ansible_wrapper.list_available_playbooks()) if self.ansible_wrapper else 0,
                    "powershell_scripts": len(self.powershell_list_available_scripts()) if self.powershell_wrapper else 0
                },
                "security": {
                    "credentials_stored": len(self.security_manager.audit_log) > 0,
                    "active_sessions": len(self.security_manager.session_tokens),
                    "encryption_enabled": True
                }
            }
            
            return json.dumps(status, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return f"Error: {str(e)}"

# Main execution
if __name__ == "__main__":
    # Create and run the enhanced server
    server = EnhancedMCPServer()
    
    try:
        # Run the server
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)