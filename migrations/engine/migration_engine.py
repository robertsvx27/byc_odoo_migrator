"""Main migration engine orchestrator."""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from migrations.transformers.python_transformer import PythonTransformer
from migrations.transformers.xml_transformer import XMLTransformer
from migrations.transformers.javascript_transformer import JavaScriptTransformer


class MigrationReport:
    """Report of migration changes."""
    
    def __init__(self, module_name: str, from_version: str, to_version: str):
        self.module_name = module_name
        self.from_version = from_version
        self.to_version = to_version
        self.timestamp = datetime.now().isoformat()
        self.changes = []
        self.errors = []
        self.warnings = []
        self.status = 'pending'
    
    def add_change(self, file_path: str, change_type: str, details: Dict[str, Any]):
        """Add a migration change to the report."""
        self.changes.append({
            'file': file_path,
            'type': change_type,
            'details': details
        })
    
    def add_error(self, message: str, file_path: Optional[str] = None):
        """Add an error to the report."""
        self.errors.append({
            'message': message,
            'file': file_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def add_warning(self, message: str, file_path: Optional[str] = None):
        """Add a warning to the report."""
        self.warnings.append({
            'message': message,
            'file': file_path,
            'timestamp': datetime.now().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            'module': self.module_name,
            'from_version': self.from_version,
            'to_version': self.to_version,
            'timestamp': self.timestamp,
            'status': self.status,
            'changes': self.changes,
            'errors': self.errors,
            'warnings': self.warnings,
            'summary': {
                'total_changes': len(self.changes),
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings)
            }
        }


class OdooMigrationEngine:
    """Main Odoo migration engine."""
    
    SUPPORTED_VERSIONS = ['14.0', '15.0', '16.0', '17.0', '18.0', '19.0']
    
    def __init__(self, config_file: Optional[str] = None, target_version: str = '19.0'):
        self.target_version = target_version
        self.config = self._load_config(config_file)
        self.python_transformer = PythonTransformer()
        self.xml_transformer = XMLTransformer()
        self.javascript_transformer = JavaScriptTransformer()
        self.migration_rules = self._load_migration_rules()
    
    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_migration_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load migration rules from YAML files."""
        rules = {}
        rules_dir = Path(__file__).parent.parent / 'rules'
        
        if rules_dir.exists():
            for rule_file in rules_dir.glob('*.yaml'):
                with open(rule_file, 'r') as f:
                    rules[rule_file.stem] = yaml.safe_load(f) or {}
        
        return rules
    
    def migrate_module(self, module_path: str, from_version: str, to_version: Optional[str] = None) -> MigrationReport:
        """Migrate a module between versions."""
        if to_version is None:
            to_version = self.target_version
        
        module_name = os.path.basename(module_path)
        report = MigrationReport(module_name, from_version, to_version)
        
        try:
            # Validate versions
            if from_version not in self.SUPPORTED_VERSIONS:
                report.add_error(f"Source version {from_version} not supported")
                report.status = 'failed'
                return report
            
            if to_version not in self.SUPPORTED_VERSIONS:
                report.add_error(f"Target version {to_version} not supported")
                report.status = 'failed'
                return report
            
            # Process each version step
            current_version = from_version
            version_index = self.SUPPORTED_VERSIONS.index(current_version)
            target_index = self.SUPPORTED_VERSIONS.index(to_version)
            
            while version_index < target_index:
                next_version = self.SUPPORTED_VERSIONS[version_index + 1]
                self._migrate_version_step(module_path, current_version, next_version, report)
                current_version = next_version
                version_index += 1
            
            report.status = 'success' if not report.errors else 'completed_with_errors'
        
        except Exception as e:
            report.add_error(f"Unexpected error: {str(e)}")
            report.status = 'failed'
        
        return report
    
    def _migrate_version_step(self, module_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Migrate a module for a single version step."""
        for root, dirs, files in os.walk(module_path):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, module_path)
                
                try:
                    if file.endswith('.py'):
                        self._transform_python_file(file_path, from_version, to_version, report)
                    elif file.endswith('.xml'):
                        self._transform_xml_file(file_path, from_version, to_version, report)
                    elif file.endswith('.js'):
                        self._transform_javascript_file(file_path, from_version, to_version, report)
                
                except Exception as e:
                    report.add_error(f"Error processing {rel_path}: {str(e)}", rel_path)
    
    def _transform_python_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform a Python file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        rules = self.migration_rules.get(rule_key, {}).get('python_patterns', [])
        
        changes = self.python_transformer.transform(file_path, rules)
        if changes:
            report.add_change(file_path, 'python', changes)
    
    def _transform_xml_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform an XML file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        rules = self.migration_rules.get(rule_key, {}).get('xml_patterns', [])
        
        changes = self.xml_transformer.transform(file_path, rules)
        if changes:
            report.add_change(file_path, 'xml', changes)
    
    def _transform_javascript_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform a JavaScript file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        rules = self.migration_rules.get(rule_key, {}).get('js_patterns', [])
        
        changes = self.javascript_transformer.transform(file_path, rules)
        if changes:
            report.add_change(file_path, 'javascript', changes)
    
    def save_report(self, report: MigrationReport, output_dir: str = 'migration_reports'):
        """Save migration report to JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f"{report.module_name}_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return report_file
