"""Base transformer class."""

import re
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """Base class for code transformers."""
    
    def __init__(self):
        self.changes = []
    
    @abstractmethod
    def transform(self, file_path: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform a file according to rules."""
        pass
    
    def _apply_pattern_replacement(self, content: str, pattern: str, replacement: str, use_regex: bool = False) -> tuple:
        """Apply pattern replacement to content."""
        changes = []
        
        if use_regex:
            try:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    matches = list(re.finditer(pattern, content))
                    changes.append({
                        'pattern': pattern,
                        'replacement': replacement,
                        'matches_found': len(matches),
                        'type': 'regex'
                    })
            except re.error as e:
                changes.append({
                    'pattern': pattern,
                    'error': f"Invalid regex: {str(e)}",
                    'type': 'error'
                })
                new_content = content
        else:
            matches = content.count(pattern)
            if matches > 0:
                new_content = content.replace(pattern, replacement)
                changes.append({
                    'pattern': pattern,
                    'replacement': replacement,
                    'matches_found': matches,
                    'type': 'literal'
                })
            else:
                new_content = content
        
        return new_content, changes
    
    def _read_file(self, file_path: str) -> str:
        """Read file content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _write_file(self, file_path: str, content: str):
        """Write file content."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
