from xomg_migration.migrations.transformers.python_transformer import PythonTransformer


def migrate_file_v140_v150(env, base_path, module_name=None) -> bool:

    return True

PythonTransformer.migrate_file_v140_v150 = migrate_file_v140_v150