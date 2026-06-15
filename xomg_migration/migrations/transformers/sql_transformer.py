from abc import ABC
from typing import List, Dict, Any

from migrations.transformers.base_transformer import BaseTransformer


class SqlTransformer(BaseTransformer):
    """Transform Python code files."""

    def transform(self, file_path: str, rules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass 