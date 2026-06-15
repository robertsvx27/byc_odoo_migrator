"""JavaScript code transformer."""

from typing import Dict, List, Any

from migrations.engine.rule_loader import MigrationRule, ActionType
from xomg_migration.migrations.transformers.base_transformer import BaseTransformer


class JavaScriptTransformer(BaseTransformer):
    """Transform JavaScript files."""
    
    def transform(self, file_path: str, rules: List[MigrationRule]) -> List[Dict[str, Any]]:
        """Transform JavaScript file according to rules."""
        try:
            content = self._read_file(file_path)
            all_changes = []
            
            for rule in rules:
                if not rule.enabled:
                    continue

                # pattern = rule.get('pattern')
                # replacement = rule.get('replacement')
                # action = rule.get('action', 'replace')
                # use_regex = rule.get('use_regex', False)

                if rule.pattern and rule.action == ActionType.REPLACE:
                    content, changes = self._apply_pattern_replacement(content, rule)
                    all_changes.extend(changes)
            
            if all_changes and not self.dry_run:
                self._write_file(file_path, content)
            #elif self.dry_run:
            #    print('\n****Mode dry-run: javascript')
            return all_changes
        
        except Exception as e:
            return [{'error': str(e), 'file': file_path}]
