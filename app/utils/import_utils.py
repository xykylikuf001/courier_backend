from importlib import import_module


def import_string(dotted_path):
    """
    Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import failed.
    """
    try:
        module_path, class_name = dotted_path.rsplit('.', 1)
    except ValueError as err:
        raise ImportError("%s doesn't look like a module path" % dotted_path) from err

    module = import_module(module_path)

    try:
        return getattr(module, class_name)
    except AttributeError as err:
        raise ImportError('Module "%s" does not define a "%s" attribute/class' % (
            module_path, class_name)
                          ) from err


def perform_import(value, setting_name):
    if isinstance(value, str):
        return import_from_string(value, setting_name)
    if isinstance(value, (list, tuple)):
        return [import_from_string(item, setting_name) for item in value]
    return value


def import_from_string(value, setting_name):
    try:
        return import_string(value)
    except ImportError as e:
        msg = 'Could not import `{}` for setting `{}`. {}: {}.'.format(
            value, setting_name, e.__class__.__name__, e,
        )
        raise ImportError(msg)
