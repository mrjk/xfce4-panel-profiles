import importlib
import os
import sys


# Create custom module importer
def module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    sys.modules[module_name] = module
    return module


# Define paths
file = __name__.replace(".", os.path.sep) + os.path.sep + "__init__.py"
root_dir = __file__.replace(f"{file}", "")
src_dir = f"{root_dir}/xfce4-panel-profiles"
