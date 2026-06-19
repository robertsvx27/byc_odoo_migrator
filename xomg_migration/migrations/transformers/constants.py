


SUPPORTED_VERSIONS = ['13.0','14.0', '15.0', '16.0', '17.0', '18.0', '19.0']

_ALLOWED_EXTENSIONS = [".py", ".xml", ".js", ".csv", ".sql"]

_MANIFEST_NAMES = ["__openerp__.py", "__manifest__.py"]

_ROOT_FILES = ['migration_conf.yaml']

_DEFAULT_EXCLUDED_DIRS = [
    '__pycache__', '.git', '.hg', '.svn',
     'examples',
    'migrations', 'scripts', 'tools', 'x_scripts',
    'node_modules', 'static/lib', 'static/src/lib',
    '.DS_Store','pytest_cache','xomg','x_tasks'
]

_DEFAULT_EXCLUDED_PATTERNS = [
    '*.bak', '*.backup', '*.orig', '*.rej',
    '*~', '*.swp', '*.tmp'
]
