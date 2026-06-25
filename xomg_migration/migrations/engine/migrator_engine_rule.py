import re
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple

from pydantic import BaseModel, Field

from xomg_migration.migrations.engine.migration_rule import MigrateRule, ActionType, _get_patterns_allowed
from xomg_migration.migrations.transformers import tools


class RuleRaw(BaseModel):
    python_patterns: list[MigrateRule] = Field(default_factory=list)
    xml_patterns: list[MigrateRule] = Field(default_factory=list)
    js_patterns: list[MigrateRule] = Field(default_factory=list)
    sql_patterns: list[MigrateRule] = Field(default_factory=list)
    css_patterns: list[MigrateRule] = Field(default_factory=list)


class MigratorEngineRules:
    """Report of migration changes."""
    # _rules_raw: Dict[str, List[MigrateRule]] = {
    #     'python_patterns': [],
    #     'xml_patterns': [],
    #     'js_patterns': [],
    #     'sql_patterns': []
    # }
    # _rules_raw = Dict[str, List[MigrateRule]]

    def __init__(self, config_files: List[str],dry_run: bool=False):
        self._patterns = {}
        self.rules: dict[str, RuleRaw] = {}
        self.dry_run = dry_run
        self._compiled = {}
        if config_files:
            self.load_rules(config_files)


    def load_rules(self, config_files: List[str]):
        all_rules = []
        for path_file in config_files:
            rule_file_path = Path(path_file)
            if not rule_file_path.exists():
                continue
            for rule_file in rule_file_path.glob('*.yaml'):
                ext = Path(rule_file).suffix
                config = {}
                if ext == '.json':
                    config = tools.load_json_file(str(rule_file))
                elif ext in ['.yml', '.yaml']:
                    config = tools.load_yaml_file(str(rule_file))
                elif ext in ['.txt', '.text']:
                    # Formato texto personalizado
                    config = tools.load_text_rule(str(rule_file))
                if config:
                    all_rules.append(config)

        for config in all_rules:
            for file_name, rule_list in config.items():
                #if lang not in self.rules:
                #     self.rules[lang] = []
                rules_find = rule_list.get('common',{}) if 'common' in rule_list else rule_list
                _rules_raw = {}
                for rule_type, rule_data in rules_find.items():
                    if rule_type == 'version':
                        continue
                    if not rule_data:
                        continue
                    for values in rule_data:
                        action = ActionType(values.get('action', 'replace'))
                        flags = re.RegexFlag(values.get('flags', 0))
                        patron = values.get('pattern','')
                        reemplazo = values.get('replacement','')
                        description = values.get('description', values.get('id','N.M'))
                        use_regex = values.get('use_regex', False)
                        # print('rule',values.get('description'), file_name)
                        rule = MigrateRule(pattern=patron,
                                           action=action,
                                           replacement=reemplazo,
                                           description=description,
                                           enabled=values.get('enabled',True),
                                           use_regex=use_regex,
                                           version=file_name,
                                           flags=flags)
                        if file_name not in self.rules:
                            # _rules_raw[rule_type] = []
                            self.rules[file_name] = RuleRaw()
                        target_list = getattr(self.rules[file_name], rule_type)
                        target_list.append(rule)
                        #_rules_raw[rule_type].append(rule)
                # self.rules[file_name]=_rules_raw
                    #self._compile_and_save(lang, patron, reemplazo,action)

    def has_rules_for(self, language: str) -> bool:
        """Verifica si hay reglas para un lenguaje específico"""
        lang = _get_patterns_allowed(language)
        return bool(self.rules.get(lang, []))

    def _compile_and_save(self, lang: str, pattern: str, replacement: str = '', action:ActionType=ActionType.REPLACE):
        """Compila y guarda la regla"""
        flags = re.DOTALL | re.MULTILINE
        pattern_replace = re.compile(pattern, flags)

        self.rules[lang].append({
            'pattern': pattern_replace,
            'reemplazo': replacement,
            'original': pattern
        })

    def add_rule(self, lang: str, pattern: str, replacement: str = '',action: str='replace',description:str='',
                 version:str='common'):
        """Agrega regla sin compilar (lazy compilation)"""
        lang_pt = _get_patterns_allowed(lang)

        rule = MigrateRule(pattern=pattern,
                           action=ActionType(action),
                           replacement=replacement,
                           description=description,
                           version=version)
        if version not in self.rules:
            self.rules[version] = RuleRaw()

        target_list = getattr(self.rules[version], lang_pt)
        target_list.append(rule)
        # Limpiar cache cuando se agregan nuevas reglas
        self._get_pattern.cache_clear()

    @lru_cache(maxsize=256)
    def _get_pattern(self, patron: str, flags: re.RegexFlag=re.NOFLAG) -> re.Pattern:
        """Compila y cachea patrones individuales"""

        return re.compile(patron, flags)

    def apply_to_file(self, file_path: str, lang: str) -> Tuple[str, List[str]]:
        """Aplica reglas a un archivo y retorna cambios realizados"""
        with open(file_path, 'r', encoding='utf-8') as f:
            result = f.read()

        changes = []
        old_content = result

        for patron, reemplazo, action in self._rules_raw.get(lang, []):
            # Verificar si hay coincidencias
            pattern = self._get_pattern(patron)
            if reemplazo and action.REPLACE:
                result = pattern.sub(reemplazo, result)
            elif action.FORMAT_CLASS:
                # print('''format class''')
                content = self._action_change_model_name(result,pattern)
            if old_content != result:
                changes.append(f"  Applied: ({action.value})")
            #if rule.compiled.search(result):
            #    old_content = result
            #    result = rule.apply(result)
            #    if old_content != result:
            #        changes.append(f"  Applied: {rule.description} ({rule.action.value})")

        return result, changes

    def apply(self, content: str, lang: str) -> str:
        """Aplica reglas compilando lazy"""
        resultado = content
        lang = _get_patterns_allowed(lang)
        for key_file, values in self.rules.items():
            for key in getattr(self.rules[key_file],lang):
                if not key.enabled:
                    continue
                #print(rule_key)
        # for patron, reemplazo,action in self.rules.get(lang, []):
                pattern = self._get_pattern(key.pattern,key.flags)
                if key.replacement and key.action == ActionType.REPLACE:
                    resultado = pattern.sub(key.replacement, resultado)
                elif key.action == ActionType.FORMAT_CLASS:
                    resultado = self._action_change_model_name(resultado,pattern)
                elif key.action == ActionType.CHANGE_VIEW:
                    resultado = key.apply_upgrade_view(resultado)
        return resultado

    def load_fields(self, **kwargs):
        if not kwargs:
            kwargs = {}
        self.pattern = kwargs.get('pattern',None)
        self.description = kwargs.get('description', None)
        self.replacement = kwargs.get('replacement', None)
        self.action = kwargs.get('action', ActionType.REPLACE)
        self.enabled = kwargs.get('enabled', True)
        self.use_regex = kwargs.get('use_regex', False)
        self.file_pattern = kwargs.get('file_pattern', '*')
        self.only_in = kwargs.get('only_in', [])
        self.exclude = kwargs.get('exclude', [])

    def _action_change_model_name(self, content, pattern: re.Pattern)->str:
        resultado = content
        # print(content)
        full_model_name =  re.search(pattern,content)
        if full_model_name:
            model_name = full_model_name.group(1)
            camel = re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), model_name)
            camel = camel[0].upper() + camel[1:] if camel else ""
            resultado = resultado.replace(model_name,camel)
        return resultado
