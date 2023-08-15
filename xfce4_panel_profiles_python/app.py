import importlib.util

from xfce4_panel_profiles_python import module_from_file, src_dir


def run():
    "test"

    # Load dependencies
    info = module_from_file("info", f"{src_dir}/info.py")
    panelconfig = module_from_file("panelconfig", f"{src_dir}/panelconfig.py")

    # Wrap
    module_from_file("__main__", f"{src_dir}/xfce4-panel-profiles.py")


if __name__ == "__main__":
    run()
