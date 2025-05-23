import rumps, psutil, subprocess, socket, requests, threading, shutil, json, os
from collections import deque

# Constants
SETTINGS_DEFAULTS = {
    "show_cpu": True,
    "show_memory": True, 
    "show_battery": True,
    "show_network": True,
    "show_clipboard": True,
    "show_uptime": True,
    "show_storage": True,
    "show_public_ip": True,
    "show_network_speed": True,
    "high_cpu_threshold": 86,
    "high_memory_threshold": 86
}

BOLD_LABELS = {
    "CPU": "𝗖𝗣𝗨",
    "Memory": "𝗠𝗘𝗠𝗢𝗥𝗬",
    "Battery": "𝗕𝗔𝗧𝗧𝗘𝗥𝗬",
    "Network Speed": "𝗡𝗘𝗧𝗪𝗢𝗥𝗞 𝗦𝗣𝗘𝗘𝗗",
    "Local IP": "𝗟𝗢𝗖𝗔𝗟 𝗜𝗣",
    "Public IP": "𝗣𝗨𝗕𝗟𝗜𝗖 𝗜𝗣",
    "Storage": "𝗦𝗧𝗢𝗥𝗔𝗚𝗘",
    "Uptime": "𝗨𝗣𝗧𝗜𝗠𝗘"
}

class SystemMonitorApp(rumps.App):

    """System Monitor for macOS Menu Bar"""

    def __init__(self):
        """Initialize the system monitor application"""
        super().__init__("💻", quit_button=None)  # Title menu bar

        # Initialize application directories and settings
        self.app_data_dir = os.path.expanduser("~/Library/Application Support/SystemMonitor")
        os.makedirs(self.app_data_dir, exist_ok=True)
        self.settings_file = os.path.join(self.app_data_dir, "settings.json")
        self.settings = self.load_settings()  

        # Initialize state variables
        self.clipboard_history = deque(maxlen=6)  
        self.last_clipboard = None
        self.last_net_io = psutil.net_io_counters()
        self.down_speed = self.up_speed = 0
        self.public_ip = "Checking..."
        
        # Setup UI and start monitoring
        self.setup_menu()
        self.start_monitoring()


    def start_monitoring(self) -> None:
        """Initialize and start all monitoring timers"""
        # Stats update every 3 seconds
        self.stats_timer = rumps.Timer(self.update_stats, 3)
        self.stats_timer.start()
        
        # Clipboard check every second (if enabled)
        if self.settings["show_clipboard"]:
            self.clipboard_timer = rumps.Timer(self.check_clipboard, 1)
            self.clipboard_timer.start()
            self.check_clipboard()  # Initial check
        
        # Public IP check every 10 minutes
        if self.settings["show_public_ip"]:
            self.ip_timer = rumps.Timer(self.update_public_ip, 600)
            self.ip_timer.start()
            # Initial IP check
            threading.Thread(target=self.update_public_ip).start()

    def load_settings(self) -> dict:
        """Load settings from file or return defaults if file doesn't exist"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file) as f:
                    return json.load(f)
            except Exception as e:
                print(f"Could not load settings, using defaults. Reason: {e}")
        return SETTINGS_DEFAULTS.copy()

    def save_settings(self) -> None:
        """Save current settings to the settings file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f)
        except (IOError, OSError) as e:
            print(f"Error saving settings to {self.settings_file}: {e}")

    def setup_menu(self):
        self.menu.clear()
        # Lihavoidut otsikot
        bold_labels = {
            "CPU": "𝗖𝗣𝗨",
            "Memory": "𝗠𝗘𝗠𝗢𝗥𝗬",
            "Battery": "𝗕𝗔𝗧𝗧𝗘𝗥𝗬",
            "Network Speed": "𝗡𝗘𝗧𝗪𝗢𝗥𝗞 𝗦𝗣𝗘𝗘𝗗",
            "Local IP": "𝗟𝗢𝗖𝗔𝗟 𝗜𝗣",
            "Public IP": "𝗣𝗨𝗕𝗟𝗜𝗖 𝗜𝗣",
            "Storage": "𝗦𝗧𝗢𝗥𝗔𝗚𝗘",
            "Uptime": "𝗨𝗣𝗧𝗜𝗠𝗘"
        }

        if self.settings["show_cpu"]:
            self.menu["CPU"] = rumps.MenuItem(bold_labels["CPU"] + ": -", callback=lambda _: None)
        if self.settings["show_memory"]:
            self.menu["Memory"] = rumps.MenuItem(bold_labels["Memory"] + ": -", callback=lambda _: None)
        if self.settings["show_battery"]:
            self.menu["Battery"] = rumps.MenuItem(bold_labels["Battery"] + ": -", callback=lambda _: None)
        if self.settings["show_network_speed"]:
            self.menu["Network Speed"] = rumps.MenuItem(bold_labels["Network Speed"] + ": -", callback=lambda _: None)
        if self.settings["show_network"]:
            self.menu["Local IP"] = rumps.MenuItem(bold_labels["Local IP"] + ": -", callback=lambda _: None)
        if self.settings["show_public_ip"]:
            self.menu["Public IP"] = rumps.MenuItem(bold_labels["Public IP"] + f": {self.public_ip}", callback=lambda _: None)
        if self.settings["show_storage"]:
            self.menu["Storage"] = rumps.MenuItem(bold_labels["Storage"] + ": -", callback=lambda _: None)
        if self.settings["show_uptime"]:
            self.menu["Uptime"] = rumps.MenuItem(bold_labels["Uptime"] + ": -", callback=lambda _: None)

        if self.settings["show_clipboard"]:
            self.menu["Clipboard History"] = rumps.MenuItem("Clipboard")
            for i in range(6):
                self.menu["Clipboard History"][f"Clip {i+1}"] = rumps.MenuItem("(empty)", callback=self.copy_from_history)
        self.menu.add(None)  # Erotin
        # Asetukset
        self.menu["Settings"] = "Settings"
        for label, key in [
            ("Show CPU", "show_cpu"), ("Show Memory", "show_memory"), ("Show Battery", "show_battery"),
            ("Show Network Speed", "show_network_speed"), ("Show Local IP", "show_network"),
            ("Show Public IP", "show_public_ip"), ("Show Storage", "show_storage"),
            ("Show Uptime", "show_uptime"), ("Show Clipboard History", "show_clipboard")
        ]:
            item = rumps.MenuItem(label, callback=self.toggle_setting)
            item.state = self.settings[key]
            self.menu["Settings"][label] = item

        quit_item = rumps.MenuItem("Quit", callback=self.quit)
        self.menu.add(quit_item)
    def toggle_setting(self, sender):
  
        setting_map = {
            "Show CPU": "show_cpu", "Show Memory": "show_memory", "Show Battery": "show_battery",
            "Show Network Speed": "show_network_speed", "Show Local IP": "show_network",
            "Show Public IP": "show_public_ip", "Show Storage": "show_storage",
            "Show Uptime": "show_uptime", "Show Clipboard History": "show_clipboard"
        }
        key = setting_map[sender.title]
        enabled = [k for k in setting_map.values() if self.settings[k]]
        if self.settings[key] and len(enabled) == 1:
            rumps.alert("Error", "You must select at least one item to display.")
            sender.state = True
            return
        self.settings[key] = not self.settings[key]
        self.save_settings()
        self.setup_menu()
        self.update_stats()

    def update_stats(self, _=None):

        try:
            bold_labels = {
                "CPU": "𝗖𝗣𝗨",
                "Memory": "𝗠𝗘𝗠𝗢𝗥𝗬",
                "Battery": "𝗕𝗔𝗧𝗧𝗘𝗥𝗬",
                "Network Speed": "𝗡𝗘𝗧𝗪𝗢𝗥𝗞 𝗦𝗣𝗘𝗘𝗗",
                "Local IP": "𝗟𝗢𝗖𝗔𝗟 𝗜𝗣",
                "Public IP": "𝗣𝗨𝗕𝗟𝗜𝗖 𝗜𝗣",
                "Storage": "𝗦𝗧𝗢𝗥𝗔𝗚𝗘",
                "Uptime": "𝗨𝗣𝗧𝗜𝗠𝗘"
            }
            if self.settings["show_cpu"]:
                cpu = psutil.cpu_percent()
                self.menu["CPU"].title = f"{bold_labels['CPU']}: {self.get_color_indicator(cpu, self.settings['high_cpu_threshold'])}{cpu}%"
            if self.settings["show_memory"]:
                mem = psutil.virtual_memory().percent
                self.menu["Memory"].title = f"{bold_labels['Memory']}: {self.get_color_indicator(mem, self.settings['high_memory_threshold'])}{mem}%"
            if self.settings["show_battery"]:
                b = psutil.sensors_battery()
                if b:
                    if b.power_plugged:
                        rem = " (⚡ Charging)" if b.percent < 100 else " (✓ Fully Charged)"
                    else:
                        rem = f" ({self.format_time(b.secsleft)} left)"
                    self.menu["Battery"].title = f"{bold_labels['Battery']}: {self.get_battery_indicator(b.percent)} {b.percent}%{rem}"
            if self.settings["show_network_speed"]:
                self.update_network_speeds()
                d_unit, d_val = self.format_network_speed(self.down_speed)
                u_unit, u_val = self.format_network_speed(self.up_speed)
                self.menu["Network Speed"].title = f"{bold_labels['Network Speed']}: ↓{d_val:.1f}{d_unit} ↑{u_val:.1f}{u_unit}"
            if self.settings["show_network"]:
                try:
                    ip = socket.gethostbyname(socket.gethostname())
                except:
                    ip = "Not connected"
                self.menu["Local IP"].title = f"{bold_labels['Local IP']}: {ip}"
            if self.settings["show_storage"]:
                self.menu["Storage"].title = f"{bold_labels['Storage']}: {self.get_storage_info().split(': ',1)[1]}"
            if self.settings["show_uptime"]:
                self.menu["Uptime"].title = f"{bold_labels['Uptime']}: {self.get_uptime().split(': ',1)[1]}"
            if self.settings["show_public_ip"]:
                self.menu["Public IP"].title = f"{bold_labels['Public IP']}: {self.public_ip}"
        except Exception as e:
            print(f"Error updating stats: {e}")

    def update_network_speeds(self):
        # Verkon nopeudet
        new = psutil.net_io_counters()
        self.down_speed = (new.bytes_recv - self.last_net_io.bytes_recv) / 3
        self.up_speed = (new.bytes_sent - self.last_net_io.bytes_sent) / 3
        self.last_net_io = new

    def format_network_speed(self, bps: float) -> tuple[str, float]:
        """Format network speed from bytes per second to appropriate unit
        
        Args:
            bps: Bytes per second
            
        Returns:
            Tuple of (unit string, converted value)
        """
        if bps < 1024:
            return "B/s", bps
        if bps < 1024*1024:
            return "KB/s", bps/1024
        return "MB/s", bps/(1024*1024)

    def get_storage_info(self) -> str:
        """Get formatted string with storage usage information"""
        try:
            total, used, free = shutil.disk_usage("/")
            total_gb, free_gb = total // 2**30, free // 2**30
            percent = (used / total) * 100
            bar_length = 5
            filled = int(percent / (100 / bar_length))
            bar = "█" * filled + "░" * (bar_length - filled)
            return f"Storage: {self.get_color_indicator(percent,86)}{bar} {free_gb}GB free of {total_gb}GB"
        except (OSError, PermissionError) as e:
            print(f"Error getting storage info: {e}")
            return "Storage: Error"

    def update_public_ip(self, _=None) -> None:
        """Update the public IP address by querying an external service"""
        if not self.settings["show_public_ip"]:
            return
        try:
            self.public_ip = requests.get('https://api.ipify.org', timeout=5).text
        except (requests.RequestException, requests.Timeout) as e:
            print(f"Failed to fetch public IP: {e}")
            self.public_ip = "Not available"

    def get_uptime(self):

        try:
            out = subprocess.check_output("uptime | awk '{print $3,$4}' | sed 's/,//g'", shell=True).decode().strip()
            return f"Uptime: {out}"
        except:
            return "Uptime: N/A"

    def check_clipboard(self, _=None):

        if not self.settings["show_clipboard"]:
            return
        try:
            content = subprocess.check_output("osascript -e 'the clipboard as text'", shell=True).decode().strip()
            if content and content != self.last_clipboard:
                self.last_clipboard = content
                self.clipboard_history.appendleft(content)
                self.update_clipboard_menu()
        except:
            pass

    def update_clipboard_menu(self):

        if not self.settings["show_clipboard"]:
            return
        try:
            for i in range(6):
                clip = self.menu["Clipboard History"][f"Clip {i+1}"]
                if i < len(self.clipboard_history):
                    c = self.clipboard_history[i]
                    d = c[:47] + "..." if len(c) > 50 else c
                    clip.title = f"Clip {i+1}: {d}"
                else:
                    clip.title = f"Clip {i+1}: (empty)"
                # Ensure callback is set
                clip.set_callback(self.copy_from_history)
        except Exception as e:
            print(f"Error updating clipboard menu: {e}")

    def format_time(self, seconds: int) -> str:
        """Format seconds into a human readable time string
        
        Args:
            seconds: Number of seconds to format
            
        Returns:
            Formatted time string in the format "Xh Ym" or "Ym"
        """
        if seconds == -1:
            return "Unknown"
        hours, minutes = divmod(seconds, 3600)[0], divmod(seconds, 3600)[1]//60
        return f"{hours}h {minutes}m" if hours else f"{minutes}m"

    def get_color_indicator(self, v, t):

        return "🔴 " if v >= t else "🟠 " if v >= t*0.7 else "🟢 "

    def get_battery_indicator(self, p):

        return "🪫" if p <= 10 else "🔋"

    @rumps.clicked("Clipboard History", "Clip 1")
    @rumps.clicked("Clipboard History", "Clip 2")
    @rumps.clicked("Clipboard History", "Clip 3")
    @rumps.clicked("Clipboard History", "Clip 4")
    @rumps.clicked("Clipboard History", "Clip 5")
    @rumps.clicked("Clipboard History", "Clip 6")
    def copy_from_history(self, sender):
        try:
            # Get the clip number before the colon (e.g., from "Clip 3: content" get "3")
            idx = int(sender.title.split(':')[0].split()[1]) - 1
            if idx < len(self.clipboard_history):
                clip_content = self.clipboard_history[idx]
                # Show preview of content (truncated if too long)
                preview = clip_content[:100] + "..." if len(clip_content) > 100 else clip_content
                # Bring app to front before showing dialog
                subprocess.run("osascript -e 'tell application \"System Events\" to set frontmost of process \"Python\" to true'", shell=True)
                # Show confirmation dialog
                response = rumps.alert(
                    title="Copy from Clipboard History?",
                    message=f"{preview}",
                    ok="Copy",
                    cancel="Cancel"
                )
                # If user clicked "Copy", proceed with copying
                if response:
                    # Encode the content in base64 to handle all special characters
                    import base64
                    encoded = base64.b64encode(clip_content.encode()).decode()
                    # Use base64 decode in AppleScript to set the clipboard
                    apple_script = f'''
                        set encodedText to "{encoded}"
                        set decodedText to do shell script "echo " & quoted form of encodedText & " | base64 -D"
                        set the clipboard to decodedText
                    '''
                    subprocess.run(['osascript', '-e', apple_script], shell=False)
        except Exception as e:
            print(f"Error copying from clipboard history: {e}")

    def quit(self, sender=None):

        self.save_settings()
        rumps.quit_application()

if __name__ == '__main__':

    SystemMonitorApp().run()