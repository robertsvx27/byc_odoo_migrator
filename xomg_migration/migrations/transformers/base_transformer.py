"""Base transformer class."""
import logging
import re
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from abc import ABC, abstractmethod
from xomg_migration.migrations.engine.migration_rule import MigrateRule
from ..log import logger

class BaseTransformer(ABC):
    """Base class for code transformers."""
    
    def __init__(self, dry_run:bool=False):
        self.changes = []
        self.dry_run = dry_run
        self._action_method = None
        self._logger = logger

    @abstractmethod
    def transform(self, file_path: str, rules: List[MigrateRule]) -> List[Dict[str, Any]]:
        """Transform a file according to rules."""
        pass

    def migrate_file(self, file_path: str, rule_key: str) -> bool:
        """Transform a file according to rules."""
        # self._action_method = 'migrate_file'
        method = self._get_adapter_method(rule_key.replace("-","_"))
        return method(file_path)

    def _apply_pattern_replacement(self, content: str, rule: MigrateRule) -> tuple:
        """Apply pattern replacement to content."""
        changes = []
        
        if rule.use_regex:
            try:
                new_content = re.sub(rule.pattern, rule.replacement, content)
                if new_content != content:
                    matches = list(re.finditer(rule.pattern, content))
                    changes.append({
                        'pattern': rule.pattern,
                        'replacement': rule.replacement,
                        'matches_found': len(matches),
                        'type': 'regex'
                    })
            except re.error as e:
                changes.append({
                    'pattern': rule.pattern,
                    'error': f"Invalid regex: {str(e)}",
                    'type': 'error'
                })
                new_content = content
        else:
            matches = content.count(rule.pattern)
            if matches > 0:
                new_content = content.replace(rule.pattern, rule.replacement)
                changes.append({
                    'pattern': rule.pattern,
                    'replacement': rule.replacement,
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

    def _apply_delete(self, content: str) -> Tuple[str, List[Dict]]:
        """Elimina coincidencias"""
        changes = []
        matches = list(self.compiled.finditer(content))

        if matches:
            result = self.compiled.sub('', content)
            for match in matches:
                changes.append({
                    'type': 'delete',
                    'matched': match.group(0)[:100],
                    'position': match.span()
                })
            return result, changes
        return content, changes


    def _get_adapter_method(self, method_sufix):

        method = "{}_{}".format(self._action_method,method_sufix)

        try:
            return getattr(self, method)
        except AttributeError:
            raise NotImplementedError(

                    '"%(method)s" method not found, check that all assets are installed '
                    "for the %(transform)s transfomer type.".format(
                    method=method,
                    transform='migrate_file'),
                           ) from AttributeError


    def __enter__(self):
        return self