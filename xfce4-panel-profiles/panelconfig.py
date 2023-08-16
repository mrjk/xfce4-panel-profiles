#!/usr/bin/env python3
# * Configuration switcher for xfce4-panel
# *
# * Copyright 2013 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

from pprint import pprint

import gi
gi.require_version('Gdk', '3.0')


from gi.repository import Gio, GLib, Gdk, GdkX11
import tarfile
import io
import time
import os
import psutil

# yes, python 3.2 has exist_ok, but it will still fail if the mode is different

config_dir = os.path.join(GLib.get_user_config_dir(), 'xfce4/panel/')

def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)
    except FileExistsError:
        pass


def add_to_tar(t, bytes, arcname):
    ti = tarfile.TarInfo(name=arcname)
    ti.size = len(bytes)
    ti.mtime = time.time()
    f = io.BytesIO(bytes)
    t.addfile(ti, fileobj=f)



def get_monitor_config():
    "Return the current dicplay configuration"

    display = Gdk.Display.get_default()

    # Get screens
    # screen_count = display.get_n_screens()
    # ret_screens = []
    # for m in range(screen_count):
    #     tmp = display.get_screen(m)
    #     ret_screens.append(tmp)

    # Get monitors
    monitor_count = display.get_n_monitors()
    ret_monitors = {}
    monitor_primary = []
    monitors_gtk_order = []
    for mon in range(monitor_count):
        monitor = Gdk.Display.get_monitor(display, mon)

        # Get monitor info
        device = monitor.get_model()
        primary = monitor.is_primary()
        pos = GdkX11.X11Monitor.get_geometry(monitor)
        area = GdkX11.X11Monitor.get_workarea(monitor)

        # Process data
        order_score = (area.x + 1 ) * (area.y + 1 )
        if primary:
            monitor_primary.append(device)
        monitors_gtk_order.append(device)

        ret_monitors[device] = {
            "monitor_number": mon,

            "manufacturer": monitor.get_manufacturer(),
            "device": device,
            "primary": primary,

            "pos_x": pos.x,            
            "pos_y": pos.y,
            "pos_width": pos.width,
            "pos_height": pos.height,

            "area_x": area.x,            
            "area_y": area.y,
            "area_width": area.width,
            "area_height": area.height,

            "area": f"{area.width}x{area.height}+{area.x}+{area.y}",
            "pos": f"{pos.width}x{pos.height}+{pos.x}+{pos.y}",

            "output": GdkX11.X11Monitor.get_output(monitor),

            "order_score": order_score,
        }

    # Get primary monitor
    assert len(monitor_primary) <= 1, f"Too many primary monitors: {monitor_primary}"
    monitor_primary = monitor_primary[0] if monitor_primary else None


    # Generate monitor order
    monitors_primary_order = []
    monitors_natural_order = []
    if monitor_primary:
        monitors_primary_order.append(monitor_primary)

    for key in (sorted(ret_monitors, key=lambda key: ret_monitors[key].get("order_score"))):
        name = ret_monitors[key]["device"]
        if not name in monitors_primary_order:
            monitors_primary_order.append(name)

        monitors_natural_order.append(name)

            
    ret = {
        "monitor_count": monitor_count,
        "monitor_primary_order": monitors_primary_order,
        "monitor_natural_order": monitors_natural_order,
        "monitor_gtk_order": monitors_gtk_order,
        "monitor_primary": monitor_primary,
        "monitors": ret_monitors,
    }
    return ret



class PanelConfig(object):

    def __init__(self):
        self.desktops = []
        self.properties = {}
        self.rc_files = []
        self.source = None
        self.errors = []

    @classmethod
    def from_xfconf(cls, xfconf):
        pc = PanelConfig()

        result = xfconf.call_sync(
            'GetAllProperties',
            GLib.Variant('(ss)', ('xfce4-panel', '')), 0, -1, None)

        props = result.get_child_value(0)

        for n in range(props.n_children()):
            p = props.get_child_value(n)
            pp = p.get_child_value(0).get_string()
            pv = p.get_child_value(1).get_variant()

            pn = GLib.Variant.parse(None, str(pv), None, None)
            assert(pv == pn)

            pc.properties[pp] = pv

        pc.remove_orphans()
        pc.find_desktops()
        pc.find_rc_files()

        return pc

    @classmethod
    def from_file(cls, filename, remove_extra_panels=False, remap_extra_panels=False, spread_panels=False):
        pc = PanelConfig()

        pc.source = tarfile.open(filename, mode='r')
        config = pc.source.extractfile('config.txt')

        for line in config:
            try:
                x = line.decode('utf-8').strip().split(' ', 1)
                pc.properties[x[0]] = GLib.Variant.parse(None, x[1], None, None)
            except:
                pass

        pc.remove_orphans()
        pc.find_desktops()
        pc.find_rc_files()

        # New
        pc.remap_screens(remove_extra_panels=remove_extra_panels, remap_extra_panels=remap_extra_panels, spread_panels=spread_panels)

        return pc

    def source_not_file(self):
        return getattr(self, 'source', None) is None


    def remap_screens(self, remove_extra_panels=True, remap_extra_panels=True, spread_panels=False):

        if not remap_extra_panels and not remove_extra_panels and not spread_panels:
            return

        # Fetch monitors config
        screen_config = get_monitor_config()
        monitor_primary_order = screen_config["monitor_primary_order"]
        primary_mon = screen_config["monitor_primary"]

        # Fetch panel config
        panel_config_orig = {}
        panel_index = 1
        for pp in sorted(self.properties):
            pv = self.properties[pp]
            path = pp.split('/')
            # pprint (path)
            if len(path) == 4 and path[0] == '' and path[1] == 'panels' and \
                    path[2].startswith('panel-') and path[3] == 'output-name':
                
                screen_req = pv.get_string()
                panel_number = path[2].replace('panel-', "")
                panel_config_orig[panel_number] = screen_req



        # Find incoherent configuration
        used_screens = {}
        missing_screens = {}
        screen_spread = {}

        for panel_number, screen_name in sorted(panel_config_orig.items()):

            real_name = screen_name
            if screen_name == "Primary":
                if primary_mon:
                    real_name = primary_mon

            if real_name in monitor_primary_order:
                used_screens[panel_number] = real_name

                if not real_name in screen_spread:
                    screen_spread[real_name] = []
                screen_spread[real_name].append(panel_number)

            else:
                missing_screens[panel_number] = real_name


        # Prepare new configuration
        panel_config_new = dict(panel_config_orig)
        panels_to_remove = []
        unused_screens = [ screen for screen in monitor_primary_order if screen not in used_screens.values()]

        spread_panels = True

        if spread_panels:

            index = 0
            for screen_name, panels in screen_spread.items():
                if len(panels) > 1:
                    print ("Unspreaded panel", panels, "on", screen_name)


                    for panel in panels[1:]:
                        if 0 <= index < len(unused_screens):
                            if remap_extra_panels:
                                available_screen = unused_screens[index]
                                panel_config_new[panel_number] = available_screen
                                used_screens[panel_number] = available_screen
                                del unused_screens[index]
                        else:
                            if remove_extra_panels:
                                print ("Remove unspread panel", panel_number)
                                panels_to_remove.append(f"/panels/panel-{panel_number}")
                                del panel_config_new[panel_number]


        if missing_screens:

            index = 0
            for panel_number in sorted(missing_screens):
                
                if 0 <= index < len(unused_screens):
                    if remap_extra_panels:
                        panel_config_new[panel_number] = unused_screens[index]
                else:

                    if remove_extra_panels:
                        print ("Remove panel", panel_number)
                        panels_to_remove.append(f"/panels/panel-{panel_number}")
                        del panel_config_new[panel_number]

        
        # pprint ({prop: self.properties[prop] for prop in self.properties if prop.startswith("/panels")})

        # Cleanup panels
        if panels_to_remove:

            # remove unecessary panels
            self.remove_keys(panels_to_remove)

            # Update panels array
            new_panel_keys = ", ".join([ f"<{index}>" for index in panel_config_new.keys() ])
            new_panel_keys = f"[{new_panel_keys}]"
            self.properties["/panels"] = GLib.Variant.parse(None, new_panel_keys, None, None)

        # Report changes to user
        if panel_config_new != panel_config_orig:
            print ("New configuration")
            pprint ({prop: self.properties[prop] for prop in self.properties if prop.startswith("/panels")})



    def remove_orphans(self):
        plugin_ids = set()
        rem_keys = []

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 4 and path[0] == '' and path[1] == 'panels' and \
                    path[2].startswith('panel-') and path[3] == 'plugin-ids':
                plugin_ids.update(pv)

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 3 and path[0] == '' and path[1] == 'plugins' and \
                    path[2].startswith('plugin-'):
                number = path[2].split('-')[1]
                try:
                    if int(number) not in plugin_ids:
                        rem_keys.append('/plugins/plugin-' + number)
                except ValueError:
                    pass

        self.remove_keys(rem_keys)

    def check_desktop(self, path):
        try:
            f = self.get_desktop_source_file(path)
            bytes = f.read()
            f.close()
        except (KeyError, FileNotFoundError):
            return False

        # Check if binary exists
        keyfile = GLib.KeyFile.new()
        try:
            if keyfile.load_from_data(bytes.decode(), len(bytes), GLib.KeyFileFlags.NONE):
                exec_str = keyfile.get_string("Desktop Entry", "Exec")
                if self.check_exec(exec_str):
                    return True
        except GLib.Error:  # pylint: disable=E0712
            self.errors.append('Error parsing desktop file ' + path)
            pass #  https://bugzilla.xfce.org/show_bug.cgi?id=14597

        return False

    def find_desktops(self):
        rem_keys = []

        for pp, pv in self.properties.items():
            path = pp.split('/')
            if len(path) == 3 and path[0] == '' and path[1] == 'plugins' and \
                    path[2].startswith('plugin-'):
                number = path[2].split('-')[1]
                if pv.get_type_string() == 's' and \
                        pv.get_string() == 'launcher':
                    prop_path = '/plugins/plugin-' + number + '/items'
                    if prop_path not in self.properties:
                        rem_keys.append('/plugins/plugin-' + number)
                        continue
                    for d in self.properties[prop_path].unpack():
                        desktop_path = 'launcher-' + number + '/' + d
                        if self.check_desktop(desktop_path):
                            self.desktops.append(desktop_path)
                        else:
                            rem_keys.append('/plugins/plugin-' + number)

        self.remove_keys(rem_keys)

    def find_rc_files(self):
        if self.source_not_file():
            plugin_ids = []
            filenames = []

            for pp in self.properties:
                path = pp.split('/')
                if len(path) == 4 and path[0] == '' and path[1] == 'panels' and path[3] == 'plugin-ids':
                    plugin_ids.extend(self.properties[pp])

            if len(plugin_ids) == 0:
                return

            for plugin_id in plugin_ids:
                plugin_id = str(plugin_id)
                prop_path = '/plugins/plugin-' + plugin_id
                try:
                    prop = self.properties[prop_path].get_string()
                except:
                    continue

                if prop == 'launcher':
                    continue

                filename = prop + '-' + plugin_id + '.rc'
                path = os.path.join(config_dir, filename)
                if os.path.exists(path):
                    filenames.append(filename)
            self.rc_files = filenames
        else:
            filenames = self.source.getnames()
            for filename in filenames:
                if filename.find('.rc') > -1:
                    self.rc_files.append(filename)

    def remove_keys(self, rem_keys):
        keys = list(self.properties.keys())
        for param in keys:
            for bad_plugin in rem_keys:
                if param == bad_plugin or param.startswith(bad_plugin+'/'):
                    try:
                        del self.properties[param]
                    except KeyError:
                        pass #  https://bugzilla.xfce.org/show_bug.cgi?id=14934

    def get_desktop_source_file(self, desktop):
        if self.source_not_file():
            path = os.path.join(config_dir, desktop)
            return open(path, 'rb')
        else:
            return self.source.extractfile(desktop)

    def get_rc_source_file(self, rc):
        if self.source_not_file():
            path = os.path.join(config_dir, rc)
            return open(path, 'rb')
        else:
            return self.source.extractfile(rc)

    def to_file(self, filename):
        if filename.endswith('.gz'):
            mode = 'w:gz'
        elif filename.endswith('.bz2'):
            mode = 'w:bz2'
        else:
            mode = 'w'
        t = tarfile.open(name=filename, mode=mode)
        props_tmp = []
        for (pp, pv) in sorted(self.properties.items()):
            props_tmp.append(str(pp) + ' ' + str(pv))
        add_to_tar(t, '\n'.join(props_tmp).encode('utf8'), 'config.txt')

        for d in self.desktops:
            bytes = self.get_desktop_source_file(d).read()
            add_to_tar(t, bytes, d)

        for rc in self.rc_files:
            bytes = self.get_rc_source_file(rc).read()
            add_to_tar(t, bytes, rc)

        t.close()

    def check_exec(self, program):
        program = program.strip()
        if len(program) == 0:
            return False

        params = list(GLib.shell_parse_argv(program)[1])
        executable = params[0]

        if os.path.exists(executable):
            return True

        path = GLib.find_program_in_path(executable)
        if path is not None:
            return True

        return False

    def to_xfconf(self, xfconf):
        # assert False, "WIPPP"
        session_bus = Gio.BusType.SESSION
        conn = Gio.bus_get_sync(session_bus, None)

        destination = 'org.xfce.Panel'
        path = '/org/xfce/Panel'
        interface = destination

        dbus_proxy = Gio.DBusProxy.new_sync(conn, 0, None, destination, path, interface, None)

        if dbus_proxy is not None:
            # Reset all properties to make sure old settings are invalidated
            try:
                xfconf.call_sync('ResetProperty', GLib.Variant(
                    '(ssb)', ('xfce4-panel', '/', True)), 0, -1, None)
            except GLib.Error:  # pylint: disable=E0712
                pass

            for (pp, pv) in sorted(self.properties.items()):
                xfconf.call_sync('SetProperty', GLib.Variant(
                    '(ssv)', ('xfce4-panel', pp, pv)), 0, -1, None)

            for d in self.desktops:
                bytes = self.get_desktop_source_file(d).read()
                mkdir_p(config_dir + os.path.dirname(d))
                f = open(config_dir + d, 'wb')
                f.write(bytes)
                f.close()

            for rc in self.rc_files:
                bytes = self.get_rc_source_file(rc).read()
                f = open(os.path.join(config_dir, rc), 'wb')
                f.write(bytes)
                f.close()

                # Kill the plugin so that it reloads the config we just wrote and does
                # not overwrite it with its current cache when the panel restarts below.
                # Some plugins don't save their config when restarting the panel
                # (e.g. whiskermenu) but others do (e.g. netload)
                plugin_id = rc.replace('.', '-').split('-')[1]
                proc_name_prefix = 'panel-' + plugin_id + '-'
                for proc in psutil.process_iter():
                    if proc.name().startswith(proc_name_prefix):
                        proc.kill()

            try:
                dbus_proxy.call_sync('Terminate', GLib.Variant('(b)', ('xfce4-panel',)), 0, -1, None)
            except GLib.GError:  # pylint: disable=E0712
                pass

    def has_errors(self):
        return len(self.errors) > 0




    def rc_to_xfconf(self, xfconf):
        # assert False, "WIPPP"
        session_bus = Gio.BusType.SESSION
        conn = Gio.bus_get_sync(session_bus, None)

        destination = 'org.xfce.Panel'
        path = '/org/xfce/Panel'
        interface = destination

        dbus_proxy = Gio.DBusProxy.new_sync(conn, 0, None, destination, path, interface, None)

        if dbus_proxy is not None:
            # Reset all properties to make sure old settings are invalidated
            try:
                xfconf.call_sync('ResetProperty', GLib.Variant(
                    '(ssb)', ('xfce4-panel', '/', True)), 0, -1, None)
            except GLib.Error:  # pylint: disable=E0712
                pass

            for (pp, pv) in sorted(self.properties.items()):
                xfconf.call_sync('SetProperty', GLib.Variant(
                    '(ssv)', ('xfce4-panel', pp, pv)), 0, -1, None)

            # for d in self.desktops:
            #     bytes = self.get_desktop_source_file(d).read()
            #     mkdir_p(config_dir + os.path.dirname(d))
            #     f = open(config_dir + d, 'wb')
            #     f.write(bytes)
            #     f.close()

            # for rc in self.rc_files:
            #     bytes = self.get_rc_source_file(rc).read()
            #     f = open(os.path.join(config_dir, rc), 'wb')
            #     f.write(bytes)
            #     f.close()

            #     # Kill the plugin so that it reloads the config we just wrote and does
            #     # not overwrite it with its current cache when the panel restarts below.
            #     # Some plugins don't save their config when restarting the panel
            #     # (e.g. whiskermenu) but others do (e.g. netload)
            #     plugin_id = rc.replace('.', '-').split('-')[1]
            #     proc_name_prefix = 'panel-' + plugin_id + '-'
            #     for proc in psutil.process_iter():
            #         if proc.name().startswith(proc_name_prefix):
            #             proc.kill()

            try:
                dbus_proxy.call_sync('Terminate', GLib.Variant('(b)', ('xfce4-panel',)), 0, -1, None)
            except GLib.GError:  # pylint: disable=E0712
                pass
