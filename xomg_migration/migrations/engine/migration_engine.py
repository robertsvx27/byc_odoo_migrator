"""Main migration engine orchestrator."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List, Tuple

from colorama import Fore, Style

from xomg_migration.migrations.engine.migration_report import MigrationReport
from xomg_migration.migrations.engine.migrator_engine_rule import MigratorEngineRules
from xomg_migration.migrations.transformers import tools, constants
from xomg_migration.migrations.transformers.constants import SUPPORTED_VERSIONS, _DEFAULT_EXCLUDED_DIRS
from xomg_migration.migrations.transformers.javascript_transformer import JavaScriptTransformer
from xomg_migration.migrations.transformers.python_transformer import PythonTransformer
from xomg_migration.migrations.transformers.xml_transformer import XMLTransformer



class OdooMigrationEngine:
    """Main Odoo migration engine."""
    
    # SUPPORTED_VERSIONS = ['14.0', '15.0', '16.0', '17.0', '18.0', '19.0']
    
    def __init__(self,
                 base_path: str,
                 config_file: Optional[str] = None,
                 from_version:str=''
                 , target_version: str = '19.0'
                 ,modules_path=None,
                 file_types=None,
                 file_patterns=None,
                 excluded_dirs=None,
                excluded_modules = None
                 , dry_run: bool = False):
        self.dry_run = dry_run
        self.target_version = target_version
        self.start_version = from_version
        self.config = tools.load_config(config_file)
        self._root_path = Path(base_path)
        self._modules_path = modules_path or {}
        self._file_types = file_types or {}
        self._file_patterns = file_patterns or {}
        self._excluded_dirs = excluded_dirs or {}
        self._excluded_modules = excluded_modules or {}
        self.props = self.config.get('defaults', {})
        self.python_transformer = PythonTransformer(self.dry_run)
        self.xml_transformer = XMLTransformer(self.dry_run)
        self.javascript_transformer = JavaScriptTransformer(self.dry_run)
        self.migration_rules = {}
        #self.python_transformer = PythonTransformer(self.dry_run)
        #self.xml_transformer = XMLTransformer(self.dry_run)
        #self.javascript_transformer = JavaScriptTransformer(self.dry_run)
        #path_rules = self.props.get('path_rules', False)
        #self.migration_rules = None
        #self._load_migration_rules(path_rules)

    def run(self):
        """Run migration for all manifests"""


        print("=" * 70)
        print("📋 MIGRACIÓN DE MANIFEST FILES Odoo desde 13 → 19")
        print("=" * 70)
        print(f"🔧 Modo: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"🔧 El log que se mostrara sera de los archivos actualizados y con error")
        print("-" * 70)
        path_rules = self.props.get('path_rules', False)
        self._load_migration_rules(path_rules)
        #manifests = self.find_manifests()
        # for module_migration in self._module_migrations:
        #    module_migration.run()
        modules_addons = self._modules_path
        for i, (key, module) in enumerate(modules_addons.items(), 1):

            report = self.migrate_module(module)
            if report.status in ['failed','success']:
                print(f"\n[{i}/{len(modules_addons)}] 📄\t{module.get('full_path')}")

            # self.results['processed'] += 1

    def find_manifests(self) -> List[Path]:
        """Encuentra archivos __manifest__.py respetando exclusiones"""
        manifests = []

        # Log de exclusiones para debug
        exclusion_log = {
            'by_dir': {},
            'by_pattern': {},
            'by_backup': []
        }
        for manifest in self._root_path.rglob('__manifest__.py'):
            # Verificar exclusión por directorio
            exclude, reason = self.should_exclude_dir(manifest.parent)
            if exclude:
                continue
            exclude, reason = self.should_exclude_file(manifest)
            if exclude:
                continue
            manifests.append(manifest)
        return manifests

    def should_exclude_file(self, file_path: str) -> Tuple[bool, str]:
        path = Path(file_path)
        if self._file_patterns:
            for fp in self._file_patterns:
                if fp != '*' and path.match(fp):
                    return False, ''
        for fp in constants._DEFAULT_EXCLUDED_PATTERNS:
            if fp != '*' and path.match(fp):
                return True, ''
        return False,''

    def matches_file_pattern(self, file_path: str) -> bool:
        path = Path(file_path)
        for f_pattern in self._file_patterns:
            if f_pattern != '*':
                if not path.match(f_pattern):
                    return False
        return True

    def matches_dir_pattern(self, dir_path: Path) -> Tuple[bool, str]:
        """Verifica si un directorio coincide con algún patrón de exclusión"""
        dir_name = dir_path.name

        for pattern in self._excluded_dirs:
            # Convertir patrón glob a regex simple
            regex_pattern = pattern.replace('*', '.*')
            if re.match(regex_pattern, dir_name, re.IGNORECASE):
                return True, f"pattern:{pattern}"

        return False, ''

    def should_exclude_dir(self, dir_path: Path) -> Tuple[bool, str]:
        """
        Determina si un directorio debe ser excluido
        Retorna: (excluir, razón)
        """

        # 2. Verificar contra lista de exclusión exacta
        for excluded in self._excluded_modules:
            if excluded.lower() in [p.lower() for p in dir_path.parts]:
                return True, f"exact_match:{excluded}"

        # 3. Verificar contra patrones de directorio
        matches, pattern = self.matches_dir_pattern(dir_path)
        if matches:
            return True, f"pattern_match:{pattern}"


        return False, ''

    def _load_migrator_rule(self,path_rules=None)-> MigratorEngineRules:
        if path_rules:
            path_rules = Path(path_rules)
            rules_dir = Path(path_rules.resolve(strict=True))

        else:
            rules_dir = Path(__file__).parent.parent / 'rules'
        mg_rules = MigratorEngineRules([str(rules_dir)])
        return mg_rules

    def _load_migration_rules(self,path_rules=None):
        """Load migration rules from YAML files."""
        # rules = {}
        if path_rules:
            path_rules = Path(path_rules)
            rules_dir =Path(path_rules.resolve(strict=True))

        else:
            rules_dir = Path(__file__).parent.parent / 'rules'
        #
        # if rules_dir.exists():
        #     for rule_file in rules_dir.glob('*.yaml'):
        #         with open(rule_file, 'r') as f:
        #             rules[rule_file.stem] = yaml.safe_load(f) or {}
        #
        # return rules
        self.migration_rules = MigratorEngineRules([str(rules_dir)])

    def migrate_module(self, module_obj: Dict[str, Any]) -> MigrationReport:
        """Migrate a module between versions."""
        to_version = self.target_version
        from_version = self.start_version
        # module_name = os.path.basename(module_path)
        report = MigrationReport(module_obj.get('name', ''), from_version, to_version)

        try:
            # Validate versions
            if from_version not in SUPPORTED_VERSIONS:
                report.add_error(f"Source version {from_version} not supported")
                report.status = 'failed'
                return report
            
            if to_version not in SUPPORTED_VERSIONS:
                report.add_error(f"Target version {to_version} not supported")
                report.status = 'failed'
                return report
            
            # Process each version step
            current_version = from_version
            version_index = SUPPORTED_VERSIONS.index(current_version)
            target_index = SUPPORTED_VERSIONS.index(to_version)
            
            while version_index < target_index:
                next_version = SUPPORTED_VERSIONS[version_index + 1]
                self._migrate_version_step(module_obj.get('full_path',''), current_version, next_version, report)
                current_version = next_version
                version_index += 1
            
            report.status = 'success' if not report.errors else 'completed_with_errors'
        
        except Exception as e:
            report.add_error(f"Unexpected error: {str(e)}")
            report.status = 'failed'
        if not report.changes and not report.warnings and not report.errors:
            report.status = 'empty'
        return report
    
    def _migrate_version_step(self, module_path: str, from_version: str,
                              to_version: str, report: MigrationReport):
        """Migrate a module for a single version step."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        #if rule_key == 'v180-v190':
        self.python_transformer.migrate_file(module_path, rule_key)
        for root, dirs, files in os.walk(module_path):
            # Skip __pycache__ and .git directories
            dirs[:] = [d for d in dirs if d not in _DEFAULT_EXCLUDED_DIRS]
            extensions = [f.value for f in self._file_types]
            if not extensions:
                extensions = constants._ALLOWED_EXTENSIONS
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, module_path)
                exclude, msg = self.should_exclude_file(file_path)
                if exclude:
                    continue
                try:
                    if file.endswith('.py') and '.py' in extensions:
                        self._transform_python_file(file_path, from_version, to_version, report)
                    elif file.endswith('.xml')  and '.xml' in extensions:
                        self._transform_xml_file(file_path, from_version, to_version, report)
                    elif file.endswith('.js')  and '.js' in extensions:
                        self._transform_javascript_file(file_path, from_version, to_version, report)
                
                except Exception as e:
                    report.add_error(f"Error processing {rel_path}: {str(e)}", rel_path)
    
    def _transform_python_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform a Python file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        # rules = self.migration_rules.get(rule_key, {}).get('python_patterns', [])
        # rules = self.migrator_rules.rules.get(rule_key, {}).get('python_patterns', [])
        lang_pt = 'python_patterns'
        target_list = getattr(self.migration_rules.rules[rule_key], lang_pt)
        if target_list:
            changes = self.python_transformer.transform(file_path, target_list)
            if changes:
                report.add_change(file_path, 'python', changes)

    def _fast_transform_python_file(self,content,version):
        rule_key = 'common_patterns'
        if isinstance(float, version):
            nro_version = int(version)
            from_version = str(nro_version - 1)+"0"
            to_version = str(nro_version)+"0"
            rule_key = f"v{from_version}-v{to_version}"

    def _transform_xml_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform an XML file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        #rules = self.migration_rules.get(rule_key, {}).get('xml_patterns', [])

        # rules = self.migrator_rules.rules.get(rule_key, {}).get('xml_patterns', [])
        # if rules:
        #     changes = self.xml_transformer.transform(file_path, rules)
        #     if changes:
        #         report.add_change(file_path, 'xml', changes)

        lang_pt = 'xml_patterns'
        target_list = getattr(self.migration_rules.rules[rule_key], lang_pt)
        if target_list:
            changes = self.xml_transformer.transform(file_path, target_list)
            if changes:
                report.add_change(file_path, 'xml', changes)

    def _transform_javascript_file(self, file_path: str, from_version: str, to_version: str, report: MigrationReport):
        """Transform a JavaScript file."""
        rule_key = f"v{from_version.replace('.', '')}-v{to_version.replace('.', '')}"
        # rules = self.migration_rules.get(rule_key, {}).get('js_patterns', [])
        # rules = self.migrator_rules.rules.get(rule_key, {}).get('js_patterns', [])
        # if rules:
        #     changes = self.javascript_transformer.transform(file_path, rules)
        #     if changes:
        #         report.add_change(file_path, 'javascript', changes)
        lang_pt = 'js_patterns'
        target_list = getattr(self.migration_rules.rules[rule_key], lang_pt)
        if target_list:
            changes = self.javascript_transformer.transform(file_path, target_list)
            if changes:
                report.add_change(file_path, 'js', changes)

    def save_report(self, report: MigrationReport, output_dir: str = 'migration_reports'):
        """Save migration report to JSON file."""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(output_dir, f"{report.module_name}_{timestamp}.json")
        
        with open(report_file, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        return report_file

