import re
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple, Optional

from pydantic import BaseModel, Field

from xomg_migration.migrations.transformers import tools


class ActionType(Enum):
    REPLACE = "replace"
    DELETE = "delete"
    INSERT = "insert"
    COMMENT = "comment"
    DELETE_CLASS = "delete_class"
    FORMAT_CLASS = "format_class"
    RENAME_FIELD = "rename_field"
    DELETE_FIELD = "delete_field"
    DELETE_ATTR = "delete_attr"
    CHANGE_VIEW = "change_view"
    FORMAT_VIEW_17 = "format_view_170"

class FileType(Enum):
    PYTHON = ".py"
    XML = ".xml"
    SQL = ".sql"
    JS = ".js"
    VIEW = "_view.xml"
    MODEL = ".py"
    SECURITY = "_security.xml"
    DATA = "_data.xml"


fields_rules = ['id', 'pattern','description','replacement','action', 'enabled','use_regex']

class MigrateRule(BaseModel):
    """Representa una regla de migración"""
    pattern: str
    action: ActionType
    replacement: Optional[str] = None
    description: str = ""
    enabled: bool = True
    use_regex: bool = False
    version: str = 'common'
    flags: re.RegexFlag = re.NOFLAG
    _compiled: Optional[re.Pattern] = None

    @lru_cache(maxsize=256)
    def _get_pattern(self, patron: str) -> re.Pattern:
        """Compila y cachea patrones individuales"""

        return re.compile(patron, re.DOTALL | re.MULTILINE)

    @property
    def compiled(self) -> re.Pattern:
        if self._compiled is None:
            flags = self.flags
            self._compiled = re.compile(self.pattern, flags)
        return self._compiled

    def apply(self, content: str) -> tuple:
        """Aplica la regla al contenido"""
        # if self.action == ActionType.DELETE:
        #     return self.compiled.sub('', content)
        # elif self.action == ActionType.REPLACE and self.replacement:
        #     return self.compiled.sub(self.replacement, content)
        # elif self.action == ActionType.COMMENT and self.replacement:
        #     # Comentar líneas que coinciden
        #     def comment_line(match):
        #         return f"# TODO MIGRATION: {self.replacement}\n# {match.group(0)}"
        #
        #     return self.compiled.sub(comment_line, content)
        new_content = content
        changes = []
        try:
            if self.use_regex:
                # pattern = self._get_pattern(key.pattern)
                # if key.replacement and key.action == ActionType.REPLACE:
                #     resultado = pattern.sub(key.replacement, resultado)
                # elif key.action == ActionType.FORMAT_CLASS:
                #     print('''format class''')
                #     resultado = self._action_change_model_name(resultado, pattern)
                #pattern = self._get_pattern(self.pattern)
                if self.action == ActionType.DELETE:
                    new_content = self.compiled.sub('', new_content)
                elif self.action == ActionType.REPLACE and self.replacement:
                    new_content = self.compiled.sub(self.replacement, new_content)
                elif self.action == ActionType.DELETE_ATTR:
                    new_content = self.remove_attribute_from_tag(new_content,*self.pattern.split(","))
                elif self.action == ActionType.COMMENT and self.replacement:
                    def comment_line(match):
                        return f"# TODO MIGRATION: {self.replacement}\n# {match.group(0)}"
                    new_content = self.compiled.sub(comment_line, new_content)
                elif self.action == ActionType.FORMAT_CLASS:
                    # print('''format class''')
                    new_content = self._action_change_model_name(new_content)
                #elif self.action == ActionType.CHANGE_VIEW:
                #    new_content = self._action_upgrade_view(new_content)
                if new_content != content:
                    #matches = list(re.finditer(self.pattern, content))
                    matches = list(self.compiled.finditer(content))
                    changes.append({
                        'pattern': self.pattern,
                        'replacement': self.replacement,
                        'matches_found': len(matches),
                        'type': 'regex'
                    })
            else:
                matches = content.count(self.pattern)
                if matches > 0:
                    new_content = content.replace(self.pattern, self.replacement)
                    changes.append({
                        'pattern': self.pattern,
                        'replacement': self.replacement,
                        'matches_found': matches,
                        'type': 'literal'
                    })
                else:
                    new_content = content
        except re.error as e:
            changes.append({
                'pattern': self.pattern,
                'error': f"Invalid regex: {str(e)}",
                'type': 'error'
            })
            new_content = content
        return  new_content, changes

    def _action_change_model_name(self, content) -> str:
        resultado = content
        # print(content)
        full_model_name = self.compiled.search(content)# re.search(pattern, content)
        if full_model_name:
            model_name = full_model_name.group(1)
            camel = re.sub(r'_([a-zA-Z])', lambda m: m.group(1).upper(), model_name)
            camel = camel[0].upper() + camel[1:] if camel else ""
            resultado = resultado.replace(model_name, camel)
        return resultado

    def apply_upgrade_view(self, content: str) -> tuple:
        new_content = content
        changes = []
        try:
            view_type = self.pattern
            if view_type == "migrate_report":
                new_content = self.rpt_view_v130_v140(new_content)
            elif view_type == "migrate_act_window":
                new_content = self.act_view_v130_v140(new_content)
        except Exception as e:
            changes.append({
                'pattern': self.pattern,
                'error': f"Invalid regex: {str(e)}",
                'type': 'error'
            })
            new_content = content
        return new_content,changes

    @staticmethod
    def rpt_view_v130_v140(content:str)-> str:
        """
           Migra reportes del formato antiguo (Odoo 13) al nuevo formato (Odoo 17)
           """
        changes = []
        report_pattern = r'''
          <report
              \s+id="([^"]+)"           # id del reporte
              \s+model="([^"]+)"        # modelo
              \s+report_type="([^"]+)"  # tipo de reporte
              \s+string="([^"]+)"       # nombre/string
              \s+name="([^"]+)"         # nombre del reporte
              \s+file="([^"]+)"         # archivo
              \s*/>
          '''

        def replace_report(match):
            # Obtener valores con defaults
            report_id = match.group(1) or "report_unknown"
            model = match.group(2) or "unknown.model"
            report_type = match.group(3) or "qweb-pdf"
            string = match.group(4) or "Report"
            name = match.group(5) or "report_name"
            file = match.group(6) or name

            # Convertir modelo a ref para binding_model_id
            model_parts = model.split('.')
            if len(model_parts) > 1:
                # medical.prescription.order -> medical_prescription_order
                model_ref = '_'.join(model_parts)
            else:
                model_ref = model

            binding_ref = f"byc_mcm.model_{model_ref}"

            # Construir nuevo reporte
            new_report = f'''<record id="{report_id}" model="ir.actions.report">
                   <field name="name">{string}</field>
                   <field name="model">{model}</field>
                   <field name="report_type">{report_type}</field>
                   <field name="report_name">{name}</field>
                   <field name="report_file">{file}</field>
                   <field name="print_report_name"></field>
                   <field name="binding_model_id" ref="{binding_ref}"/>
               </record>'''

            # changes.append({
            #     'old_id': report_id,
            #     'new_id': report_id,
            #     'model': model,
            #     'old_format': match.group(0).strip(),
            #     'new_format': new_report.strip()
            # })

            return new_report

        # Aplicar reemplazo

        result = re.sub(report_pattern, replace_report, content, flags=re.VERBOSE | re.DOTALL)

        return result

    @staticmethod
    def act_view_v130_v140(content:str)-> str:
        """
           Encuentra y migra todos los act_window en el contenido XML
           """
        changes = []

        # Buscar todos los act_window
        act_pattern = r'<act_window[^>]*/>'

        def process_act_window(match):
            act_text = match.group(0)

            # Extraer atributos
            id_match = re.search(r'id="([^"]+)"', act_text)
            name_match = re.search(r'name="([^"]+)"', act_text)
            res_model_match = re.search(r'res_model="([^"]+)"', act_text)
            binding_match = re.search(r'binding_model="([^"]+)"', act_text)
            view_mode_match = re.search(r'view_mode="([^"]+)"', act_text)
            target_match = re.search(r'target="([^"]+)"', act_text)
            view_id_match = re.search(r'view_id="([^"]+)"', act_text)
            context_match = re.search(r'context="([^"]+)"', act_text)
            domain_match = re.search(r'domain="([^"]+)"', act_text)

            # Construir diccionario de atributos
            attrs = {
                'id': id_match.group(1) if id_match else 'action_unknown',
                'name': name_match.group(1) if name_match else 'Action',
                'res_model': res_model_match.group(1) if res_model_match else 'unknown.model',
                'binding_model': binding_match.group(1) if binding_match else None,
                'view_mode': view_mode_match.group(1) if view_mode_match else 'form',
                'target': target_match.group(1) if target_match else 'current',
                'view_id': view_id_match.group(1) if view_id_match else None,
                'context': context_match.group(1) if context_match else None,
                'domain': domain_match.group(1) if domain_match else None,
            }

            # Construir nuevo formato
            new_act = f'''<record model="ir.actions.act_window" id="{attrs['id']}">
                <field name="name">{attrs['name']}</field>
                <field name="res_model">{attrs['res_model']}</field>
                <field name="view_mode">{attrs['view_mode']}</field>
                <field name="target">{attrs['target']}</field>'''

            if attrs['view_id']:
                new_act += f'''
                <field name="view_id" ref="{attrs['view_id']}"/>'''

            if attrs['context']:
                new_act += f'''
                <field name="context">{attrs['context']}</field>'''

            if attrs['domain']:
                new_act += f'''
                <field name="domain">{attrs['domain']}</field>'''

            if attrs['binding_model']:
                binding_ref = attrs['binding_model'].replace('.', '_')
                new_act += f'''
                <field name="binding_model_id" ref="byc_mcm.model_{binding_ref}"/>'''

            new_act += '''
            </record>'''

            changes.append({
                'old_format': act_text,
                'new_format': new_act,
                'act_id': attrs['id'],
                'res_model': attrs['res_model'],
                'binding_model': attrs['binding_model']
            })

            return new_act

        new_content = re.sub(act_pattern, process_act_window, content, flags=re.DOTALL)

        return new_content

    @staticmethod
    def remove_attribute_from_tag(xml_content: str, tag: str, attribute: str) -> str:
        """
        Elimina un atributo específico de una etiqueta XML
        """
        # Escapar el nombre del atributo para seguridad
        tag_escaped = re.escape(tag)
        attr_escaped = re.escape(attribute)

        # Patrón para encontrar la etiqueta con el atributo
        def process_match(match):
            full_tag = match.group(0)

            # Eliminar el atributo
            attr_pattern = rf'\s+{attr_escaped}\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s/>]+)'
            cleaned_tag = re.sub(attr_pattern, '', full_tag)

            # Limpiar espacios extras SOLO dentro del tag
            cleaned_tag = re.sub(r'\s+>', '>', cleaned_tag)
            cleaned_tag = re.sub(r'\s+/>', '/>', cleaned_tag)
            cleaned_tag = re.sub(r'\s{2,}', ' ', cleaned_tag)

            return cleaned_tag

        # Patrón para tags que pueden tener atributos en múltiples líneas
        # Usamos DOTALL para capturar saltos de línea dentro del tag
        pattern = rf'<{tag_escaped}[^>]*/>'

        result = re.sub(pattern, process_match, xml_content, flags=re.DOTALL)

        return result

        # # Ejemplo
        # xml = '''
        # <menuitem id="menu_misc" string="Misc" name='Misc'
        #          parent="main_menu_configuration" sequence='11' groups="byc_mcm.mcm_group_manager"/>
        # '''
        #
        # result = remove_attribute_from_tag(xml, 'menuitem', 'string')
        # print("Resultado:")
        # print(result)

def _get_patterns_allowed(lang: str):
    if lang == '.py':
        return 'python_patterns'
    elif lang == '.xml':
        return 'xml_patterns'
    elif lang == '.js':
        return 'js_patterns'
    elif lang in ['python_patterns', 'xml_patterns', 'js_patterns']:
        return lang
    return ''


