from abc import ABC
from typing import List, Dict, Any

from xomg_migration.migrations.engine.migration_rule import MigrateRule
from xomg_migration.migrations.transformers.base_transformer import BaseTransformer


class SqlTransformer(BaseTransformer):
    """Transform Python code files."""

    def transform(self, file_path: str, rules: List[MigrateRule]) -> List[Dict[str, Any]]:
        pass 