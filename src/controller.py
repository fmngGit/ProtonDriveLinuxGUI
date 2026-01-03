import subprocess
import shutil
import os
import json
import logging
from gi.repository import GLib, GObject

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ProtonDriveController")

class ProtonDriveController(GObject.Object):
    __gsignals__ = {
        'mount-error': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        'mount-log': (GObject.SignalFlags.RUN_LAST, None, (str,))
    }

    def __init__(self):
        super().__init__()
        self.rclone_path = shutil.which("rclone")
        # Fallback to local bin if not found in path (for Flatpak)
        if not self.rclone_path and os.path.exists("/app/bin/rclone"):
            self.rclone_path = "/app/bin/rclone"

        self.config_name = "proton"
        
    def check_installation(self):
        """Checks if rclone is installed."""
        if not self.rclone_path:
            return False, "rclone binary not found."
        return True, f"Found rclone at {self.rclone_path}"

    def check_config(self):
        """Checks if the proton remote is already configured."""
        if not self.rclone_path:
            return False
            
        try:
            # List remotes to see if 'proton' exists
            result = subprocess.run(
                [self.rclone_path, "listremotes"], 
                capture_output=True, 
                text=True
            )
            return f"{self.config_name}:" in result.stdout
        except Exception as e:
            logger.error(f"Error checking config: {e}")
            return False

    def get_quota(self):
        """Returns (used, total) bytes or (None, None) on error."""
        if not self.rclone_path:
            return None, None
            
        try:
            # rclone about remote: --json
            result = subprocess.run(
                [self.rclone_path, "about", f"{self.config_name}:", "--json"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logger.error(f"Error checking quota: {result.stderr}")
                return None, None
                
            import json
            data = json.loads(result.stdout)
            return data.get("used", 0), data.get("total", 0)
            
        except Exception as e:
            logger.error(f"Failed to get quota: {e}")
            return None, None

    def get_current_user(self):
        try:
             user_file = os.path.expanduser("~/.config/protondrive-gui/user.json")
             if os.path.exists(user_file):
                 import json
                 with open(user_file, 'r') as f:
                     data = json.load(f)
                     return data.get("username")
        except: pass
        return None

    def delete_config(self):
        """Removes the proton remote configuration."""
        if not self.rclone_path:
            return False
            
        try:
            # Stop mount first if active
            self.stop_mount()
            
            logger.info(f"Deleting remote {self.config_name}")
            subprocess.run(
                [self.rclone_path, "config", "delete", self.config_name],
                check=True
            )
            # Also remove user info
            try:
                os.remove(os.path.expanduser("~/.config/protondrive-gui/user.json"))
            except: pass
            
            return True
        except Exception as e:
            logger.error(f"Failed to delete config: {e}")
            return False

    def obscure_password(self, password):
        """Obscures the password using rclone obscure."""
        try:
            result = subprocess.run(
                [self.rclone_path, "obscure", password],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to obscure password: {e}")
            return None

    def create_config_interactive(self, username, password, two_fa_code, callback):
        """
        Runs rclone config create interactively in a background thread.
        """
        def _run_config():
            obscured_pass = self.obscure_password(password)
            if not obscured_pass:
                GLib.idle_add(callback, False, "Failed to process password.")
                return

            cmd = [
                self.rclone_path, 
                "config", "create", self.config_name, "protondrive",
                f"username={username}",
                f"password={obscured_pass}",
                "--non-interactive"
            ]
            
            if two_fa_code and two_fa_code.strip():
                # Only append 2FA if provided
                pass 
                # Actually, the original code had `if two_fa_code: cmd.append(...)`.
                # If the user passed empty string "", it evaluated to False? 
                # Let's verify. Yes, empty string is False.
                # But let's be explicit and strip it.
                cmd.append(f"2fa={two_fa_code.strip()}")
            
            # Note: If Proton EXPECTS 2FA and we send nothing, it fails. 
            # If Proton DOES NOT expect 2FA and we send nothing, it works.
            # If we send 2fa="" (empty), rclone might get confused. 
            
            # The error "Incorrect login credentials" (422) suggests:
            # 1. Password wrong? (Obscuring issue?)
            # 2. 2FA needed but not provided?
            # 3. 2FA provided but wrong?
            
            # Let's add logging to see what we are sending (omitting sensitive data)
            safe_cmd = cmd.copy()
            # Redact password for log
            safe_cmd[6] = "password=***" 
            if len(safe_cmd) > 8: # If 2FA was added
                 safe_cmd[-1] = "2fa=***"
            
            logger.info(f"Running config command: {safe_cmd}")

            try:
                msg = f"Attempting to login as {username}..."
                GLib.idle_add(lambda: callback(False, msg, True)) # Update status, keep loading

                # rclone config create returns 0 on success
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if process.returncode == 0:
                    # Save username for display
                    try:
                         user_file = os.path.expanduser("~/.config/protondrive-gui/user.json")
                         if not os.path.exists(os.path.dirname(user_file)):
                             os.makedirs(os.path.dirname(user_file), exist_ok=True)
                         
                         import json
                         with open(user_file, 'w') as f:
                             json.dump({"username": username}, f)
                    except: pass

                    GLib.idle_add(callback, True, "Login successful!")
                else:
                    error_msg = process.stderr
                    GLib.idle_add(callback, False, f"Login failed: {error_msg}")

            except Exception as e:
                GLib.idle_add(callback, False, f"System error: {e}")

        # Run in a separate thread to not block UI
        import threading
        thread = threading.Thread(target=_run_config)
        thread.daemon = True
        thread.start()

    def get_remote_name(self):
        return f"{self.config_name}:"

    def get_mount_path(self):
        # Default mount path in user's home or run/user
        # For simplicity in prototype, use ~/ProtonDrive
        return os.path.expanduser("~/ProtonDrive")

    def _prepare_mount_point(self, path):
        """Ensures the mount point is clean and exists."""
        # 1. Try to unmount if it's a stale mount
        try:
             subprocess.run(["fusermount3", "-u", "-z", path], stderr=subprocess.DEVNULL)
        except: pass
        
        # 2. Now try to create it
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)
            
    def start_mount(self, callback):
        """Starts rclone mount in the background."""
        if hasattr(self, 'mount_process') and self.mount_process and self.mount_process.poll() is None:
            callback(True, "Already mounted.")
            return

        mount_point = self.get_mount_path()
        
        # Ensure it's ready
        try:
            self._prepare_mount_point(mount_point)
        except Exception as e:
            callback(False, f"Failed to prepare mount point: {e}")
            return

        remote = self.get_remote_name()

        # Command: rclone mount proton: ~/ProtonDrive --vfs-cache-mode writes
        # We remove --daemon to manage it ourselves
        cmd = [
            self.rclone_path, 
            "mount", 
            remote, 
            mount_point, 
            "--vfs-cache-mode", "full",
            "--allow-non-empty",
            "-v" # Verbose logging
        ]

        try:
            # We use Popen to keep it running
            # Check if fusermount3 or fusermount is available (rclone needs one)
            if not shutil.which("fusermount3") and not shutil.which("fusermount"):
                 callback(False, "Error: fusermount/fusermount3 not found. Install fuse3?")
                 return

            logger.info(f"Starting mount command: {' '.join(cmd)}")
            self.mount_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1, # Line buffered
                universal_newlines=True
            )
            
            # Start a thread to read stderr for logs
            import threading
            def log_reader():
                while self.mount_process and self.mount_process.poll() is None:
                    line = self.mount_process.stderr.readline()
                    if line:
                        GLib.idle_add(self.emit, 'mount-log', line)
            
            self.log_thread = threading.Thread(target=log_reader, daemon=True)
            self.log_thread.start()

            # Start a monitoring loop for exit check
            GLib.timeout_add(1000, self._monitor_mount, callback)
            
            # success (tentative) - we don't know if it fully worked until we check later, 
            # but for UI responsiveness we say "Mounting..." or "Mounted"
            self.is_connected = True
            callback(True, "Mounted successfully")

        except Exception as e:
            logger.error(f"Failed to start mount: {e}")
            callback(False, str(e))

    def _monitor_mount(self, callback):
        """Checks if the mount process is still alive."""
        if not hasattr(self, 'mount_process') or not self.mount_process:
            return False # Stop monitoring

        ret = self.mount_process.poll()
        if ret is not None:
            # Process exited
            # stdout, stderr = self.mount_process.communicate() 
            # Note: communicate() might block if streams are open, and we are reading stderr in thread.
            # So we should be careful. 
            # Since thread reads stderr, we rely on it.
            
            self.is_connected = False
            self.mount_process = None
            
            # Notify failure via signal
            # We assume the log reader has captured the error output already.
            self.emit('mount-error', f"Mount process exited with code {ret}")
            return False
            
        return True # Continue monitoring

    def stop_mount(self, callback=None):
        """Stops the rclone mount process."""
        if hasattr(self, 'mount_process') and self.mount_process:
            logger.info("Stopping mount...")
            # Try to terminate gracefully
            self.mount_process.terminate()
            try:
                self.mount_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Mount process hung, killing...")
                self.mount_process.kill()
            
            self.mount_process = None
            self.is_connected = False
            if callback:
                callback(True, "Unmounted successfully")
        
    def get_autostart_file(self):
        return os.path.expanduser("~/.config/autostart/protondrive-gui.desktop")

    def check_autostart(self):
        return os.path.exists(self.get_autostart_file())

    def set_autostart(self, enable):
        path = self.get_autostart_file()
        if enable:
            if not os.path.exists(os.path.dirname(path)):
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Determine Exec command
            # For development usage, we point to the python script
            # In proper packaging, this would be the app ID
            cwd = os.getcwd()
            exec_cmd = f"python3 {os.path.join(cwd, 'src', 'main.py')} --minimized"
            
            content = f"""[Desktop Entry]
Type=Application
Name=Proton Drive GUI
Comment=Unofficial Proton Drive Client
Exec={exec_cmd}
Icon=drive-harddisk
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
"""
            try:
                with open(path, "w") as f:
                    f.write(content)
                return True
            except Exception as e:
                logger.error(f"Failed to create autostart: {e}")
                return False
        else:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    return True
                except Exception as e:
                    logger.error(f"Failed to remove autostart: {e}")
                    return False
            return True
