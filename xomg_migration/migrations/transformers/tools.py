import ast
import json
import os
import pathlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from os.path import join as opj
import yaml

from xomg_migration.migrations.log import logger
from xomg_migration.migrations.transformers import constants, addons_mig
from xomg_migration.migrations.transformers.constants import SUPPORTED_VERSIONS, _MANIFEST_NAMES,_DEFAULT_EXCLUDED_DIRS


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


def get_modules_info(path:str, depth=1, modules_name=None,file_types=None,file_patterns=None,
                     exc_modules=None, exc_dirs=None):
    """ Return a digest of each installable module's manifest in path repo"""
    modules_founded=addons_mig.get_modules_info(path,depth,modules_name,file_types,file_patterns,exc_modules,exc_dirs)
    new_modules = {}
    if modules_name:
        for key, values in modules_founded.items():
            if key in modules_name and key not in new_modules:
                new_modules[key] = values
    else:
        new_modules = modules_founded
    return new_modules
    return modules_founded

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

def get_files(module_path, extensions):
    """
    Returns a list of files with the specified extensions within the module_path.
    """
    file_paths = []
    module_dir = pathlib.Path(module_path)

    if not module_dir.is_dir():
        raise Exception(f"'{module_path}' is not a valid directory.")

    for ext in extensions:
        file_paths.extend(module_dir.rglob(f"*{ext}"))
    clean_file_paths = []
    for file_path in file_paths:
        exclude = False
        for exclude_dir in _DEFAULT_EXCLUDED_DIRS:
            if exclude_dir.lower() in [p.lower() for p in file_path.parts[:-1]]:
                exclude = True
                break
        if not exclude:
            clean_file_paths.append(file_path)
    return clean_file_paths


def _read_content(file_path):
    f = open(file_path, "r")
    text = f.read()
    f.close()
    return text


def _write_content(file_path, content):
    f = open(file_path, "w")
    f.write(content)
    f.close()

def _replace_in_file(file_path, replaces, log_message=False):
    current_text = _read_content(file_path)
    new_text = current_text

    for old_term, new_term in replaces.items():
        new_text = re.sub(old_term, new_term or "", new_text)

    # Write file if changed
    if new_text != current_text:
        if not log_message:
            log_message = "Changing content of file: %s" % file_path.name
        logger.info(log_message)
        _write_content(file_path, new_text)
    return new_text
