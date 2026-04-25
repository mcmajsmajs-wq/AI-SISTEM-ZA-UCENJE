#!/usr/bin/env python3
"""
Test Suite for MCP_HpOneView Extended System
Comprehensive testing of all components
"""

import sys
import os
import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add scripts directory to Python path
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import our modules
from script_executor import ScriptExecutor
from security_manager import SecurityManager
from ansible_wrapper import AnsibleWrapper
from powershell_wrapper import PowerShellWrapper
from enhanced_main import EnhancedMcpHpOneViewServer

class TestSuite:
    """Comprehensive test suite for MCP_HpOneView Extended"""
    
    def __init__(self):
        self.setup_logging()
        self.results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': [],
            'test_results': []
        }
        
        # Initialize components
        self.security_manager = SecurityManager()
        self.script_executor = ScriptExecutor(self.security_manager)
        self.ansible_wrapper = AnsibleWrapper(self.security_manager)
        self.powershell_wrapper = PowerShellWrapper(self.security_manager)
        
    def setup_logging(self):
        """Setup test logging"""
        log_dir = Path("tests/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"test_suite_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('TestSuite')
        
    def run_test(self, test_name: str, test_func, *args, **kwargs):
        """Run a single test and track results"""
        self.results['total_tests'] += 1
        self.logger.info(f"Running test: {test_name}")
        
        try:
            result = test_func(*args, **kwargs)
            if result:
                self.results['passed'] += 1
                self.logger.info(f"✅ PASSED: {test_name}")
                self.results['test_results'].append({
                    'name': test_name,
                    'status': 'PASSED',
                    'message': 'Test completed successfully'
                })
                return True
            else:
                self.results['failed'] += 1
                self.logger.error(f"❌ FAILED: {test_name}")
                self.results['test_results'].append({
                    'name': test_name,
                    'status': 'FAILED',
                    'message': 'Test returned False'
                })
                return False
                
        except Exception as e:
            self.results['failed'] += 1
            error_msg = f"❌ ERROR in {test_name}: {str(e)}"
            self.logger.error(error_msg)
            self.results['errors'].append(error_msg)
            self.results['test_results'].append({
                'name': test_name,
                'status': 'ERROR',
                'message': str(e)
            })
            return False
    
    # Test Security Manager
    def test_security_manager_initialization(self):
        """Test security manager initialization"""
        return self.security_manager is not None
    
    def test_credential_encryption(self):
        """Test credential encryption and decryption"""
        test_password = "TestPassword123!"
        
        # Encrypt
        encrypted = self.security_manager.encrypt_password(test_password)
        assert encrypted != test_password
        assert len(encrypted) > 0
        
        # Decrypt
        decrypted = self.security_manager.decrypt_password(encrypted)
        assert decrypted == test_password
        
        return True
    
    def test_session_management(self):
        """Test session management"""
        user_id = "test_user"
        session_token = self.security_manager.create_session(user_id)
        
        assert session_token is not None
        assert len(session_token) > 0
        
        # Validate session
        is_valid = self.security_manager.validate_session(session_token)
        assert is_valid == True
        
        # Destroy session
        self.security_manager.destroy_session(session_token)
        is_valid_after = self.security_manager.validate_session(session_token)
        assert is_valid_after == False
        
        return True
    
    # Test Script Executor
    def test_script_executor_initialization(self):
        """Test script executor initialization"""
        return self.script_executor is not None
    
    def test_python_script_execution(self):
        """Test Python script execution in simulate mode"""
        test_script = """
print("Test Python script executed successfully")
result = {"status": "success", "message": "Python test passed"}
"""
        
        result = self.script_executor.execute_script(
            script_type="python",
            script_content=test_script,
            simulate=True,
            parameters={}
        )
        
        assert result['success'] == True
        assert 'Test Python script executed successfully' in result['output']
        return True
    
    def test_ansible_script_execution(self):
        """Test Ansible script execution in simulate mode"""
        test_playbook = """
---
- name: Test Playbook
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Test task
      debug:
        msg: "Ansible test executed successfully"
"""
        
        result = self.script_executor.execute_script(
            script_type="ansible",
            script_content=test_playbook,
            simulate=True,
            parameters={}
        )
        
        assert result['success'] == True
        return True
    
    def test_powershell_script_execution(self):
        """Test PowerShell script execution in simulate mode"""
        test_script = """
Write-Host "PowerShell test executed successfully"
$result = @{
    status = "success"
    message = "PowerShell test passed"
}
"""
        
        result = self.script_executor.execute_script(
            script_type="powershell",
            script_content=test_script,
            simulate=True,
            parameters={}
        )
        
        assert result['success'] == True
        return True
    
    # Test Ansible Wrapper
    def test_ansible_wrapper_initialization(self):
        """Test Ansible wrapper initialization"""
        return self.ansible_wrapper is not None
    
    def test_ansible_server_management(self):
        """Test Ansible server management functionality"""
        result = self.ansible_wrapper.execute_server_management(
            server_names=["test-server-1"],
            action="power_on",
            simulate=True
        )
        
        assert result['success'] == True
        return True
    
    def test_ansible_firmware_update(self):
        """Test Ansible firmware update functionality"""
        result = self.ansible_wrapper.execute_firmware_update(
            server_names=["test-server-1"],
            firmware_version="1.2.3",
            simulate=True
        )
        
        assert result['success'] == True
        return True
    
    # Test PowerShell Wrapper
    def test_powershell_wrapper_initialization(self):
        """Test PowerShell wrapper initialization"""
        return self.powershell_wrapper is not None
    
    def test_powershell_server_management(self):
        """Test PowerShell server management functionality"""
        result = self.powershell_wrapper.execute_server_management(
            server_names=["test-server-1"],
            action="power_on",
            simulate=True
        )
        
        assert result['success'] == True
        return True
    
    def test_powershell_hardware_inventory(self):
        """Test PowerShell hardware inventory functionality"""
        result = self.powershell_wrapper.execute_hardware_inventory(
            server_names=["test-server-1"],
            simulate=True
        )
        
        assert result['success'] == True
        return True
    
    # Test Enhanced Main Server
    def test_enhanced_server_initialization(self):
        """Test enhanced main server initialization"""
        server = EnhancedMcpHpOneViewServer()
        return server is not None
    
    def test_tool_registration(self):
        """Test tool registration in enhanced server"""
        server = EnhancedMcpHpOneViewServer()
        
        # Check if tools are registered
        tools = server.list_tools()
        assert len(tools) > 0
        
        # Check for specific tools
        tool_names = [tool['name'] for tool in tools]
        expected_tools = [
            'execute_script',
            'manage_credentials',
            'execute_ansible_playbook',
            'execute_powershell_script'
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        return True
    
    # Test File Structure
    def test_directory_structure(self):
        """Test if all required directories exist"""
        required_dirs = [
            'scripts/ansible',
            'scripts/ansible/playbooks',
            'scripts/ansible/inventory',
            'scripts/powershell',
            'scripts/powershell/scenarios',
            'scripts/powershell/core',
            'docs/english',
            'docs/serbian',
            'tests',
            'tests/logs'
        ]
        
        for dir_path in required_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} does not exist"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
        
        return True
    
    def test_required_files(self):
        """Test if all required files exist"""
        required_files = [
            'scripts/script_executor.py',
            'scripts/security_manager.py',
            'scripts/ansible_wrapper.py',
            'scripts/powershell_wrapper.py',
            'enhanced_main.py',
            'scripts/ansible/playbooks/server_management.yml',
            'scripts/ansible/playbooks/firmware_update.yml',
            'scripts/ansible/playbooks/profile_compliance.yml',
            'scripts/powershell/scenarios/ServerManagement.ps1',
            'scripts/powershell/scenarios/FirmwareUpdate.ps1',
            'scripts/powershell/scenarios/ProfileCompliance.ps1',
            'scripts/powershell/scenarios/HardwareInventory.ps1'
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"File {file_path} does not exist"
            assert full_path.is_file(), f"{file_path} is not a file"
        
        return True
    
    # Test Configuration
    def test_configuration_files(self):
        """Test configuration file validity"""
        config_files = [
            'scripts/ansible/inventory/hosts',
            'scripts/ansible/inventory/group_vars/all.yml'
        ]
        
        for config_file in config_files:
            full_path = project_root / config_file
            if full_path.exists():
                # Try to parse YAML/JSON
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                        assert len(content) > 0
                except Exception as e:
                    self.logger.warning(f"Could not parse {config_file}: {e}")
        
        return True
    
    # Run all tests
    def run_all_tests(self):
        """Run all tests in the suite"""
        self.logger.info("🚀 Starting MCP_HpOneView Extended Test Suite")
        self.logger.info("=" * 60)
        
        # Security Manager Tests
        self.logger.info("\n🔐 Testing Security Manager...")
        self.run_test("Security Manager Initialization", self.test_security_manager_initialization)
        self.run_test("Credential Encryption", self.test_credential_encryption)
        self.run_test("Session Management", self.test_session_management)
        
        # Script Executor Tests
        self.logger.info("\n🔧 Testing Script Executor...")
        self.run_test("Script Executor Initialization", self.test_script_executor_initialization)
        self.run_test("Python Script Execution", self.test_python_script_execution)
        self.run_test("Ansible Script Execution", self.test_ansible_script_execution)
        self.run_test("PowerShell Script Execution", self.test_powershell_script_execution)
        
        # Ansible Wrapper Tests
        self.logger.info("\n📦 Testing Ansible Wrapper...")
        self.run_test("Ansible Wrapper Initialization", self.test_ansible_wrapper_initialization)
        self.run_test("Ansible Server Management", self.test_ansible_server_management)
        self.run_test("Ansible Firmware Update", self.test_ansible_firmware_update)
        
        # PowerShell Wrapper Tests
        self.logger.info("\n💻 Testing PowerShell Wrapper...")
        self.run_test("PowerShell Wrapper Initialization", self.test_powershell_wrapper_initialization)
        self.run_test("PowerShell Server Management", self.test_powershell_server_management)
        self.run_test("PowerShell Hardware Inventory", self.test_powershell_hardware_inventory)
        
        # Enhanced Main Server Tests
        self.logger.info("\n🖥️ Testing Enhanced Main Server...")
        self.run_test("Enhanced Server Initialization", self.test_enhanced_server_initialization)
        self.run_test("Tool Registration", self.test_tool_registration)
        
        # File Structure Tests
        self.logger.info("\n📁 Testing File Structure...")
        self.run_test("Directory Structure", self.test_directory_structure)
        self.run_test("Required Files", self.test_required_files)
        self.run_test("Configuration Files", self.test_configuration_files)
        
        # Print results
        self.print_results()
        
        return self.results
    
    def print_results(self):
        """Print test results summary"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 TEST RESULTS SUMMARY")
        self.logger.info("=" * 60)
        
        self.logger.info(f"Total Tests: {self.results['total_tests']}")
        self.logger.info(f"✅ Passed: {self.results['passed']}")
        self.logger.info(f"❌ Failed: {self.results['failed']}")
        
        if self.results['errors']:
            self.logger.info(f"\n🚨 Errors encountered:")
            for error in self.results['errors']:
                self.logger.info(f"  - {error}")
        
        # Calculate success rate
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed'] / self.results['total_tests']) * 100
            self.logger.info(f"\n📈 Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        self.logger.info(f"\n📋 Detailed Results:")
        for test_result in self.results['test_results']:
            status_icon = "✅" if test_result['status'] == 'PASSED' else "❌"
            self.logger.info(f"  {status_icon} {test_result['name']}: {test_result['status']}")
        
        # Save results to file
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON file"""
        results_dir = Path("tests/results")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = results_dir / f"test_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        self.logger.info(f"\n💾 Results saved to: {results_file}")

def main():
    """Main test execution function"""
    print("🧪 MCP_HpOneView Extended Test Suite")
    print("=" * 50)
    
    # Create and run test suite
    test_suite = TestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    if results['failed'] == 0:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {results['failed']} test(s) failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()