"""Python code transformer."""

from typing import Dict, List, Any
from migrations.transformers.base_transformer import BaseTransformer


class PythonTransformer(BaseTransformer):
    """Transform Python code files."""
    
    def transform(self, file_path: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform Python file according to rules."""
        try:
            content = self._read_file(file_path)
            all_changes = []
            
            for rule in rules:
                if not rule.get('enabled', True):
                    continue
                
                pattern = rule.get('pattern')
                replacement = rule.get('replacement')
                use_regex = rule.get('use_regex', False)
                
                if pattern and replacement:
                    content, changes = self._apply_pattern_replacement(
                        content, pattern, replacement, use_regex
                    )
                    all_changes.extend(changes)
            
            if all_changes:
                self._write_file(file_path, content)
            
            return all_changes
        
        except Exception as e:
            return [{'error': str(e), 'file': file_path}]
