"""XML code transformer."""
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
    ATTR_MAPPING = {
        'invisible': 'invisible',
        'readonly': 'readonly',
        'required': 'required',
        'column_invisible': 'column_invisible',
        'states': 'invisible'
        #'optional': 'optional',
        #'widget': 'widget',
        #'class': 'class',
        #'placeholder': 'placeholder',
        #'confirm': 'confirm'
    }
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
                changes = []
                    # pattern = rule.get('pattern')
                    # replacement = rule.get('replacement')
                    # action = rule.get('action', 'replace')
                    # use_regex = rule.get('use_regex', False)

                # if rule.pattern and rule.action == ActionType.REPLACE:
                #    content, changes = self._apply_pattern_replacement(content, rule)
                if rule.action == ActionType.CHANGE_VIEW:
                    new_content, changes = rule.apply_upgrade_view(new_content)
                elif rule.action == ActionType.FORMAT_VIEW_17:
                    new_content, _ = self._transformar_tag_attribute(new_content)
                    new_content, _ = self._transformar_property_states_corregido(new_content)
                    new_content, _ = self._transformar_property_attrs_corregido(new_content)
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

    def _transformar_tag_attribute(self, texto: str) -> tuple:
        """Transforma <attribute name="attrs">...</attribute>"""
        transformados = []

        # Patrón que captura todo el contenido
        patron = re.compile(
            r'<attribute\s+name="attrs"\s*>\s*\n?'
            r'(.*?)'
            r'\s*</attribute>',
            re.DOTALL | re.MULTILINE
        )

        def procesar_tag(match):
            nonlocal transformados
            contenido = match.group(1).strip()

            # Extraer el diccionario interno
            dict_match = re.search(r'\{(.*)\}', contenido, re.DOTALL)
            if not dict_match:
                return match.group(0)

            dict_content = dict_match.group(1)

            # Parsear cada par key:value
            pares = self._parsear_todos_los_pares(dict_content)

            if not pares:
                return match.group(0)

            # Generar nuevos tags
            resultados = []
            for key, value in pares:
                if key in self.ATTR_MAPPING:
                    attr_name = self.ATTR_MAPPING[key]
                    value_clean = value.strip().rstrip(',')
                    nuevo_tag = f'<attribute name="{attr_name}">{value_clean}</attribute>'
                    resultados.append(nuevo_tag)
                    # self.transformaciones.append(f"  • tag: {key} → {attr_name}")
                    #transformados += 1

            if len(resultados) == 1:
                return resultados[0]
            elif len(resultados) > 1:
                return '\n'.join(resultados)

            return match.group(0)

        resultado = patron.sub(procesar_tag, texto)
        return resultado, transformados

    def _transformar_property_states_corregido(self, texto: str) -> tuple:
        transformados = []

        # Estrategia: Encontrar todo el bloque attrs y procesarlo
        # Buscar desde attrs=" hasta el cierre de llaves que corresponda
        patron_base = re.compile(
            r'states=\"'
        r'([^"]+)'
        r'\"',
            re.DOTALL | re.MULTILINE
        )

        def procesar_states_completo(match):
            nonlocal transformados
            contenido_completo = match.group(0)
            contenido_dict = match.group(1)

            # Parsear TODOS los pares key:value
            pares = self._parsear_todos_los_states(contenido_dict)

            if not pares:
                return contenido_completo

            # Construir nuevos atributos
            nuevos_atributos = []
            key = "states"
            attr_name = self.ATTR_MAPPING[key]
            for value in pares:
                # Limpiar el valor
                value_clean = self._limpiar_valor_profundo(value)
                nuevo_attr = f'{attr_name}="{value_clean}"'
                nuevos_atributos.append(nuevo_attr)
                # self.transformaciones.append(f"  • prop: {key} → {attr_name}")
                # transformados += 1

            if not nuevos_atributos:
                return contenido_completo

            # Mantener el formato original si es multilínea
            if '\n' in contenido_completo:
                # Preservar indentación aproximada
                indent = self._detectar_indentacion(contenido_completo)
                return ' '.join(nuevos_atributos)
            else:
                return ' '.join(nuevos_atributos)

        resultado = patron_base.sub(procesar_states_completo, texto)

        return resultado, transformados

    def _transformar_property_attrs_corregido(self, texto: str) ->tuple:
        """
        Transforma attrs="..." CORRIGIENDO el problema del tercer key
        Método robusto que captura TODOS los keys sin importar la complejidad
        """
        transformados = []

        # Estrategia: Encontrar todo el bloque attrs y procesarlo
        # Buscar desde attrs=" hasta el cierre de llaves que corresponda
        patron_base = re.compile(
            r'attrs=\"'  # attrs="
            r'\{'  # {
            r'([^}]*(?:\{[^}]*}[^}]*)*)'  # Contenido con posibles llaves anidadas
            r'}'  # }
            r'\"',  # "
            re.DOTALL | re.MULTILINE
        )

        def procesar_attrs_completo(match):
            nonlocal transformados
            contenido_completo = match.group(0)
            contenido_dict = match.group(1)

            # Parsear TODOS los pares key:value
            pares = self._parsear_todos_los_pares(contenido_dict)

            if not pares:
                return contenido_completo

            # Construir nuevos atributos
            nuevos_atributos = []

            for key, value in pares:
                if key in self.ATTR_MAPPING:
                    attr_name = self.ATTR_MAPPING[key]
                    # Limpiar el valor
                    value_clean = self._limpiar_valor_profundo(value)

                    nuevo_attr = f'{attr_name}="{value_clean}"'
                    nuevos_atributos.append(nuevo_attr)
                    # self.transformaciones.append(f"  • prop: {key} → {attr_name}")
                    # transformados += 1

            if not nuevos_atributos:
                return contenido_completo

            # Mantener el formato original si es multilínea
            if '\n' in contenido_completo:
                # Preservar indentación aproximada
                indent = self._detectar_indentacion(contenido_completo)
                return ' '.join(nuevos_atributos)
            else:
                return ' '.join(nuevos_atributos)

        resultado = patron_base.sub(procesar_attrs_completo, texto)
        return resultado, transformados

    def _parsear_todos_los_pares(self, texto: str) -> List[Tuple[str, str]]:
        """
        Parsea TODOS los pares key:value de un diccionario Odoo
        Maneja valores complejos como [False, None], listas anidadas, operadores
        """
        pares = []

        # Método: Buscar cada 'key': y luego encontrar su valor correspondiente
        # usando balance de corchetes y paréntesis

        i = 0
        largo = len(texto)

        while i < largo:
            # Buscar una key con comillas simples
            key_match = re.search(r"'(\w+)'\s*:\s*", texto[i:])
            if not key_match:
                break

            key = key_match.group(1)
            key_start = i + key_match.start()
            value_start = i + key_match.end()

            # Encontrar el valor completo
            value, next_pos = self._encontrar_valor_completo(texto, value_start)

            if value:
                pares.append((key, value))

            # Mover índice
            i = next_pos if next_pos > i else value_start + len(value) if value else key_start + len(key_match.group(0))

        # Si el método anterior falla, usar regex más flexible como respaldo
        if not pares:
            # Buscar patrones básicos
            patron_flexible = re.compile(
                r"'(\w+)':\s*"  # key
                r'('  # inicio valor
                r'(?:\[[^\]]*\]|'  # lista
                r'\([^\)]*\)|'  # tupla
                r'[^,}\n]+'  # valor simple
                r')'  # fin valor
                r')',  # cierre
                re.DOTALL
            )
            pares = patron_flexible.findall(texto)

        return pares

    def _parsear_todos_los_states(self, texto: str) -> List[str]:
        pares = []
        i = 0
        #largo = len(texto)
        state_opt = texto.strip().split(",")
        total = len(state_opt)
        if total == 1:
            for opt_state in state_opt:
                pares.append("state!='%s'" % opt_state)
        elif total > 1:
            opt_values = []
            for opt_state in state_opt:
                opt_values.append(opt_state)
            all_complete = "state not in [%s]" % ",".join("'%s'" % f for f in opt_values)
            pares.append(all_complete)
        # while i < largo:
        #     # Buscar una key con comillas simples
        #     key_match = re.search(r'(\w+)\s*', texto[i:])
        #     if not key_match:
        #         break
        #     key = key_match.group(1)
        #     key_start = i + key_match.start()
        #     value_start = i + key_match.end()

        return pares

    def _encontrar_valor_completo(self, texto: str, start_pos: int) -> Tuple[str, int]:
        """
        Encuentra el valor completo desde start_pos
        Maneja listas anidadas [], tuplas (), strings, etc.
        Retorna (valor, nueva_posicion)
        """
        if start_pos >= len(texto):
            return "", start_pos

        char = texto[start_pos]

        # Caso: valor es una lista [ ... ]
        if char == '[':
            return self._encontrar_cierre_balanceado(texto, start_pos, '[', ']')

        # Caso: valor es una tupla ( ... )
        elif char == '(':
            return self._encontrar_cierre_balanceado(texto, start_pos, '(', ')')

        # Caso: valor empieza con comilla
        elif char in ('"', "'"):
            quote_char = char
            end = texto.find(quote_char, start_pos + 1)
            if end == -1:
                return "", start_pos
            valor = texto[start_pos:end + 1]
            # Buscar la siguiente coma o cierre de diccionario
            next_pos = end + 1
            while next_pos < len(texto) and texto[next_pos] in ' \t\n\r':
                next_pos += 1
            if next_pos < len(texto) and texto[next_pos] == ',':
                next_pos += 1
            return valor, next_pos

        # Caso: valor simple (True, False, None, número, etc.)
        else:
            # Buscar hasta la próxima coma o cierre de diccionario
            end = start_pos
            balance = 0
            while end < len(texto):
                if texto[end] == ',' and balance == 0:
                    break
                if texto[end] in '[(':
                    balance += 1
                elif texto[end] in '])':
                    balance -= 1
                if balance < 0:
                    break
                end += 1

            valor = texto[start_pos:end].strip()

            # Avanzar después de la coma si existe
            next_pos = end
            while next_pos < len(texto) and texto[next_pos] in ' \t\n\r':
                next_pos += 1
            if next_pos < len(texto) and texto[next_pos] == ',':
                next_pos += 1

            return valor, next_pos

    def _encontrar_cierre_balanceado(self, texto: str, start: int, open_char: str, close_char: str) -> Tuple[str, int]:
        """Encuentra el cierre balanceado para corchetes o paréntesis"""
        balance = 0
        end = start

        for end in range(start, len(texto)):
            if texto[end] == open_char:
                balance += 1
            elif texto[end] == close_char:
                balance -= 1
                if balance == 0:
                    end += 1
                    break

        valor = texto[start:end].strip()

        # Buscar la coma después del valor
        next_pos = end
        while next_pos < len(texto) and texto[next_pos] in ' \t\n\r':
            next_pos += 1
        if next_pos < len(texto) and texto[next_pos] == ',':
            next_pos += 1

        return valor, next_pos

    def _limpiar_valor_profundo(self, valor: str) -> str:
        """Limpia el valor eliminando espacios extras y normalizando"""
        # Eliminar espacios al inicio y final
        valor = valor.strip()

        # Eliminar comas finales
        valor = re.sub(r',$', '', valor)

        # Normalizar espacios: múltiples espacios a uno solo
        valor = re.sub(r'\s+', ' ', valor)

        # Eliminar espacios alrededor de comas dentro de listas
        valor = re.sub(r',\s+', ', ', valor)

        return valor

    def _detectar_indentacion(self, texto: str) -> str:
        """Detecta la indentación usada"""
        match = re.search(r'\n(\s+)', texto)
        if match:
            return match.group(1)
        return ''
