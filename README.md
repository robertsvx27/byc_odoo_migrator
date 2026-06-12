# BYC Odoo Migrator

Framework automático para migrar módulos personalizados de Odoo entre versiones.

## 📋 Descripción

Este framework automatiza la migración de módulos personalizados de Odoo desde la versión 14.0 hasta 19.0, siguiendo el flujo de 4 fases:

1. **Fase 1**: Migrar addons estándar (oficial Odoo)
2. **Fase 2**: Migrar módulos OCA (OpenUpgrade)
3. **Fase 3**: Migrar módulos personalizados (byc_odoo_migrator)
4. **Fase 4**: Revisión y optimización manual

## 🚀 Características

- ✅ Motor de migración automático
- ✅ Transformadores para Python, XML y JavaScript
- ✅ Reglas configurables en YAML
- ✅ Soporte para versiones 14.0 → 19.0
- ✅ Reportes detallados de cambios
- ✅ Auto-detección de versiones
- ✅ Sistema de validación

## 📁 Estructura del Proyecto
byc_odoo_migrator/ ├── migrations/ │ ├── engine/ # Motor principal │ ├── transformers/ # Transformadores de código │ └── rules/ # Reglas YAML por versión ├── config/ # Configuración ├── examples/ # Ejemplos ├── tests/ # Tests unitarios └── .github/ └── workflows/ # GitHub Actions CI/CD


## 🛠️ Instalación

```bash
git clone https://github.com/robertsvx27/byc_odoo_migrator.git
cd byc_odoo_migrator
pip install -r requirements.txt

```
from migrations.engine.migration_engine import OdooMigrationEngine

# Inicializar el motor
engine = OdooMigrationEngine(
    config_file='config/odoo_migration.yaml',
    target_version='19.0'
)

# Migrar un módulo
report = engine.migrate_module(
    module_path='/ruta/a/modulo_custom',
    from_version='14.0',
    to_version='19.0'
)

print(report.to_dict())


