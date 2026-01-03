import gi
import sys
import signal

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import AppIndicator3
except ValueError:
    try:
        gi.require_version('AyatanaAppIndicator3', '0.1')
        from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    except ValueError:
        print("AppIndicator3 not found")
        sys.exit(1)

from gi.repository import Gtk, GLib

APPINDICATOR_ID = 'proton-drive-tray'

class TrayIcon:
    def __init__(self):
        self.indicator = AppIndicator3.Indicator.new(
            APPINDICATOR_ID,
            "drive-harddisk", # Default icon (safer than network-cloud)
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())
        
        # Watch stdin for updates
        GLib.io_add_watch(GLib.IOChannel(0), GLib.IO_IN, self.on_stdin_data)

    def build_menu(self):
        menu = Gtk.Menu()
        
        item_show = Gtk.MenuItem(label="Show Window")
        item_show.connect('activate', self.on_show)
        menu.append(item_show)

        item_toggle = Gtk.MenuItem(label="Mount/Unmount")
        item_toggle.connect('activate', self.on_toggle)
        menu.append(item_toggle)

        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label="Quit")
        item_quit.connect('activate', self.on_quit)
        menu.append(item_quit)
        
        menu.show_all()
        return menu

    def on_show(self, _):
        print("ACTION:SHOW")
        sys.stdout.flush()

    def on_toggle(self, _):
        print("ACTION:TOGGLE")
        sys.stdout.flush()

    def on_quit(self, _):
        print("ACTION:QUIT")
        sys.stdout.flush()
        Gtk.main_quit()

    def on_stdin_data(self, source, condition):
        line = sys.stdin.readline()
        if not line:
            Gtk.main_quit()
            return False
            
        line = line.strip()
        if line.startswith("STATUS:"):
            status = line.split(":", 1)[1]
            # Update menu or icon based on status if needed
            # For MVP just keep generic icon
            pass
        elif line == "QUIT":
            Gtk.main_quit()
            return False
            
        return True

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = TrayIcon()
    Gtk.main()

if __name__ == "__main__":
    main()
