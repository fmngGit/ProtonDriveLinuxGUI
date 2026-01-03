#!/usr/bin/env python3
import sys
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from controller import ProtonDriveController
import signal
import subprocess
import threading

class ProtonDriveWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'ProtonDriveWindow'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        pass

class ProtonDriveApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id='org.example.protondrive',
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.controller = ProtonDriveController()
        self.tray_process = None
        self.tray_thread = None

    def do_activate(self):
        win = self.props.active_window
        if not win:
            self.builder = Gtk.Builder()
            ui_path = os.path.join(os.path.dirname(__file__), 'interface.ui')
            self.builder.add_from_file(ui_path)
            
            win = self.builder.get_object('ProtonDriveWindow')
            win.set_application(self)
            
            # Setup Window Close Interception
            win.connect('close-request', self.on_window_close_request)

            # Setup Tray
            self.setup_system_tray()

            
            self.connect_button = self.builder.get_object('connect_button')
            self.status_label = self.builder.get_object('status_label')
            self.mount_switch = self.builder.get_object('mount_switch')
            self.autostart_switch = self.builder.get_object('autostart_switch')
            self.quota_label = self.builder.get_object('quota_label')
            self.quota_bar = self.builder.get_object('quota_bar')
            self.user_label = self.builder.get_object('user_label')
            
            self.connect_button.connect('clicked', self.on_connect_clicked)
            self.mount_switch.connect('notify::active', self.on_mount_toggled)
            self.autostart_switch.connect('notify::active', self.on_autostart_toggled)
            
            self.controller.connect('mount-error', self.on_mount_error)
            self.controller.connect('mount-log', self.on_mount_log)
            
            self.log_view = self.builder.get_object('log_view')

            # Initialize Autostart state
            self.autostart_switch.set_active(self.controller.check_autostart())
            
            # Initial check
            ok, msg = self.controller.check_installation()
            if not ok:
                self.status_label.set_label(f"Error: {msg}")
                self.connect_button.set_sensitive(False)
            else:
                self.check_login_status()

            # Handle Minimized Start
            if "--minimized" in sys.argv:
                print("Starting minimized to tray...")
                # Auto-mount if configured
                if self.controller.check_config():
                    GLib.idle_add(lambda: self.mount_switch.set_active(True))
                # Do not present window
            else:
                win.present()

    def check_login_status(self):
        if self.controller.check_config():
            self.status_label.set_label("Status: Ready to Mount")
            self.connect_button.set_label("Disconnect Account")
            self.connect_button.add_css_class("destructive-action")
            self.mount_switch.set_sensitive(True)
            
            # Reuse button for disconnect logic later
            try:
                self.connect_button.disconnect_by_func(self.on_connect_clicked)
            except: pass
            self.connect_button.connect('clicked', self.on_disconnect_clicked)
            
            # Update Quota
            GLib.idle_add(self.update_quota_ui)
            
            # Update User Label
            username = self.controller.get_current_user()
            if username:
                self.user_label.set_text(username)
                self.user_label.set_visible(True)
            else:
                 self.user_label.set_visible(False)
        else:
            self.status_label.set_label("Status: Login Required")
            self.mount_switch.set_sensitive(False)
            self.mount_switch.set_active(False)
            self.user_label.set_visible(False)
            # Reset button state
            self.connect_button.set_label("Connect Account")
            self.connect_button.remove_css_class("destructive-action")
            try:
                self.connect_button.disconnect_by_func(self.on_disconnect_clicked)
            except: pass
            self.connect_button.connect('clicked', self.on_connect_clicked)

    def setup_system_tray(self):
        """Launches the tray helper process."""
        tray_script = os.path.join(os.path.dirname(__file__), 'tray.py')
        try:
            self.tray_process = subprocess.Popen(
                ["python3", tray_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr to debug tray issues
                text=True,
                bufsize=1
            )
            
            # Start monitoring thread
            self.tray_thread = threading.Thread(target=self._monitor_tray, daemon=True)
            self.tray_thread.start()
            
        except Exception as e:
            print(f"Failed to start tray icon: {e}")

    def _monitor_tray(self):
        """Reads commands from the tray process."""
        while self.tray_process and self.tray_process.poll() is None:
            line = self.tray_process.stdout.readline()
            if not line: break
            
            line = line.strip()
            
            if line == "ACTION:SHOW":
                GLib.idle_add(self.on_tray_show)
            elif line == "ACTION:TOGGLE":
                GLib.idle_add(self.on_tray_toggle)
            elif line == "ACTION:QUIT":
                GLib.idle_add(self.quit)

    def on_window_close_request(self, win):
        """Hides the window instead of closing it."""
        # If tray is not running, close normally
        if not self.tray_process or self.tray_process.poll() is not None:
             return False

        win.hide()
        # Return True to prevent default destruction
        return True

    def on_tray_show(self):
        win = self.props.active_window
        if win:
            win.set_visible(True)
            win.present()

    def on_tray_toggle(self):
        if hasattr(self, 'mount_switch'):
             active = self.mount_switch.get_active()
             self.mount_switch.set_active(not active)
             
    def send_tray_update(self, status):
        """Sends status to tray process."""
        if self.tray_process and self.tray_process.poll() is None:
            try:
                self.tray_process.stdin.write(f"STATUS:{status}\n")
                self.tray_process.stdin.flush()
            except BrokenPipeError:
                pass

    def do_shutdown(self):
        if self.tray_process:
            try:
                self.tray_process.stdin.write("QUIT\n")
                self.tray_process.stdin.flush()
            except: pass
            self.tray_process.terminate()
        
        # Superclass shutdown
        Adw.Application.do_shutdown(self)

    def on_mount_toggled(self, switch, gparam):
        if switch.get_active():
            self.status_label.set_label("Mounting...")
            switch.set_sensitive(False) # Prevent toggling while processing
            self.controller.start_mount(self.on_mount_result)
            self.send_tray_update("MOUNTING")
        else:
            self.status_label.set_label("Unmounting...")
            switch.set_sensitive(False)
            self.controller.stop_mount(self.on_mount_result)
            self.send_tray_update("UNMOUNTING")

    def on_mount_result(self, success, message):
        self.mount_switch.set_sensitive(True)
        self.status_label.set_label(f"Status: {message}")
        if not success:
            # Revert switch if failed
            # Block signal to prevent loop
            self.mount_switch.handler_block_by_func(self.on_mount_toggled)
            self.mount_switch.set_active(not self.mount_switch.get_active())
            self.mount_switch.handler_unblock_by_func(self.on_mount_toggled)
            self.send_tray_update("DISCONNECTED")
        else:
             if "unmounted" in message.lower():
                 self.send_tray_update("DISCONNECTED")
             else:
                 self.send_tray_update("MOUNTED")
                 self.update_quota_ui()

    def on_mount_log(self, controller, message):
        buffer = self.log_view.get_buffer()
        end_iter = buffer.get_end_iter()
        buffer.insert(end_iter, message)
        
        # Scroll to bottom
        adj = self.log_view.get_parent().get_vadjustment()
        if adj:
             adj.set_value(adj.get_upper() - adj.get_page_size())

    def on_mount_error(self, controller, message):
        self.status_label.set_label(f"Error: {message}")
        try:
            self.status_label.add_css_class("error")
        except: pass # GtkLabel might not support add_css_class directly in some bindings if not widget? No, it's fine.
        
        # Reset switch without triggering toggle logic again (block handlers)
        self.mount_switch.handler_block_by_func(self.on_mount_toggled)
        self.mount_switch.set_active(False)
        self.mount_switch.handler_unblock_by_func(self.on_mount_toggled)
        self.mount_switch.set_sensitive(True)

    def on_connect_clicked(self, button):
        # Open Login Dialog
        self.login_window = self.builder.get_object('LoginWindow')
        self.login_window.set_transient_for(self.props.active_window)
        
        self.username_entry = self.builder.get_object('username_entry')
        self.password_entry = self.builder.get_object('password_entry')
        self.two_fa_entry = self.builder.get_object('2fa_entry')
        self.login_status_label = self.builder.get_object('login_status_label')
        
        confirm_btn = self.builder.get_object('login_confirm_button')
        # Disconnect any previous signals to avoid multiple bindings
        try:
            confirm_btn.disconnect_by_func(self.on_login_confirm)
        except:
            pass
        confirm_btn.connect('clicked', self.on_login_confirm)
        
        self.login_window.present()

    def on_disconnect_clicked(self, button):
        if self.controller.delete_config():
            self.check_login_status()
            self.status_label.set_label("Disconnected")
            self.send_tray_update("DISCONNECTED")
        else:
             self.status_label.set_label("Error disconnecting")

    def update_quota_ui(self):
        used, total = self.controller.get_quota()
        if used is None or total is None or total == 0:
             self.quota_label.set_label("Storage Usage: Unknown")
             self.quota_bar.set_value(0)
             return

        # Format bytes
        import math
        def convert_size(size_bytes):
            if size_bytes == 0: return "0B"
            size_name = ("B", "KB", "MB", "GB", "TB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return "%s %s" % (s, size_name[i])

        usage_str = f"{convert_size(used)} used of {convert_size(total)}"
        self.quota_label.set_label(f"Storage Usage: {usage_str}")
        self.quota_bar.set_value(used / total)

    def on_autostart_toggled(self, switch, gparam):
        self.controller.set_autostart(switch.get_active())

    def on_login_confirm(self, button):
        username = self.username_entry.get_text()
        password = self.password_entry.get_text()
        two_fa = self.two_fa_entry.get_text()
        
        if not username or not password:
            self.login_status_label.set_text("Username and Password are required.")
            self.login_status_label.set_visible(True)
            return

        self.login_status_label.set_visible(False)
        button.set_sensitive(False)
        self.login_status_label.set_text("Connecting...")
        self.login_status_label.set_visible(True)
        
        self.controller.create_config_interactive(username, password, two_fa, self.on_login_result)

    def on_login_result(self, success, message, loading=False):
        if loading:
            self.login_status_label.set_text(message)
            return

        confirm_btn = self.builder.get_object('login_confirm_button')
        confirm_btn.set_sensitive(True)
        
        if success:
            self.login_window.close()
            self.check_login_status()
            # Show toast or simple message
            self.status_label.set_text(message)
        else:
            self.login_status_label.set_text(message)
            self.login_status_label.add_css_class("error")
            self.login_status_label.set_visible(True)

def main():
    app = ProtonDriveApp()
    return app.run(sys.argv)

if __name__ == '__main__':
    sys.exit(main())
