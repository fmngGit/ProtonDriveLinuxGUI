# Proton Drive Linux GUI

A native, unofficial graphical user interface for Proton Drive on Linux, designed for the Bazzite/Flatpak ecosystem. Built with GTK4, Libadwaita, and Python, leveraging `rclone` for reliable secure storage access.

## Features
*   **Easy Setup**: Graphical login flow with 2FA support.
*   **Native Integration**: Designed with GNOME guidelines for a seamless Bazzite experience.
*   **Mount**: Mount your Proton Drive as a local folder (`~/ProtonDrive`) with a single toggle.
*   **Logs**: Built-in real-time log viewer for troubleshooting.
*   **Secure**: Uses `rclone` internally (zero-knowledge encryption maintained).

## Requirements
*   **Runtime**: Flatpak (org.gnome.Platform // 45) or localized Python 3 + GTK4 environment.
*   **Dependencies**: `rclone` (bundled in Flatpak build), `fuse3`.

## Installation & Running

### For Development (Local)
1.  Ensure you have `python3`, `gtk4`, `libadwaita`, and `rclone` installed.
2.  Install python dependencies: `pip install pygobject`
3.  Run the app:
    ```bash
    python3 src/main.py
    ```

### For Bazzite / Flatpak
1.  Install `flatpak-builder`.
2.  Build and install the application:
    ```bash
    flatpak-builder --user --install --force-clean build-dir org.example.protondrive.json
    ```
3.  Run:
    ```bash
    flatpak run org.example.protondrive
    ```

## Usage
1.  **Login**: Click "Connect Account", enter your Proton credentials. If you have 2FA, enter the code; otherwise leave it blank.
2.  **Mount**: Toggle the "Mount Drive" switch. Your files will appear in `~/ProtonDrive`.
3.  **Logs**: Expand the "Show Logs" section to see real-time output from the background process.
5.  **Autostart**: Toggle "Start on Login" to automatically launch the app minimized to the tray when your computer starts.
6.  **Unmount**: Toggle the switch OFF to safely unmount.
7.  **Disconnect**: Click "Disconnect Account" to remove credentials from the system.

## Troubleshooting
*   **Mount failures**: Ensure `fuse3` is installed on your host system.
*   **App stuck/crashed**: The application automatically cleans up stale mount points on startup. If you have issues, simply restart the app.
*   **Login failures**: Verify your password. If using 2FA, ensure the code is fresh. Note that Proton mailbox passwords are different from login passwords if you are in "two-password mode" (rare for modern accounts).

## Known Issues
*   **Move to Trash**: Some file managers (like Dolphin/Nautilus) may fail to "Move to Trash" files on the mounted drive due to Proton API limitations (`Code=2000` error). 
    *   **Workaround**: Use **Permanent Delete** (Shift+Delete) to remove files.

## License
MIT License. This project is not affiliated with Proton AG.
