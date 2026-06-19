"""Python code transformer."""
from enum import Enum
from typing import Dict, List, Any

from xomg_migration.migrations.engine.migration_rule import MigrateRule
from xomg_migration.migrations.transformers.base_transformer import BaseTransformer



class PythonTransformer(BaseTransformer):
    """Transform Python code files."""
    
    def transform(self, file_path: str, rules: List[MigrateRule]) -> List[Dict[str, Any]]:
        """Transform Python file according to rules."""
        try:
            content = self._read_file(file_path)
            all_changes = []
            
            for rule in rules:
                if not rule.enabled:
                    continue
                
                #pattern = rule.get('pattern')
                #replacement = rule.get('replacement')
                #action = rule.get('action', 'replace')
                #use_regex = rule.get('use_regex', False)
                content,changes = rule.apply(content)
                # if rule.pattern and rule.action == ActionType.REPLACE:
                #    content, changes = self._apply_pattern_replacement(content, rule)
                all_changes.extend(changes)
            
            if all_changes and not self.dry_run:
                self._write_file(file_path, content)
            #if self.dry_run:
            #    print('\n****Mode dry-run: python')
            return all_changes
        
        except Exception as e:
            return [{'error': str(e), 'file': file_path}]

    def _action_change_model_name(self,content,pattern,replacement):
        pass
