"""XML code transformer."""
import os.path
import re
from enum import Enum
from typing import Dict, List, Any, Tuple

from xomg_migration.migrations.engine.migration_rule import MigrateRule, ActionType
from xomg_migration.migrations.transformers.base_transformer import BaseTransformer

try:
    from lxml import etree
    HAS_LXML = True
except ImportError:
    HAS_LXML = False


class OdooViewType(Enum):
    TREE_VIEW = "tree"
    REPORT_VIEW = "report"
    ACTION_VIEW = "act_window"
    FORM_VIEW = "form"


class XMLTransformer(BaseTransformer):
    """Transform XML files."""
    
    def transform(self, file_path: str, rules: List[MigrateRule]) -> List[Dict[str, Any]]:
        """Transform XML file according to rules."""
        stopped=False
        try:
            content = self._read_file(file_path)
            #file_name = os.path.basename(file_path)
            # print(file_name)
            all_changes = []
            new_content = content
            for rule in rules:
                if stopped:
                    continue
                if not rule.enabled:
                    continue

                    # pattern = rule.get('pattern')
                    # replacement = rule.get('replacement')
                    # action = rule.get('action', 'replace')
                    # use_regex = rule.get('use_regex', False)

                # if rule.pattern and rule.action == ActionType.REPLACE:
                #    content, changes = self._apply_pattern_replacement(content, rule)
                if rule.action == ActionType.CHANGE_VIEW:
                    new_content, changes = rule.apply_upgrade_view(new_content)
                else:
                    new_content, changes = rule.apply(new_content)
                all_changes.extend(changes)

            if (all_changes or new_content!=content) and not self.dry_run:
                self._write_file(file_path, new_content)
            #elif self.dry_run:
            #    print('\n****Mode dry-run: xml')
            
            return all_changes
        
        except Exception as e:
            return [{'error': str(e), 'file': file_path}]


    def migrate_view(self, content: str, rule: MigrateRule) -> tuple:
        view_type = rule.pattern
        changes = []
        if view_type == "migrate_report":
            content,changes = self.rpt_view_v130_v140(content)

        return content, changes

    @staticmethod
    def rpt_view_v130_v140(content:str)-> tuple:
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

            changes.append({
                'old_id': report_id,
                'new_id': report_id,
                'model': model,
                'old_format': match.group(0).strip(),
                'new_format': new_report.strip()
            })

            return new_report

        # Aplicar reemplazo

        result = re.sub(report_pattern, replace_report, content, flags=re.VERBOSE | re.DOTALL)

        return result, changes