import os
from datetime import datetime
from typing import Dict, Any, Optional


class MigrationReport:
    """Report of migration changes."""

    def __init__(self, module_name: str, from_version: str, to_version: str,
                 rel_path :str =''):
        self.module_name = module_name
        self.rel_path = rel_path
        self.from_version = from_version
        self.to_version = to_version
        self.timestamp = datetime.now().isoformat()
        self.changes = []
        self.errors = []
        self.warnings = []
        self.status = 'empty'

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

    def to_light_dict(self )->Dict[str ,Any]:
        if not self.changes and not self.warnings and not self.errors:
            return {
                'module': os.path.basename(self.module_name),
                # 'from_version': self.from_version,
                # 'to_version': self.to_version,
                # 'timestamp': self.timestamp,
                'status': 'empty'
            }
        return {
            'module': os.path.basename(self.module_name),
            # 'from_version': self.from_version,
            # 'to_version': self.to_version,
            # 'timestamp': self.timestamp,
            'status': self.status,
            'changes': self.changes,
            'errors': self.errors,
            'warnings': self.warnings,
            # 'summary': {
            #    'total_changes': len(self.changes),
            #    'total_errors': len(self.errors),
            #    'total_warnings': len(self.warnings)
            # }
        }
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        if not self.changes and not self.warnings and not self.errors:
            return {
                'module': os.path.basename(self.module_name),
                # 'from_version': self.from_version,
                # 'to_version': self.to_version,
                # 'timestamp': self.timestamp,
                'status': 'empty'
            }
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
