import importlib.util
import os
import sys

from xfce4_panel_profiles_python import module_from_file, src_dir

# Import source files
info = module_from_file("info", f"{src_dir}/info.py")
panelconfig = module_from_file("panelconfig", f"{src_dir}/panelconfig.py")
xfce4_panel_profiles = module_from_file("xfp", f"{src_dir}/xfce4-panel-profiles.py")

# XfcePanelProfiles = xfce4_panel_profiles.XfcePanelProfiles
# PanelSaveDialog = xfce4_panel_profiles.PanelSaveDialog
# PanelConfirmDialog = xfce4_panel_profiles.PanelConfirmDialog
# PanelErrorDialog = xfce4_panel_profiles.PanelErrorDialog
