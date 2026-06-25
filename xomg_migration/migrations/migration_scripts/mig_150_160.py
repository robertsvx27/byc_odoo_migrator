import ast
import json
import re
from io import BytesIO
from typing import List, Dict, Any

from lxml import etree

from xomg_migration.migrations.engine.migration_rule import MigrateRule
from xomg_migration.migrations.transformers import tools
from xomg_migration.migrations.transformers.base_transformer import BaseTransformer
from xomg_migration.migrations.transformers.python_transformer import PythonTransformer


def _replace_toggle_button(
        logger, base_path, module_name=None, dry_run=False):
    if module_name:
        module_path = module_name
    else:
        module_path = base_path
    files_to_process = tools.get_files(module_path, (".xml",))
    replaces = {
        r'widget="\s*toggle_button\s*"': 'widget="boolean_toggle"',
        r"widget='\s*toggle_button\s*'": 'widget="boolean_toggle"',
        r'<attribute\s+name=["\']widget["\']>\s*toggle_button\s*</attribute>': '<attribute name="widget">boolean_toggle</attribute>',
    }

    for file in files_to_process:
        try:
            tools._replace_in_file(
                file,
                replaces,
                log_message=f"Replace toggle_button widget to boolean_toggle widget in file: {file}",
            )
        except Exception as e:
            logger.error(f"Error processing file {file}: {str(e)}")

def migrate_file_v150_v160(env, base_path, module_name=None) -> bool:
    _replace_toggle_button(env._logger, base_path, module_name, env.dry_run)
    return True

PythonTransformer.migrate_file_v150_v160 = migrate_file_v150_v160