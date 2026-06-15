import ast
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from os.path import join as opj
import yaml

from xomg_migration.migrations.transformers import constants, addons_mig
from xomg_migration.migrations.transformers.constants import SUPPORTED_VERSIONS, _MANIFEST_NAMES


def load_config(config_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return yaml.safe_load(f) or {}
    return {}

def get_latest_version_code():
    return SUPPORTED_VERSIONS[len(SUPPORTED_VERSIONS)-1]

def is_module_path(module_path):
    return any([(module_path / x).exists() for x in _MANIFEST_NAMES])


def get_modules_info(path:str, depth=1, modules_name=None):
    """ Return a digest of each installable module's manifest in path repo"""
    return addons_mig.get_modules_info(path,depth,modules_name)