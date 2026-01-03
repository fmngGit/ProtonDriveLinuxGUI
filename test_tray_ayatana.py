import gi
try:
    gi.require_version('Gtk', '4.0')
    gi.require_version('AyatanaAppIndicator3', '0.1')
    from gi.repository import Gtk, AyatanaAppIndicator3
    print("Imports successful")
except Exception as e:
    print(f"Error: {e}")
