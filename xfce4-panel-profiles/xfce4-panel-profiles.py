#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#   Panel Profiles
#   Copyright (C) 2013 Alistair Buxton <a.j.buxton@gmail.com>
#   Copyright (C) 2015-2021 Sean Davis <bluesabre@xfce.org>
#
#   This program is free software: you can redistribute it and/or modify it
#   under the terms of the GNU General Public License version 3 or newer,
#   as published by the Free Software Foundation.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranties of
#   MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along
#   with this program.  If not, see <http://www.gnu.org/licenses/>.

import tarfile
from pprint import pprint

from locale import gettext as _

import logging
import shutil
import shlex
import os
import datetime

import warnings

import gi
gi.require_version('Gtk', '3.0')
# Try to import the new Libxfce4ui gir name (since 4.15.7)
# if it does not exists, try the old libxfce4ui
try:
  gi.require_version('Libxfce4ui', '2.0')
  from gi.repository import Libxfce4ui as libxfce4ui
  from gi.repository import Libxfce4util as libxfce4util
except ValueError:
  gi.require_version('libxfce4ui', '2.0')
  from gi.repository import libxfce4ui
  from gi.repository import libxfce4util

from gi.repository import Gtk, GLib, Gio

from panelconfig import PanelConfig

import info

warnings.filterwarnings("ignore")

logger = logging.getLogger("xfce4_panel_profiles")


class Recall(Exception):
    "Exception to ask a new try"

def path_to_tuple(path):
    directory = os.path.dirname(path)
    filename = os.path.basename(path)

    name, ext = os.path.splitext(filename)
    name, tar = os.path.splitext(name)
    if ext in [".gz", ".bz2"] and tar == ".tar":
        path = os.path.join(directory, filename)
        t = int(os.path.getmtime(path))
        return (path, name, int(t))

def path_to_name(path):
    directory = os.path.dirname(path)
    filename = os.path.basename(path)

    name, ext = os.path.splitext(filename)
    name, tar = os.path.splitext(name)
    if ext in [".gz", ".bz2"] and tar == ".tar":
        return name


class FileConfig():

    def __init__(self, path=None):

        if path:
            self.from_path(path)

    def from_path(self, path):

        directory = os.path.dirname(path)
        filename = os.path.basename(path)

        name, ext = os.path.splitext(filename)
        name, tar = os.path.splitext(name)

        if ext in [".gz", ".bz2"] and tar == ".tar":
            self.directory = directory
            self.filename = filename
            self.name = name
            self.ext = tar + ext
            #self.path = self.to_path()
        else:
            raise ValueError(f"Not a valid file extensions: {path}")

    def to_path(self):
        return os.path.join(self.directory, self.filename)


class XfcePanelProfilesApp:
    "Main app logic"



    def __init__(self):

        self.load_xfconf()

        self.xpp_conf = self.load_xpp_config()


                    
    def cli_save(self, filename):
        logger.info (f"Save: {filename}")
        PanelConfig.from_xfconf(xfconf).to_file(filename)


    def cli_restore(self):

        pconf = self.xpp_conf
        template = True
        filename = pconf.get("/template_config")
        if not source:
            filename = pconf.get("/current_config")
            template = False

        logger.info (f"Restore: {filename}")

        self.load_configuration(filename,
                template=template, 
                )


    def cli_load(self, filename=None, template=False):

        pconf = self.xpp_conf
        if not filename:
            if template:
                filename = pconf.get("/template_config")
                if filename:
                    logger.info (f"Load template: {filename}")
                else:
                    filename = pconf.get("/current_config")
                    logger.info (f"Load file instead of template : {filename}")

            else:
                filename = pconf.get("/current_config")
                logger.info (f"Load file: {filename}")


        

        self.load_configuration(filename,
                template=template, 
                )

                        # app.cli_load(sys.argv[2])


                        # remove_extra_panels=False, 
                        # remap_extra_panels=False,
                        # spread_panels=False,

                        # conf_file = conf_file or pconf.get("/current_config")
            # PanelConfig.from_file(
            #     conf_file,
            #     # remove_extra_panels=remove_extra_panels, 
            #     # remap_extra_panels=remap_extra_panels,
            #     # spread_panels=spread_panels,
            #     ).to_xfconf(xfconf)

                    # elif sys.argv[1] == 'template':

                    #     app.cli_load(sys.argv[2], template=True)


                        # conf_file = conf_file or pconf.get("/template_config") or pconf.get("/current_config")
                        # PanelConfig.from_file(
                        #     conf_file,
                        #     remove_extra_panels=True, 
                        #     remap_extra_panels=True,
                        #     spread_panels=True,
                        #     ).to_xfconf(xfconf)

             
    def load_xfconf(self):
        session_bus = Gio.BusType.SESSION
        cancellable = None
        connection = Gio.bus_get_sync(session_bus, cancellable)

        proxy_property = 0
        interface_properties_array = None
        destination = 'org.xfce.Xfconf'
        path = '/org/xfce/Xfconf'
        interface = destination

        self.xfconf = Gio.DBusProxy.new_sync(
            connection,
            proxy_property,
            interface_properties_array,
            destination,
            path,
            interface,
            cancellable)

    def save_xpp_config(self, conf):
        PanelConfig.rc_to_xfconf(self.xfconf, conf)

    def load_xpp_config(self):
        return PanelConfig.xfconf_to_rc(self.xfconf)


    def load_configuration(self, filename, template=False):

        # spread_panels = spread_panels or self.builder.get_object("spread_panels").get_active()
        # remap_extra_panels = remap_extra_panels or self.builder.get_object("remap_extra_panels").get_active()
        # remove_extra_panels = remove_extra_panels or self.builder.get_object("remove_extra_panels").get_active()
        
        if os.path.isfile(filename):

            # Keep last
            old_conf = self.load_xpp_config()
            old_file = old_conf.get("/current_config")

            # Load config
            if template:
                PanelConfig.from_file(
                    filename,
                    remove_extra_panels=True, 
                    remap_extra_panels=True,
                    spread_panels=True,
                ).to_xfconf(self.xfconf)
            else:
                PanelConfig.from_file(
                    filename,
                ).to_xfconf(self.xfconf)

            # Save config
            conf = {
                "/last_config": old_file,
                "/current_config": filename,

                "/template": False,
                "/template_config": "",
            }

            if template:
                conf["/template"] = True
                conf["/template_config"] = filename
            self.save_xpp_config(conf)



class XfcePanelProfiles(XfcePanelProfilesApp):

    '''XfcePanelProfiles application class.'''

    data_dir = "xfce4-panel-profiles"
    save_location = os.path.join(GLib.get_user_data_dir(), data_dir)

    def __init__(self, from_panel=False):
        '''Initialize the Panel Profiles application.

        If 'from_panel' is set to 'True' the application launches 'xfce4-panel
        --preferences' when the user closes this application.
        '''
        # Temporary fix: https://stackoverflow.com/a/44230815
        _ = libxfce4ui.TitledDialog()

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain('xfce4-panel-profiles')

        script_dir = os.path.dirname(os.path.abspath(__file__))
        glade_file = os.path.join(script_dir, "xfce4-panel-profiles.glade")
        self.builder.add_from_file(glade_file)
        self.builder.connect_signals(self)

        self.window = self.builder.get_object("xfpanel_switch_window")

        # Load config
        self.load_xfconf()
        


        modified_col = self.builder.get_object('modified_column')
        cell = Gtk.CellRendererText()
        modified_col.pack_start(cell, False)
        modified_col.set_cell_data_func(cell, self.cell_data_func_modified, 2)

        self.treeview = self.builder.get_object('saved_configurations')
        self.tree_model = self.treeview.get_model()
        self._update_treeview()


        # Update last config
        self._update_label_current_conf()


        # Sort by name, then sort by date so timestamp sort is alphabetical
        self.tree_model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
        self.tree_model.set_sort_column_id(2, Gtk.SortType.DESCENDING)

        if not os.path.exists(self.save_location):
            os.makedirs(self.save_location)

        self.from_panel = from_panel

        self.window.show()


    def load_configuration(self, filename, template=False):

        super().load_configuration(filename, template=template)
        self._update_label_current_conf()


    def _update_label_current_conf(self):
        suffix = ""
        xpp_conf = self.load_xpp_config()
        label_current_config = self.builder.get_object('label_current_config')
        was_template = xpp_conf.get("/template")
        if was_template:
            current_config = xpp_conf.get("/template_config")
            suffix = ' (as template)'
        else:
            current_config = xpp_conf.get("/current_config")

        fconf = FileConfig(current_config).name
        msg = 'Current configuration' + f": {fconf}" + suffix
        label_current_config.set_label(msg)


    def _update_treeview(self):
        self.tree_model.clear()
        for config in self.get_saved_configurations():
            self.tree_model.append(config)

    def _copy(self, src, dst):


        # Check for existing files
        cont = self.windows_confirm_override(dst)
        if not cont:
            raise Recall(f"User refused override of file: {dst}")

        try:
            PanelConfig.from_file(
                src
                ).to_file(dst)

        except Exception as err:
            # dialog2 = PanelInfoDialog(self.window, message=str(err))
            # dialog2.run()
            # dialog2.destroy()
            # dialog.destroy()
            raise Recall(f"An error occured while trying to copy file: {err}")


            # message = str(err)
            # errordlg = Gtk.MessageDialog(
            #     transient_for=self.window, modal=True,
            #     message_type=Gtk.MessageType.ERROR,
            #     text=message)

            # errordlg.add_button(_("OK"), Gtk.ResponseType.OK)


    def _filedlg(self, title, action, default_name=None):
        if action == Gtk.FileChooserAction.SAVE:
            button = _("Save")
        else:
            button = _("Open")
        dialog = Gtk.FileChooserDialog(title=title,
                                       transient_for=self.window,
                                       action=action)
        dialog.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            button, Gtk.ResponseType.ACCEPT
        )
        dialog.set_default_response(Gtk.ResponseType.ACCEPT)
        

        if default_name:
            if os.path.isdir(default_name):
                dialog.set_current_folder(default_name)
            else:
                base_dir = os.path.dirname(default_name)
                if os.path.isdir(base_dir):
                    basename = os.path.basename(default_name)

                    dialog.set_current_folder(base_dir)
                    dialog.set_current_name(basename)
                else:
                    dialog.set_current_name(default_name)

        return dialog



    def get_data_dirs(self):
        dirs = []
        for directory in GLib.get_system_data_dirs():
            path = os.path.join(directory, self.data_dir)
            if os.path.isdir(path):
                dirs.append(path)
                path = os.path.join(path, "layouts")
                if os.path.isdir(path):
                    dirs.append(path)
        path = os.path.join(GLib.get_user_data_dir(), self.data_dir)
        if os.path.isdir(path):
            dirs.append(path)
        return list(set(dirs))

    def get_saved_configurations(self):
        now = int(datetime.datetime.now().strftime('%s'))

        results = [('', _('Current Configuration'), now)]
        for directory in self.get_data_dirs():
            for filename in os.listdir(directory):
                name, ext = os.path.splitext(filename)
                name, tar = os.path.splitext(name)
                if ext in [".gz", ".bz2"] and tar == ".tar":
                    path = os.path.join(directory, filename)
                    t = int(os.path.getmtime(path))
                    results.append((path, name, int(t)))

        return results

    def cell_data_func_modified(self, column, cell_renderer,
                                tree_model, tree_iter, id):
        today_delta = datetime.datetime.today() - datetime.timedelta(days=1)
        t = tree_model.get_value(tree_iter, id)
        datetime_o = datetime.datetime.fromtimestamp(t)
        if datetime_o > today_delta:
            modified = _("Today")
        elif datetime_o == today_delta:
            modified = _("Yesterday")
        else:
            modified = datetime_o.strftime("%x")
        cell_renderer.set_property('text', modified)
        return

    def get_selected(self):
        model, treeiter = self.treeview.get_selection().get_selected()
        
        if not model or not treeiter:
            return None

        values = model[treeiter][:]
        return (model, treeiter, values)

    def get_selected_filename(self):
        # selection = self.get_selected()

        # if not isinstance(selection, list):
        #     return None

        try:
            values = self.get_selected()[2]
        except TypeError:
            return

        filename = values[0]
        return filename

    def copy_configuration(self, row, name, append=True):
        values = row[2]
        filename = values[0]
        created = values[2]
        new_filename = name + ".tar.bz2"
        new_filename = os.path.join(self.save_location, new_filename)

        self._copy(filename, new_filename)
        if append:
            self.tree_model.append([new_filename, name, created])

    def save_configuration(self, name, append=True):
        filename = name + ".tar.bz2"
        filename = os.path.join(self.save_location, filename)

        # Check for existing files
        cont = self.windows_confirm_override(filename)
        if not cont:
            raise Recall(f"User refused override of file: {filename}")

        pc = PanelConfig.from_xfconf(self.xfconf)
        if pc.has_errors():
            dialog = PanelErrorDialog(self.window, pc.errors)
            accept = dialog.run()
            dialog.destroy()
            if accept != Gtk.ResponseType.ACCEPT:
                raise Recall(f"An error occured while saving file: {filename}")
        pc.to_file(filename)
        created = int(datetime.datetime.now().strftime('%s'))
        if append:
            self.tree_model.append([filename, name, created])

    # def make_name_unique(self, name):
    #     iter = self.tree_model.get_iter_first()
    #     while iter != None:
    #         if self.tree_model.get_value(iter, 1) == name:
    #             date = datetime.datetime.now().strftime("%x_%X")
    #             date = date.replace(":", "-").replace("/", "-")
    #             return name + '_' + date
    #         iter = self.tree_model.iter_next(iter)
    #     return name



    def delete_configuration(self, filename):
        if os.path.isfile(filename):
            os.remove(filename)



    # Top toolbar actions
    # ===================


    def on_save_clicked(self, widget):
        filename = self.get_selected_filename()

        if filename:
            filec = FileConfig(filename)
            filename = filec.name + " - Copy"
        else:
            filename = None

        name = self.windows_save_dialog(default=filename)

        # dialog = PanelSaveDialog(self.window, default=filename)

        if name:
        # if dialog.run() == Gtk.ResponseType.ACCEPT:
            # name = dialog.get_save_name()
            # if len(name) > 0:

            row = self.get_selected()

            if filename == "" or row is None: # Current configuration.
                name = self.make_name_unique(name)
                self.save_configuration(name)
            else:
                
                old_name = row[2][1]
                name = self.make_name_unique(_("%s (Copy of %s)") % (name, old_name))
                #name = _("%s (Copy of %s)") % (name, old_name)
                self.copy_configuration(row, name)

        # dialog.destroy()


    def on_import_clicked(self, widget):
        recall = True

        selected = self.get_selected_filename() or ""
        if selected:
            selpath = FileConfig(selected).directory
        else:
            selpath = None



        dialog = self._filedlg(_("Import configuration file..."),
                               Gtk.FileChooserAction.OPEN, selpath)
        response = dialog.run()

        while recall == True:


            if response != Gtk.ResponseType.ACCEPT:
                recall = False
            else:
                filename = dialog.get_filename()

                # VAlidate file type
                dname = None
                try:
                    dname = FileConfig(filename).name
                    if dname is None:
                        recall = False

                except ValueError as err:
                    # dialog2 = PanelInfoDialog(self.window, message=str(err))
                    # dialog2.run()
                    # dialog2.destroy()
                    # dialog.destroy()


                    message = str(err)
                    errordlg = Gtk.MessageDialog(
                        transient_for=self.window, modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        text=message)

                    errordlg.add_button(_("OK"), Gtk.ResponseType.OK)

                    errordlg.run()
                    errordlg.destroy()
                    

                    # self.on_import_clicked(widget)
                    # return

                if dname:                    
                    name = self.windows_save_dialog(default=dname)
                    if not name:
                        recall = False
                    else:
                        
                        # savedlg = PanelSaveDialog(self.window, default=dname)

                    # if savedlg.run() == Gtk.ResponseType.ACCEPT:
                        # name = self.make_name_unique(savedlg.get_save_name())
                        # name = self.make_name_unique(name)
                        dst = os.path.join(self.save_location, name + ".tar.bz2")
                        try:
                            self._copy(filename, dst)
                            self.tree_model.append(
                                [dst, name, int(datetime.datetime.now().strftime('%s'))])

                            recall = False
                        except tarfile.ReadError:
                            message = _("Invalid configuration file!\n"
                                        "Please select a valid configuration file.")

                            errordlg = Gtk.MessageDialog(
                                transient_for=self.window, modal=True,
                                message_type=Gtk.MessageType.ERROR,
                                text=message)

                            errordlg.add_button(_("OK"), Gtk.ResponseType.OK)

                            errordlg.run()
                            errordlg.destroy()
                            recall=True
                        except Recall:
                            recall = True

            # savedlg.destroy()
        dialog.destroy()





    # COnfiguration toolbar actions
    # ===================

    def on_apply_clicked(self, widget, template=False):
        filename = self.get_selected_filename()
        if not filename:
            return

        # Confirm panel
        dialog = PanelConfirmDialog(self.window)
        ans = dialog.run()
        do_backup = dialog.backup.get_active()
        dialog.destroy()

        if ans == Gtk.ResponseType.ACCEPT:

            if do_backup:
                self.on_save_clicked(widget)

            self.load_configuration(filename,
                template=template, 
                )
    

    def on_apply_template_clicked(self, widget):
        self.on_apply_clicked(widget, template=True)




    def windows_confirm_override(self, dst_path):
        ret = True
        if os.path.exists(dst_path):
            msg = f"Do you want to override file '{dst_path}'?"
            dialog2 = PanelConfirmContinueDialog(self.window, message=msg)
            if dialog2.run() != Gtk.ResponseType.ACCEPT:
                ret = False
            dialog2.destroy()
        return ret

    def windows_save_dialog(self, default=None):

        dialog = PanelSaveDialog(self.window, default=default)
        resp = dialog.run()
        ret = None
        if resp == Gtk.ResponseType.ACCEPT:
            dest_name = dialog.get_save_name()
            ret = dest_name
        
        # Quit menu
        dialog.destroy()
        return ret
        


    def _cp_mv(self, widget, action, path, dest_name=None, dest_dir=None):

        assert action in ["cp", "mv"]
        recall = False
        src = FileConfig(path)

        # Build destination name
        nname = dest_name
        if not dest_name:
            nname = src.name
            if action == "cp":
                nname = nname + " - Copy"

        # Ask name destination
        dest_name = self.windows_save_dialog(default=nname)
        if not dest_name:
            return
        # dialog = PanelSaveDialog(self.window, default=nname)
        # resp = dialog.run()
        # if resp == Gtk.ResponseType.ACCEPT:
        #     dest_name = dialog.get_save_name()
        # else:
        #     # Quit menu
        #     dialog.destroy()
        #     return


        # Build destination
        target = FileConfig(dest_name + ".tar.bz2")
        target.directory = self.save_location

        if len(target.name) > 0:

            src_path = src.to_path()
            dst_path = target.to_path()

            if src_path == dst_path:
                msg = f"Please choose a different name"
                dialog2 = PanelInfoDialog(self.window, message=msg, message_type=Gtk.MessageType.ERROR)
                if dialog2.run() == Gtk.ResponseType.ACCEPT:
                    recall = True

                dialog2.destroy()

            else:

                confirmed = self.windows_confirm_override(dst_path)

                # confirmed = True
                # if os.path.exists(dst_path):
                #     confirmed = False
                #     msg = f"Do you want to override file '{dst_path}'?"
                #     dialog2 = PanelConfirmContinueDialog(self.window, message=msg)
                #     if dialog2.run() == Gtk.ResponseType.ACCEPT:
                #         confirmed = True
                #     dialog2.destroy()

                if confirmed is True:
                    
                    if action == "mv":
                        logger.info (f"Move {src_path} to {dst_path}")
                        shutil.move(src_path, dst_path)
                    else:
                        logger.info (f"Copy {src_path} to {dst_path}")
                        shutil.copy(src_path, dst_path)

                    self._update_treeview()
                else:
                    recall = True

        # dialog.destroy()

        if recall:
            self._cp_mv(widget, action, path, dest_name=target.name, dest_dir=dest_dir)


    def on_copy_clicked(self, widget, last_entry=None):
        
        filename = self.get_selected_filename()
        self._cp_mv(widget,"cp", filename, dest_dir=None)


    def on_rename_clicked(self, widget, last_entry=None):

        filename = self.get_selected_filename()
        self._cp_mv(widget, "mv", filename, dest_dir=None)



    def on_delete_clicked(self, widget):
        model, treeiter, values = self.get_selected()
        filename = values[0]
        if filename == "": # Current configuration.
            return
        self.delete_configuration(filename)
        model.remove(treeiter)



    def on_export_clicked(self, widget):
        recall = True

        selected = self.get_selected_filename() or None
        if selected:
            selpath = FileConfig(selected).to_path()
        else:
            selpath = "Current config"

        dialog = self._filedlg(_("Export configuration as..."),
                               Gtk.FileChooserAction.SAVE, selpath)

        while recall == True:
            response = dialog.run()
            if response == Gtk.ResponseType.ACCEPT:
                filename = dialog.get_filename()
                try:
                    if selected == "": # Current configuration.
                        self.save_configuration(filename, False)
                    else:
                        self.copy_configuration(self.get_selected(), filename, False)

                    recall = False
                except Recall as err:
                    message = str(err)
                    errordlg = Gtk.MessageDialog(
                        transient_for=self.window, modal=True,
                        message_type=Gtk.MessageType.ERROR,
                        text=message)

                    errordlg.add_button(_("OK"), Gtk.ResponseType.OK)

                    errordlg.run()
                    errordlg.destroy()
                    # continue
            else:
                recall = False

        dialog.destroy()








    def on_saved_configurations_cursor_changed(self, widget):
        filename = self.get_selected_filename()

        sensitive = False
        if filename is not None:
            sensitive = True if os.access(filename, os.W_OK) else False

        delete = self.builder.get_object('toolbar_delete')
        delete.set_sensitive(sensitive)
        rename = self.builder.get_object('toolbar_rename')
        rename.set_sensitive(sensitive)

        # Current configuration cannot be applied.
        apply = self.builder.get_object('toolbar_apply')
        apply.set_sensitive(True if filename else False)


    def on_saved_configurations_cursor_double_click(self, widget, path, column):
        self.on_apply_clicked(widget)



    def on_window_destroy(self, *args):
        self.on_close_clicked(args)

    def on_close_clicked(self, *args):
        '''
        Exit the application when the window is closed. Optionally launch
        'xfce4-panel --preferences' if the application is launched with
        '--from-profile' option.
        '''
        if self.from_panel:
            path = GLib.find_program_in_path('xfce4-panel')

            if path != None:
                GLib.spawn_command_line_async(path + ' --preferences')

        Gtk.main_quit()

    def on_help_clicked(self, *args):
        '''Shows Xfce's standard help dialog.'''
        libxfce4ui.dialog_show_help(parent=self.window,
                                    component='xfce4-panel-profiles',
                                    page='xfce4-panel-profiles',
                                    offset=None)


















    # def windows_confirm_override(self, dst_path=None):
    #     ret = True
    #     if os.path.exists(dst_path):
    #         msg = f"Do you want to override file '{dst_path}'?"
    #         dialog2 = PanelConfirmContinueDialog(self.window, message=msg)
    #         if dialog2.run() != Gtk.ResponseType.ACCEPT:
    #             ret = False
    #         dialog2.destroy()
    #     return ret



    # def windows_save_dialog(self, default=None):

    #     dialog = PanelSaveDialog(self.window, default=default)
    #     resp = dialog.run()
    #     ret = None
    #     if resp == Gtk.ResponseType.ACCEPT:
    #         dest_name = dialog.get_save_name()
    #         ret = dest_name
        
    #     # Quit menu
    #     dialog.destroy()
    #     return ret
        







class PanelSaveDialog(Gtk.MessageDialog):

    def __init__(self, parent=None, default=None, extra_opt=None):
        primary = _("Name the new panel configuration")
        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=primary)
        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Save Configuration"), Gtk.ResponseType.ACCEPT
        )
        self.set_default_icon_name("document-save-as")
        self.set_default_response(Gtk.ResponseType.ACCEPT)
        box = self.get_message_area()
        self.entry = Gtk.Entry.new()
        self.entry.set_activates_default(True)
        if default:
            self.entry.set_text(default)
        else:
            self.default()
        box.pack_start(self.entry, True, True, 0)

        self.extra = None
        if extra_opt:
            self.extra = Gtk.CheckButton.new()
            self.extra.set_label(extra_opt)
            box.pack_start(self.extra, True, True, 0)

        box.show_all()

    def default(self):
        date = datetime.datetime.now().strftime("%x %X")
        date = date.replace(":", "-").replace("/", "-").replace(" ", "_")
        name = _("Backup_%s") % date
        self.set_save_name(name)

    def get_save_name(self):
        return self.entry.get_text().strip()

    def set_save_name(self, name):
        self.entry.set_text(name.strip())


class PanelConfirmContinueDialog(Gtk.MessageDialog):
    '''Ask to the user if he wants to override existing configuration'''

    def __init__(self, parent=None, message=None):
        message = message or _("Do you want to continue ?")

        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=message)

        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Continue"), Gtk.ResponseType.ACCEPT
        )

        self.set_default_icon_name("dialog-information")
        self.set_default_response(Gtk.ResponseType.CANCEL)

        box = self.get_message_area()
        box.show_all()


class PanelInfoDialog(Gtk.MessageDialog):
    '''Simple dialog box for notifications'''

    def __init__(self, parent=None, message=None, message_type=None):
        message = message or _("Info message")
        message_type = message_type or Gtk.MessageType.QUESTION

        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=message_type,
            text=message)

        self.add_buttons(
            _("OK"), Gtk.ResponseType.ACCEPT
        )

        self.set_default_icon_name("dialog-information")
        self.set_default_response(Gtk.ResponseType.ACCEPT)

        box = self.get_message_area()
        box.show_all()




class PanelConfirmDialog(Gtk.MessageDialog):
    '''Ask to the user if he wants to apply a configuration, because the current
    configuration will be lost.'''

    def __init__(self, parent=None):
        message = _("Do you want to apply this configuration?\n"
                    " The current configuration will be lost!")

        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=message)

        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Apply Configuration"), Gtk.ResponseType.ACCEPT
        )

        self.set_default_icon_name("dialog-information")
        self.set_default_response(Gtk.ResponseType.ACCEPT)

        self.backup = Gtk.CheckButton.new()
        self.backup.set_label(_("Make a backup of the current configuration"))

        box = self.get_message_area()
        box.pack_start(self.backup, True, True, 0)
        box.show_all()

class PanelErrorDialog(Gtk.MessageDialog):
    '''Ask the user if he wants to apply a configuration, because the current
    configuration will be lost.'''

    def __init__(self, parent=None, messages=[]):
        message = _("Errors occured while parsing the current configuration.")

        Gtk.MessageDialog.__init__(
            self, transient_for=parent, modal=True,
            message_type=Gtk.MessageType.QUESTION,
            text=message)

        self.add_buttons(
            _("Cancel"), Gtk.ResponseType.CANCEL,
            _("Save"), Gtk.ResponseType.ACCEPT
        )

        self.set_default_icon_name("dialog-information")
        self.set_default_response(Gtk.ResponseType.ACCEPT)

        box = self.get_message_area()
        for line in messages:
            label = Gtk.Label.new(line)
            box.pack_start(label, True, True, 0)

        label = Gtk.Label.new(_("Do you want to save despite the errors? "
                                "Some configuration information could be missing."))
        box.pack_start(label, True, True, 0)

        box.show_all()

if __name__ == "__main__":
    from_panel = False

    import sys

    libxfce4util.textdomain('xfce4-panel-profiles',
                            os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../locale'),
                            'UTF-8')

    session_bus = Gio.BusType.SESSION
    cancellable = None
    connection = Gio.bus_get_sync(session_bus, cancellable)

    proxy_property = 0
    interface_properties_array = None
    destination = 'org.xfce.Xfconf'
    path = '/org/xfce/Xfconf'
    interface = destination

    xfconf = Gio.DBusProxy.new_sync(
        connection,
        proxy_property,
        interface_properties_array,
        destination,
        path,
        interface,
        cancellable)


    logging.basicConfig( level="DEBUG")

    
    if len(sys.argv) > 1:

        if sys.argv[1] in ['save', 'load', 'template', 'restore']:

            app = XfcePanelProfilesApp()

            try:
                if sys.argv[1] == 'save':
                    # PanelConfig.from_xfconf(xfconf).to_file()

                    app.cli_save(sys.argv[2])

                # elif sys.argv[1] == 'restore':
                #     conf_file = conf_file or pconf.get("/template_config") or pconf.get("/last_config")
                #     PanelConfig.from_xfconf(xfconf).to_file(conf_file)

                else:

                    conf_file = None
                    if len(sys.argv) > 2:
                        conf_file = sys.argv[2]
                    # else:
                    #     pconf = self.load_xpp_config()
                        

                    if sys.argv[1] == 'load':

                        app.cli_load(conf_file)


                        # remove_extra_panels=False, 
                        # remap_extra_panels=False,
                        # spread_panels=False,

                        # conf_file = conf_file or pconf.get("/current_config")
                        # PanelConfig.from_file(
                        #     conf_file,
                        #     # remove_extra_panels=remove_extra_panels, 
                        #     # remap_extra_panels=remap_extra_panels,
                        #     # spread_panels=spread_panels,
                        #     ).to_xfconf(xfconf)

                    elif sys.argv[1] == 'template':

                        app.cli_load(conf_file, template=True)


                        # conf_file = conf_file or pconf.get("/template_config") or pconf.get("/current_config")
                        # PanelConfig.from_file(
                        #     conf_file,
                        #     remove_extra_panels=True, 
                        #     remap_extra_panels=True,
                        #     spread_panels=True,
                        #     ).to_xfconf(xfconf)


            except Exception as e:
                print(repr(e))
                exit(1)
            exit(0)
        elif sys.argv[1] == '--version':
            print(info.appname + ' ' + info.version)
            exit(0)
        elif sys.argv[1] == '--from-panel':
            from_panel = True
        else:
            print('Xfce Panel Profiles - Usage:')
            print(info.appname + ' : load graphical user interface.')
            print(info.appname + ' save <filename> : save current configuration.')
            print(info.appname + ' load [<filename>] : load configuration from file.')
            print(info.appname + ' template [<filename>] : load configuration from template file.')
            print('')
            exit(-1)

    main = XfcePanelProfiles(from_panel)

    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
