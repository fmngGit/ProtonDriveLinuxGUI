# Technical Plan & Architecture - Proton Drive Linux GUI

## 1. Architecture Overview

The application follows a standard Model-View-Controller (MVC) pattern, adapted for a GTK4 application.

*   **Frontend (View)**: GTK4 + Libadwaita (Python). Provides a modern, responsive UI that fits well with GNOME and Bazzite's desktop mode.
*   **Controller**: Python logic that bridges the UI and the rclone subprocess. Handles state management, configuration parsing, and signal handling.
*   **Backend (Model)**: `rclone` (binary). Handles the actual communication with Proton Drive API, encryption, and FUSE mounting.

```mermaid
graph TD
    User[User] -->|Interacts| GUI[GTK4/Libadwaita GUI]
    GUI -->|Commands| Controller[Python Controller]
    GUI -->|Launches/Talks| Tray[Tray Helper Process (GTK3)]
    Controller -->|Manages| Rclone[Rclone Subprocess]
    Controller -->|Reads/Writes| Config[Config File (~/.var/app/...)]
    Rclone -->|Mounts via FUSE| Mount[Local Mountpoint]
    Rclone -->|HTTPS| Proton[Proton Drive Servers]
```

## 2. Technology Stack

*   **Language**: Python 3.10+
*   **GUI Toolkit**: PyGObject (GTK4), Libadwaita
*   **Core Dependency**: `rclone` (bundled or via Flatpak SDK extension)
*   **Packaging**: Flatpak (freedesktop SDK)
*   **Async/Concurrency**: `GLib.subprocess` for non-blocking UI during rclone operations.

## 3. Key Components

### 3.1. Authentication Service
Wraps `rclone config`. Since rclone's interactive config CLI is hard to wrap blindly, we will automate the command flags or parse the `rclone.conf` generation.
*   *Strategy*: Utilize `rclone config create protondrive protondrive` type commands, or guide the user to paste the auth token if the browser callback is blocked in Flatpak (though `xdg-open` usually works).

### 3.2. Mount Manager
Controls the lifecycle of the `rclone mount` process.
*   Monitors the `pid` of the mount process.
*   Parses stdout/stderr for errors.
*   Handles graceful termination (unmount) on app exit.

### 3.3. System Tray / Status
Uses `AppIndicator` (shimmed for GNOME) or background portal to show status.

## 4. Development Phases

### Phase 1: Prototype (MVP)
*   [x] Basic GTK Window.
*   [x] Check for `rclone` binary.
*   [x] Hardcoded config for testing.
*   [x] Start/Stop Mount button.

### Phase 2: Configuration & Persistence
*   [x] Implement "Add Account" flow.
*   [x] Save configuration to persistent storage.
*   [x] Auto-mount logic (via Toggle + Persistence).

### Phase 5: Final Polish
*   [x] Implement Storage Quota Display (Used/Total).
*   [x] Tune Flatpak Permissions (Restricted to `filesystem=home`).
*   [x] Create CI/CD Workflow (GitHub Actions).
*   [x] Tray icon and notifications (Implemented via `src/tray.py` helper).
*   [x] Log Viewer for troubleshooting.

### Phase 4: Background Service & Integration
*   [x] Research System Tray implementation.
*   [x] Implement System Tray Icon with Menu (Show/Quit).
*   [x] Implement "Minimize to Tray" behavior.
*   [x] Implement "Start on Boot" (Autostart .desktop file).

## 5. Bazzite/Flatpak Specifics
*   **Filesystem Access**: The app needs read/write access to the specific directory chosen by the user for mounting. We will use the FileChooser portal which grants permission to the selected folder.
*   **FUSE**: Flatpak needs access to the FUSE device.
    *   `--device=all` is often needed for FUSE in Flatpaks, or at least `--device=dri` + access to `/dev/fuse`.
*   **Rclone Distribution**: We should include the `rclone` binary in the Flatpak builder manifest to ensure we have a compatible version.
