import gi
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('AppIndicator3', '0.1')
    from gi.repository import Gtk, AppIndicator3
    print("Imports successful")
    app = Gtk.Application()
    print("Gtk4 App created")
except Exception as e:
    print(f"Error: {e}")
