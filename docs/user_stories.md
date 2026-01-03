# User Stories - Proton Drive Linux GUI

## Epic 1: Initial Setup & Authentication

*   **US-01**: As a **new user**, I want to **launch the app and see a "Connect Account" button**, so that I can easily start the setup process without reading documentation.
*   **US-02**: As a **Proprietary Software refugee**, I want to **log in using my existing Proton credentials**, so that I can access my files.
*   **US-03**: As a **security-conscious user**, I want to **use 2FA during login**, so that my account remains secure.
*   **US-04**: As a **user**, I want the app to **remember my login**, so I don't have to re-authenticate every time I reboot my computer.

## Epic 2: Daily Usage (Mounting & Sync)

*   **US-05**: As a **content creator**, I want to **mount my Proton Drive as a folder (e.g., `~/ProtonDrive`)**, so that I can open files directly in applications like Krita or Blender. [x]
*   **US-06**: As a **user**, I want to **see a tray icon** that shows me if the drive is currently connected or syncing. [x]
*   **US-07**: As a **Flatpak user**, I want the app to **handle FUSE permissions automatically**, so I don't have to fiddle with command-line overrides. [x]
*   **US-08**: As a **user with limited bandwidth**, I want to **adjust the cache size**, so the app doesn't consume all my disk space. [ ]

## Epic 3: Monitoring & Settings

*   **US-09**: As a **user**, I want to **see how much storage space I have left**, so I can manage my quota. [x]
*   **US-10**: As a **user**, I want to **enable "Start on Boot"**, so my drive is always available when I turn on my Bazzite handheld/PC. [x]
*   **US-11**: As a **careful user**, I want to **disconnect/unmount the drive safely** from the GUI, to ensure data consistency before shutting down. [x]

## Epic 4: Troubleshooting

*   **US-12**: As a **technical user**, I want to **view logs**, so I can diagnose why a file isn't syncing. [x]
*   **US-13**: As a **user**, I want to **reset the configuration**, in case the authentication token expires or becomes invalid. [x]
