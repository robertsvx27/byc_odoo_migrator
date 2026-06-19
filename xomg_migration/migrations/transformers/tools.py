import ast
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from os.path import join as opj
import yaml

from xomg_migration.migrations.transformers import constants, addons_mig
from xomg_migration.migrations.transformers.constants import SUPPORTED_VERSIONS, _MANIFEST_NAMES


def load_yaml_file(path_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    rules = {}
    if path_file and os.path.exists(path_file):
        rule_file = Path(path_file)
        with open(rule_file, 'r') as f:
            rules[rule_file.stem] = yaml.safe_load(f) or {}
        return rules
    # rules[rule_file.stem] = yaml.safe_load(f) or {}
    return rules

def load_json_file(path_file: Optional[str]) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if path_file and os.path.exists(path_file):
        with open(path_file, 'r') as f:
            return json.load(f) or {}
    return {}

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

def load_text_rule(path_file: str):
    """Carga el formato de texto que mostraste"""
    text_rules = {}
    with open(path_file, 'r', encoding='utf-8') as f:
        lineas = f.readlines()

    lenguaje_actual = None
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        if linea.endswith(':'):
            lenguaje_actual = linea.rstrip(':').strip()
            if lenguaje_actual not in text_rules:
                text_rules[lenguaje_actual] = []
        elif ':' in linea and lenguaje_actual:
            partes = linea.split(':', 1)
            patron = partes[0].strip()
            reemplazo = partes[1].strip() if len(partes) > 1 else None
            if reemplazo == '':
                reemplazo = None
            text_rules[lenguaje_actual]['pattern'] = patron
            text_rules[lenguaje_actual]['replacement'] = reemplazo
            text_rules[lenguaje_actual]['action'] = 'REPLACE'
            # self._compilar_y_guardar(lenguaje_actual, patron, reemplazo)
    return text_rules