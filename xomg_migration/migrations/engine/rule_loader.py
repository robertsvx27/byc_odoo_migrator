from enum import Enum


class ActionType(Enum):
    REPLACE = "replace"
    DELETE = "delete"
    INSERT = "insert"
    COMMENT = "comment"
    DELETE_CLASS = "delete_class"
    RENAME_FIELD = "rename_field"
    DELETE_FIELD = "delete_field"
    CHANGE_VIEW = "change_view"

class FileType(Enum):
    PYTHON = ".py"
    XML = ".xml"
    VIEW = "_view.xml"
    MODEL = ".py"
    SECURITY = "_security.xml"
    DATA = "_data.xml"


fields_rules = ['pattern','description','replacement','action', 'enabled','use_regex']

class MigrationRule:
    """Report of migration changes."""

    def __init__(self, **kwargs):
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
