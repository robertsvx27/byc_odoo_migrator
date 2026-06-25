SUPPORTED_VERSIONS = ['13.0', '14.0', '15.0', '16.0', '17.0', '18.0', '19.0']

_ALLOWED_EXTENSIONS = {".py", ".xml", ".js", ".csv", ".sql"}

_MANIFEST_NAMES = ["__openerp__.py", "__manifest__.py"]

_ROOT_FILES = ['migration_conf.yaml']

_DEFAULT_EXCLUDED_DIRS = {
    # Backups (los que genera el script)
    'backups', 'backup', '.backup', 'bak', '.bak',
    'backups_odoo_migration', 'backup_odoo',
    'migration_backup', 'manifest_backup',
    # Tests y ejemplos
    'tests', 'test', 'demo', 'example',
    # Migraciones
    'migrations', 'migration', 'scripts', 'tools', 'x_scripts',

    # Caché y control de versiones
    '__pycache__', '.git', '.hg', '.svn', '.idea', '.vscode',
    # Documentación
    'docs', 'documentation', 'doc', 'sphinx',

    # Imágenes y multimedia
    'images', 'img', 'fonts', 'icons', 'photos',

    # Directorios temporales
    'tmp', 'temp', 'cache', 'downloads',

    # Assets y librerías
    'node_modules', 'static', 'assets', 'lib', 'vendor',
    'examples', 'migrator', 'openupgrade',

    'pytest_cache', 'xomg', 'x_tasks',
    # Directorios de otros proyectos
    'venv', 'env', 'virtualenv', '.venv',
}

_DEFAULT_EXCLUDED_PATTERNS = {
    '*.bak', '*.backup', '*.orig', '*.rej',
    '*~', '*.swp', '*.tmp','*.pyc', '*.pyo', '.DS_Store',
        '*.log', '*.cache', '*.sql', '*.dump',
}
