#!/usr/bin/env python3
"""
NetMind Setup Wizard — PyQt6 GUI installer
Build:  bash build.sh
Run:    sudo -E ./dist/NetMind-Setup
"""

import os
import sys
import pwd
import shutil
import tarfile
import threading
import subprocess
import queue
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QLineEdit, QProgressBar, QTextEdit, QFileDialog, QStackedWidget,
    QHBoxLayout, QVBoxLayout, QFrame,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor

# ─── Constants ────────────────────────────────────────────────────────────────
APP_VERSION  = "2.0"
DEFAULT_DIR  = "/opt/netmind"
LAUNCHER_BIN = "/usr/local/bin/netmind-launch"
TARBALL_NAME = "netmind-app.tar.gz"

# ─── Colours ──────────────────────────────────────────────────────────────────
BG      = "#0f1729"
BG2     = "#1a2540"
BG3     = "#1e2d4a"
ACCENT  = "#0066ff"
GREEN   = "#10b981"
RED     = "#ef4444"
YELLOW  = "#f59e0b"
TEXT    = "#e2e8f0"
MUTED   = "#94a3b8"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_resource(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

def is_root():
    return os.geteuid() == 0

def get_real_user():
    user = os.environ.get("SUDO_USER", "")
    if not user:
        uid_str = os.environ.get("PKEXEC_UID")
        if uid_str:
            try:
                user = pwd.getpwuid(int(uid_str)).pw_name
            except Exception:
                pass
    return user or os.environ.get("USER", "root")

def get_real_home():
    try:
        return pwd.getpwnam(get_real_user()).pw_dir
    except Exception:
        return os.path.expanduser("~")


# ─── Worker thread ────────────────────────────────────────────────────────────

class InstallWorker(QThread):
    log_line  = pyqtSignal(str, str)   # (message, level)
    progress  = pyqtSignal(int)
    step_changed = pyqtSignal(int, int, str)
    finished  = pyqtSignal(bool, str)

    def __init__(self, install_dir):
        super().__init__()
        self.install_dir = install_dir
        self.real_user   = get_real_user()
        self.real_home   = get_real_home()

    def log(self, msg, lvl="info"):
        self.log_line.emit(msg, lvl)

    def step(self, n, total, title):
        self.step_changed.emit(n, total, title)
        self.log(f"\n── Step {n}/{total}: {title}", "step")

    def run_cmd(self, cmd, shell=False, stream=True):
        try:
            proc = subprocess.Popen(
                cmd, shell=shell,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=os.environ.copy(),
            )
            lines = []
            if stream:
                for line in proc.stdout:
                    line = line.rstrip()
                    if line:
                        self.log(f"  {line}", "cmd")
                        lines.append(line)
            else:
                out, _ = proc.communicate()
                lines = out.splitlines()
            proc.wait()
            return proc.returncode, "\n".join(lines)
        except FileNotFoundError as e:
            self.log(f"  Command not found: {e}", "error")
            return 1, str(e)
        except Exception as e:
            self.log(f"  Error: {e}", "error")
            return 1, str(e)

    # ── Step 1 ────────────────────────────────────────────────────────────────
    def detect_distro(self):
        self.log("Detecting distribution...")
        distro = distro_like = pretty = ""
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    k, _, v = line.partition("=")
                    v = v.strip().strip('"').lower()
                    if k == "ID":            distro      = v
                    elif k == "ID_LIKE":     distro_like = v
                    elif k == "PRETTY_NAME": pretty      = v.title()
        except Exception:
            pass
        self.log(f"  Distro: {pretty or distro or 'unknown'}", "ok")
        apt_set    = {"ubuntu","debian","kali","linuxmint","pop"}
        dnf_set    = {"fedora","rhel","centos","rocky","alma"}
        pacman_set = {"arch","manjaro","endeavouros","garuda"}
        if distro in apt_set:           pkg = "apt"
        elif distro in dnf_set:         pkg = "dnf"
        elif distro in pacman_set:      pkg = "pacman"
        elif "debian" in distro_like or "ubuntu" in distro_like: pkg = "apt"
        elif "fedora" in distro_like or "rhel"   in distro_like: pkg = "dnf"
        elif "arch"   in distro_like:   pkg = "pacman"
        else:
            self.log("  Unknown distro — assuming apt", "warn")
            pkg = "apt"
        self.log(f"  Package manager: {pkg}", "ok")
        return pkg

    # ── Step 2 ────────────────────────────────────────────────────────────────
    def install_system_packages(self, pkg):
        self.log("Installing system packages...")
        apt_pkgs = (
            "python3 python3-pip python3-dev python3-venv "
            "python3-pyqt6 python3-pyqt6.qtsvg python3-pyaudio "
            "libgl1 libglib2.0-0 libxcb-xinerama0 libxcb-icccm4 libxcb-image0 "
            "libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xkb1 "
            "libxcb-cursor0 libxkbcommon-x11-0 libxkbcommon0 libegl1 libdbus-1-3 "
            "libpcap-dev libffi-dev libssl-dev "
            "net-tools iproute2 curl wget git ca-certificates gnupg "
            "portaudio19-dev policykit-1"
        ).split()
        dnf_pkgs = (
            "python3 python3-pip python3-devel python3-PyQt6 mesa-libGL glib2 "
            "libpcap-devel libffi-devel openssl-devel net-tools iproute curl wget "
            "git ca-certificates portaudio-devel polkit"
        ).split()
        pacman_pkgs = (
            "python python-pip python-pyqt6 mesa glib2 libpcap libffi openssl "
            "net-tools iproute2 curl wget git portaudio polkit"
        ).split()
        cmds = {
            "apt":    ["apt-get", "install", "-y", "-q", "--no-install-recommends"] + apt_pkgs,
            "dnf":    ["dnf", "install", "-y"] + dnf_pkgs,
            "pacman": ["pacman", "-Sy", "--noconfirm"] + pacman_pkgs,
        }
        if pkg == "apt":
            self.run_cmd(["apt-get", "update", "-qq"])
        code, _ = self.run_cmd(cmds.get(pkg, cmds["apt"]))
        if code == 0:
            self.log("  System packages installed", "ok")
        else:
            self.log("  Some packages failed — continuing", "warn")

    # ── Step 3 ────────────────────────────────────────────────────────────────
    def extract_app(self):
        self.log(f"Extracting application to {self.install_dir}...")
        tarball = get_resource(TARBALL_NAME)
        if not os.path.exists(tarball):
            raise FileNotFoundError(f"Bundled tarball not found: {tarball}")
        os.makedirs(self.install_dir, exist_ok=True)
        with tarfile.open(tarball, "r:gz") as tar:
            tar.extractall(self.install_dir)
        try:
            for root, dirs, files in os.walk(self.install_dir):
                for d in dirs:
                    try: shutil.chown(os.path.join(root, d), self.real_user, self.real_user)
                    except Exception: pass
                for fn in files:
                    try: shutil.chown(os.path.join(root, fn), self.real_user, self.real_user)
                    except Exception: pass
        except Exception as e:
            self.log(f"  chown: {e}", "warn")
        for fname in ("start.sh", "stop.sh", "netmind-launch.sh"):
            p = os.path.join(self.install_dir, fname)
            if os.path.exists(p):
                os.chmod(p, 0o755)
        has_bin = os.path.exists(os.path.join(self.install_dir, "NetMindDesktop"))
        has_py  = os.path.exists(os.path.join(self.install_dir, "NetMindDesktop.py"))
        if not has_bin and not has_py:
            raise RuntimeError("NetMindDesktop not found after extraction")
        self.log(f"  App files ready at {self.install_dir}", "ok")

    # ── Step 4 ────────────────────────────────────────────────────────────────
    def install_python_deps(self):
        self.log("Installing Python dependencies...")
        reqs = os.path.join(self.install_dir, "requirements.txt")
        if not os.path.exists(reqs):
            self.log("  requirements.txt not found — skipping", "warn")
            return
        flags = ["--quiet", "--no-warn-script-location"]
        code, _ = self.run_cmd(["pip3", "install"] + flags + ["-r", reqs])
        if code != 0:
            self.log("  Retrying with --break-system-packages...")
            self.run_cmd(["pip3", "install"] + flags +
                         ["--break-system-packages", "--ignore-installed", "-r", reqs])
        self.log("  Python packages installed", "ok")

    # ── Step 5 ────────────────────────────────────────────────────────────────
    def install_docker(self):
        code, _ = self.run_cmd(["docker", "--version"], stream=False)
        if code == 0:
            self.log("  Docker already installed", "ok")
        else:
            self.log("Installing Docker via convenience script...")
            self.run_cmd(["sh", "-c", "curl -fsSL https://get.docker.com | sh"])
            self.log("  Docker installed", "ok")
        self.run_cmd(["systemctl", "enable", "docker", "--now"])
        self.run_cmd(["usermod", "-aG", "docker", self.real_user])
        self.log("  Docker service enabled", "ok")

    # ── Step 6 ────────────────────────────────────────────────────────────────
    def _ollama_ok(self):
        if subprocess.run(["which", "ollama"], capture_output=True).returncode != 0:
            return False, "binary missing"
        lib = "/usr/local/lib/ollama"
        if os.path.isdir(lib):
            ignore_exts = {".txt", ".md"}
            ignore_pfx  = {"LICENSE", "README"}
            bins = [
                n for n in os.listdir(lib)
                if not any(n.endswith(e) for e in ignore_exts)
                and not any(n.upper().startswith(p) for p in ignore_pfx)
            ]
            if not bins:
                return False, "llama-server missing from lib dir"
        r = subprocess.run(["curl", "-sf", "http://localhost:11434/api/tags"],
                           capture_output=True, timeout=5)
        if r.returncode != 0:
            srv = subprocess.Popen(["ollama", "serve"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(6):
                    time.sleep(2)
                    if subprocess.run(["curl", "-sf", "http://localhost:11434/api/tags"],
                                      capture_output=True, timeout=3).returncode == 0:
                        break
            finally:
                srv.terminate()
            if subprocess.run(["curl", "-sf", "http://localhost:11434/api/tags"],
                               capture_output=True, timeout=3).returncode != 0:
                return False, "API unreachable"
        return True, "ok"

    def install_ollama(self):
        self.log("Checking Ollama...")
        ok, reason = self._ollama_ok()
        if ok:
            try:
                ver = subprocess.check_output(["ollama", "--version"], text=True, timeout=5).strip()
            except Exception:
                ver = "version unknown"
            self.log(f"  Ollama verified ({ver})", "ok")
        else:
            if subprocess.run(["which", "ollama"], capture_output=True).returncode == 0:
                self.log(f"  Ollama has silent problems ({reason}) — reinstalling", "warn")
                subprocess.run(["pkill", "-x", "ollama"], capture_output=True)
                time.sleep(2)
            else:
                self.log("  Ollama not found — installing", "info")
            self.run_cmd(["sh", "-c", "curl -fsSL https://ollama.com/install.sh | sh"])
            self.log("  Ollama installed", "ok")
        if subprocess.run(["curl", "-sf", "http://localhost:11434/api/tags"],
                           capture_output=True, timeout=5).returncode != 0:
            self.log("  Starting Ollama daemon...")
            subprocess.Popen(["ollama", "serve"],
                             stdout=open("/tmp/ollama-setup.log", "w"),
                             stderr=subprocess.STDOUT)
            time.sleep(5)
        self.log("  Waiting for Ollama API...")
        for _ in range(30):
            if subprocess.run(["curl", "-sf", "http://localhost:11434/api/tags"],
                               capture_output=True, timeout=3).returncode == 0:
                self.log("  Ollama API ready", "ok")
                break
            time.sleep(2)
        else:
            self.log("  Ollama slow to start — continuing", "warn")
        r = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        if "llama3.1" in r.stdout:
            self.log("  Llama 3.1 already downloaded", "ok")
        else:
            self.log("  Pulling Llama 3.1 (~4.9 GB — this takes a while)...")
            self.run_cmd(["ollama", "pull", "llama3.1"])
            self.log("  Llama 3.1 downloaded", "ok")

    # ── Step 7 ────────────────────────────────────────────────────────────────
    def configure_system(self):
        self.log("Configuring system...")
        try:
            with open("/proc/sys/net/ipv4/ip_forward", "w") as f:
                f.write("1")
            sysctl = "/etc/sysctl.conf"
            content = open(sysctl).read() if os.path.exists(sysctl) else ""
            if "net.ipv4.ip_forward=1" not in content:
                with open(sysctl, "a") as f:
                    f.write("\nnet.ipv4.ip_forward=1\n")
            self.log("  IP forwarding enabled", "ok")
        except Exception as e:
            self.log(f"  IP forwarding: {e}", "warn")
        try:
            r = subprocess.run(["iw", "dev"], capture_output=True, text=True)
            for line in r.stdout.splitlines():
                if "Interface" in line:
                    iface = line.split()[-1]
                    subprocess.run(["iw", "dev", iface, "set", "power_save", "off"],
                                    capture_output=True)
                    self.log(f"  Wi-Fi power-save disabled on {iface}", "ok")
                    break
        except FileNotFoundError:
            self.log("  iw not found — skipping Wi-Fi power-save", "warn")
        subprocess.run(
            ["sudo", "-u", self.real_user, "git", "config",
             "--global", "--add", "safe.directory", self.install_dir],
            capture_output=True,
        )

    # ── Step 8 ────────────────────────────────────────────────────────────────
    def install_desktop(self):
        self.log("Setting up desktop application...")
        icon_src = os.path.join(self.install_dir, "assets", "netmind.png")
        for size in ("256x256", "512x512"):
            d = f"/usr/share/icons/hicolor/{size}/apps"
            os.makedirs(d, exist_ok=True)
            if os.path.exists(icon_src):
                shutil.copy2(icon_src, os.path.join(d, "netmind.png"))
        subprocess.run(["gtk-update-icon-cache", "-f", "-t",
                         "/usr/share/icons/hicolor/"], capture_output=True)
        self.log("  Icon installed", "ok")

        real_user   = self.real_user
        real_home   = self.real_home
        install_dir = self.install_dir
        launcher = (
            "#!/bin/bash\n"
            "# NetMind launcher — runs as root via pkexec\n"
            f'INSTALL_DIR="{install_dir}"\n'
            'OBS_DIR="$INSTALL_DIR/observability"\n'
            "exec >> /tmp/netmind.log 2>&1\n"
            'echo "=== NetMind launch $(date) ==="\n\n'
            'export DISPLAY="${DISPLAY:-:0}"\n'
            f'export XAUTHORITY="${{XAUTHORITY:-{real_home}/.Xauthority}}"\n'
            "export QT_X11_NO_MITSHM=1\n\n"
            "for sp in /home/*/.local/lib/python*/site-packages; do\n"
            '  export PYTHONPATH="$sp:${PYTHONPATH}"\ndone\n\n'
            "docker info > /dev/null 2>&1 || {\n"
            "  systemctl start docker 2>/dev/null || service docker start 2>/dev/null || true\n"
            "  sleep 3\n}\n\n"
            'docker compose -f "$OBS_DIR/docker-compose.yml" down --remove-orphans 2>/dev/null || true\n'
            'docker compose -f "$OBS_DIR/docker-compose.yml" up -d 2>/dev/null || true\n\n'
            "for i in $(seq 1 15); do\n"
            "  curl -sf http://localhost:3000 > /dev/null 2>&1 && break; sleep 1\ndone\n\n"
            "curl -sf http://localhost:11434/api/tags > /dev/null 2>&1 || {\n"
            f'  su - {real_user} -c "nohup ollama serve > /tmp/ollama.log 2>&1 &" 2>/dev/null || true\n'
            "  sleep 3\n}\n\n"
            'cd "$INSTALL_DIR"\n'
            f'if [ -x "{install_dir}/NetMindDesktop" ]; then\n'
            f'  exec "{install_dir}/NetMindDesktop"\n'
            f'else\n'
            f'  exec python3 -B "{install_dir}/NetMindDesktop.py"\n'
            f'fi\n'
        )
        with open(LAUNCHER_BIN, "w") as f:
            f.write(launcher)
        os.chmod(LAUNCHER_BIN, 0o755)
        self.log("  Launcher installed", "ok")

        os.makedirs("/usr/share/polkit-1/actions", exist_ok=True)
        with open("/usr/share/polkit-1/actions/com.netmind.app.policy", "w") as f:
            f.write("""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="com.netmind.app.launch">
    <description>Run NetMind AI Network Manager</description>
    <message>NetMind needs administrator access to monitor and manage network traffic.</message>
    <icon_name>netmind</icon_name>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/local/bin/netmind-launch</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
</policyconfig>""")
        self.log("  Privilege policy installed", "ok")

        os.makedirs("/usr/share/applications", exist_ok=True)
        with open("/usr/share/applications/netmind.desktop", "w") as f:
            f.write("""\
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMind
GenericName=AI Network Manager
Comment=Intelligent bandwidth management and network monitoring powered by AI
Exec=pkexec /usr/local/bin/netmind-launch
Icon=netmind
Terminal=false
Categories=Network;System;Security;
Keywords=network;bandwidth;monitoring;ai;firewall;
StartupNotify=true
StartupWMClass=NetMindDesktop
""")
        os.chmod("/usr/share/applications/netmind.desktop", 0o644)
        subprocess.run(["update-desktop-database", "/usr/share/applications/"], capture_output=True)

        # Resolve desktop folder (respects localized names via xdg-user-dir)
        try:
            xdg = subprocess.check_output(
                ["sudo", "-u", real_user, "xdg-user-dir", "DESKTOP"],
                text=True, timeout=5
            ).strip()
            user_desktop = xdg if xdg and os.path.isdir(xdg) else os.path.join(real_home, "Desktop")
        except Exception:
            user_desktop = os.path.join(real_home, "Desktop")

        if os.path.isdir(user_desktop):
            shortcut = os.path.join(user_desktop, "NetMind.desktop")
            shutil.copy2("/usr/share/applications/netmind.desktop", shortcut)
            os.chmod(shortcut, 0o755)
            try: shutil.chown(shortcut, real_user, real_user)
            except Exception: pass
            subprocess.run(
                ["sudo", "-u", real_user, "gio", "set", shortcut,
                 "metadata::trusted", "true"],
                capture_output=True
            )
            self.log(f"  Desktop shortcut created at {shortcut}", "ok")
        else:
            self.log(f"  Desktop folder not found — skipping shortcut", "warn")
        self.log("  App menu entry created", "ok")

        # ── Uninstaller launcher & desktop entry ──────────────────────────────
        uninstaller_launcher = (
            "#!/bin/bash\n"
            "# NetMind uninstaller — runs as root via pkexec\n"
            f'export DISPLAY="${{DISPLAY:-:0}}"\n'
            f'export XAUTHORITY="${{XAUTHORITY:-{real_home}/.Xauthority}}"\n'
            "export QT_X11_NO_MITSHM=1\n"
            "for sp in /home/*/.local/lib/python*/site-packages; do\n"
            '  export PYTHONPATH="$sp:${PYTHONPATH}"\ndone\n'
            f'if [ -x "{install_dir}/uninstaller" ]; then\n'
            f'  exec "{install_dir}/uninstaller"\n'
            f'else\n'
            f'  exec python3 -B "{install_dir}/uninstaller.py"\n'
            f'fi\n'
        )
        with open("/usr/local/bin/netmind-uninstall", "w") as f:
            f.write(uninstaller_launcher)
        os.chmod("/usr/local/bin/netmind-uninstall", 0o755)

        os.makedirs("/usr/share/polkit-1/actions", exist_ok=True)
        with open("/usr/share/polkit-1/actions/com.netmind.uninstall.policy", "w") as f:
            f.write("""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE policyconfig PUBLIC
 "-//freedesktop//DTD PolicyKit Policy Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/PolicyKit/1/policyconfig.dtd">
<policyconfig>
  <action id="com.netmind.uninstall">
    <description>Uninstall NetMind AI Network Manager</description>
    <message>NetMind Uninstaller needs administrator access to remove application files.</message>
    <icon_name>netmind</icon_name>
    <defaults>
      <allow_any>auth_admin</allow_any>
      <allow_inactive>auth_admin</allow_inactive>
      <allow_active>auth_admin_keep</allow_active>
    </defaults>
    <annotate key="org.freedesktop.policykit.exec.path">/usr/local/bin/netmind-uninstall</annotate>
    <annotate key="org.freedesktop.policykit.exec.allow_gui">true</annotate>
  </action>
</policyconfig>""")

        with open("/usr/share/applications/netmind-uninstall.desktop", "w") as f:
            f.write("""\
[Desktop Entry]
Version=1.0
Type=Application
Name=NetMind Uninstaller
GenericName=Uninstall NetMind
Comment=Remove NetMind AI Network Manager from your system
Exec=pkexec /usr/local/bin/netmind-uninstall
Icon=netmind
Terminal=false
Categories=Network;System;
StartupNotify=true
""")
        os.chmod("/usr/share/applications/netmind-uninstall.desktop", 0o644)
        subprocess.run(["update-desktop-database", "/usr/share/applications/"], capture_output=True)
        self.log("  Uninstaller installed", "ok")

    # ── Step 9 ────────────────────────────────────────────────────────────────
    def health_check(self):
        self.log("\nRunning health check...")
        checks = [
            ("Python 3.10+",
             ["python3", "-c", "import sys; assert sys.version_info >= (3,10)"]),
            ("PyQt6",
             ["python3", "-c", "from PyQt6.QtWidgets import QApplication"]),
            ("Scapy",            ["python3", "-c", "import scapy"]),
            ("prometheus-client",["python3", "-c", "import prometheus_client"]),
            ("Docker",           ["docker", "--version"]),
            ("Docker Compose",   ["docker", "compose", "version"]),
            ("Ollama API",
             ["curl", "-sf", "http://localhost:11434/api/tags"]),
            ("NetMindDesktop",
             ["sh", "-c",
              f'test -x "{self.install_dir}/NetMindDesktop" || '
              f'test -f "{self.install_dir}/NetMindDesktop.py"']),
            ("Launcher",         ["test", "-x", LAUNCHER_BIN]),
            ("Desktop entry",
             ["test", "-f", "/usr/share/applications/netmind.desktop"]),
        ]
        passed = failed = 0
        for label, cmd in checks:
            r = subprocess.run(cmd, capture_output=True, timeout=15)
            if r.returncode == 0:
                self.log(f"  ✔ {label}", "ok")
                passed += 1
            else:
                self.log(f"  ✘ {label}", "warn")
                failed += 1
        self.log(f"\n  Results: {passed} passed  {failed} failed",
                 "ok" if failed == 0 else "warn")

    # ── Main ──────────────────────────────────────────────────────────────────
    def run(self):
        total = 9
        try:
            self.step(1, total, "Detecting Linux Distribution")
            pkg = self.detect_distro()
            self.progress.emit(8)

            self.step(2, total, "Installing System Packages")
            self.install_system_packages(pkg)
            self.progress.emit(20)

            self.step(3, total, "Installing NetMind Application Files")
            self.extract_app()
            self.progress.emit(32)

            self.step(4, total, "Installing Python Dependencies")
            self.install_python_deps()
            self.progress.emit(42)

            self.step(5, total, "Installing Docker")
            self.install_docker()
            self.progress.emit(55)

            self.step(6, total, "Installing & Verifying Ollama + Llama 3.1 AI Model")
            self.install_ollama()
            self.progress.emit(80)

            self.step(7, total, "System Configuration")
            self.configure_system()
            self.progress.emit(87)

            self.step(8, total, "Installing Desktop Application")
            self.install_desktop()
            self.progress.emit(95)

            self.step(9, total, "Final Health Check")
            self.health_check()
            self.progress.emit(100)

            self.finished.emit(True, "")
        except Exception as exc:
            import traceback
            self.log(f"\nFATAL: {exc}\n{traceback.format_exc()}", "error")
            self.finished.emit(False, str(exc))


# ─── Shared styles ────────────────────────────────────────────────────────────

def btn_style(bg=ACCENT, fg="white"):
    return f"""
        QPushButton {{
            background: {bg}; color: {fg};
            border: none; border-radius: 6px;
            padding: 9px 22px; font-size: 13px; font-weight: bold;
        }}
        QPushButton:hover {{ background: {_lighten(bg)}; }}
        QPushButton:disabled {{ background: {BG3}; color: {MUTED}; }}
    """

def sbtn_style():
    return f"""
        QPushButton {{
            background: {BG2}; color: {MUTED};
            border: none; border-radius: 6px;
            padding: 9px 18px; font-size: 13px;
        }}
        QPushButton:hover {{ background: {BG3}; color: {TEXT}; }}
    """

def _lighten(hex_color, amount=20):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, r + amount); g = min(255, g + amount); b = min(255, b + amount)
    return f"#{r:02x}{g:02x}{b:02x}"


# ─── Main window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    PAGE_WELCOME    = 0
    PAGE_CONFIGURE  = 1
    PAGE_INSTALLING = 2
    PAGE_FINISH     = 3

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NetMind {APP_VERSION} Setup")
        self.setFixedSize(700, 540)
        self.setStyleSheet(f"background: {BG}; color: {TEXT};")

        self._install_dir = DEFAULT_DIR
        self._success     = False
        self._error       = ""
        self._installing  = False

        # Header
        self._header_bar = QWidget(self)
        self._header_bar.setGeometry(0, 0, 700, 72)
        self._header_bar.setStyleSheet(f"background: {ACCENT};")
        self._header_title = QLabel("NetMind", self._header_bar)
        self._header_title.setGeometry(24, 8, 400, 32)
        self._header_title.setStyleSheet(f"color: white; font-size: 20px; font-weight: bold; background: transparent;")
        self._header_sub = QLabel("", self._header_bar)
        self._header_sub.setGeometry(24, 44, 500, 20)
        self._header_sub.setStyleSheet(f"color: #cce0ff; font-size: 11px; background: transparent;")
        ver = QLabel(APP_VERSION, self._header_bar)
        ver.setGeometry(650, 8, 40, 20)
        ver.setStyleSheet(f"color: #8ab4f8; font-size: 10px; background: transparent;")

        # Pages
        self._stack = QStackedWidget(self)
        self._stack.setGeometry(0, 72, 700, 468)
        self._stack.setStyleSheet(f"background: {BG};")

        self._stack.addWidget(self._build_welcome())
        self._stack.addWidget(self._build_configure())
        self._stack.addWidget(self._build_installing())
        self._stack.addWidget(self._build_finish_placeholder())

        self._goto(self.PAGE_WELCOME)

    def closeEvent(self, event):
        if self._installing:
            event.ignore()
        else:
            event.accept()

    def _goto(self, page, subtitle=""):
        subtitles = [
            "Welcome to the NetMind Installer",
            "Installation Options",
            "Installing NetMind...",
            "Installation Complete" if self._success else "Installation Failed",
        ]
        self._header_sub.setText(subtitle or subtitles[page])
        self._stack.setCurrentIndex(page)

    # ── Page helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _label(parent, text, size=11, bold=False, color=TEXT, wrap=False):
        lbl = QLabel(text, parent)
        weight = "bold" if bold else "normal"
        lbl.setStyleSheet(f"color: {color}; font-size: {size}px; font-weight: {weight}; background: transparent;")
        if wrap:
            lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def _make_btn(text, bg=ACCENT, fg="white", handler=None):
        b = QPushButton(text)
        b.setStyleSheet(btn_style(bg, fg))
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if handler:
            b.clicked.connect(handler)
        return b

    @staticmethod
    def _make_sbtn(text, handler=None):
        b = QPushButton(text)
        b.setStyleSheet(sbtn_style())
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if handler:
            b.clicked.connect(handler)
        return b

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 1 — WELCOME
    # ─────────────────────────────────────────────────────────────────────────
    def _build_welcome(self):
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        title = self._label(w, "Welcome to NetMind Setup", 18, True)
        title.setGeometry(40, 24, 620, 36)

        desc = (
            "This wizard installs NetMind — an AI-powered network bandwidth\n"
            "manager — on your Linux system.\n\n"
            "What will be installed:\n"
            "  •  NetMind desktop application\n"
            "  •  Ollama + Llama 3.1 AI model  (~4.9 GB)\n"
            "  •  Docker  (Prometheus + Grafana observability)\n"
            "  •  Python dependencies\n\n"
            "Requirements:\n"
            "  •  Active internet connection\n"
            "  •  ~8 GB free disk space\n"
            "  •  Administrator (root) privileges"
        )
        desc_lbl = self._label(w, desc, 11, color=MUTED)
        desc_lbl.setGeometry(40, 68, 620, 260)

        if not is_root():
            warn_lbl = self._label(w, "⚠  Run with:  sudo -E ./NetMind-Setup", 11, True, YELLOW)
            warn_lbl.setGeometry(40, 330, 620, 24)

        btn_cancel = self._make_sbtn("Cancel", self.close)
        state = True if is_root() else False
        btn_next = self._make_btn("Next  →", handler=lambda: self._goto(self.PAGE_CONFIGURE))
        btn_next.setEnabled(state)

        btn_row = QWidget(w)
        btn_row.setGeometry(0, 402, 700, 56)
        btn_row.setStyleSheet(f"background: {BG};")
        lay = QHBoxLayout(btn_row)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.addStretch()
        lay.addWidget(btn_cancel)
        lay.addWidget(btn_next)
        return w

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 2 — CONFIGURE
    # ─────────────────────────────────────────────────────────────────────────
    def _build_configure(self):
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        self._label(w, "Choose Installation Folder", 18, True).setGeometry(40, 24, 620, 36)
        self._label(w, "NetMind will be installed to the folder below.", 11, color=MUTED
                    ).setGeometry(40, 68, 620, 24)
        self._label(w, "Installation directory:", 11, True).setGeometry(40, 116, 200, 22)

        row = QWidget(w)
        row.setGeometry(40, 144, 620, 44)
        row.setStyleSheet(f"background: {BG3}; border-radius: 6px;")
        rlay = QHBoxLayout(row)
        rlay.setContentsMargins(10, 0, 6, 0)
        self._dir_entry = QLineEdit(self._install_dir)
        self._dir_entry.setStyleSheet(
            f"background: transparent; color: {TEXT}; border: none; font-size: 12px; font-family: monospace;"
        )
        self._dir_entry.textChanged.connect(lambda v: setattr(self, "_install_dir", v))
        rlay.addWidget(self._dir_entry)
        browse = QPushButton("Browse")
        browse.setStyleSheet(
            f"background: {BG2}; color: {TEXT}; border: none; border-radius: 4px; padding: 6px 12px;"
        )
        browse.setCursor(Qt.CursorShape.PointingHandCursor)
        browse.clicked.connect(self._browse)
        rlay.addWidget(browse)

        note = (
            "Disk space required:  ~8 GB\n"
            "(The Llama 3.1 model is ~4.9 GB and lives in /usr/share/ollama,\n"
            "not inside the installation folder.)"
        )
        self._label(w, note, 10, color=MUTED).setGeometry(40, 206, 620, 60)

        btn_cancel = self._make_sbtn("Cancel", self.close)
        btn_back   = self._make_sbtn("← Back", lambda: self._goto(self.PAGE_WELCOME))
        btn_install = self._make_btn("Install  ▶", bg=GREEN,
                                     handler=self._start_install)

        btn_row = QWidget(w)
        btn_row.setGeometry(0, 402, 700, 56)
        btn_row.setStyleSheet(f"background: {BG};")
        lay = QHBoxLayout(btn_row)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.addStretch()
        lay.addWidget(btn_cancel)
        lay.addWidget(btn_back)
        lay.addWidget(btn_install)
        return w

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Choose folder", "/opt")
        if d:
            self._install_dir = d
            self._dir_entry.setText(d)

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 3 — INSTALLING
    # ─────────────────────────────────────────────────────────────────────────
    def _build_installing(self):
        w = QWidget()
        w.setStyleSheet(f"background: {BG};")

        self._step_lbl = QLabel("Starting installation...", w)
        self._step_lbl.setGeometry(40, 12, 620, 26)
        self._step_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: bold; background: transparent;"
        )

        self._prog = QProgressBar(w)
        self._prog.setGeometry(40, 44, 620, 10)
        self._prog.setRange(0, 100)
        self._prog.setValue(0)
        self._prog.setTextVisible(False)
        self._prog.setStyleSheet(f"""
            QProgressBar {{ background: {BG3}; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
        """)

        self._log_box = QTextEdit(w)
        self._log_box.setGeometry(40, 62, 620, 312)
        self._log_box.setReadOnly(True)
        self._log_box.setStyleSheet(
            f"background: #060e1c; color: #9bb5cc; border: none;"
            f"font-family: monospace; font-size: 9pt;"
        )

        self._fin_btn = QPushButton("Finish  →", w)
        self._fin_btn.setGeometry(548, 398, 114, 42)
        self._fin_btn.setEnabled(False)
        self._fin_btn.setStyleSheet(btn_style(BG3))
        self._fin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fin_btn.clicked.connect(self._show_finish)
        return w

    def _append_log(self, msg, lvl):
        colors = {
            "ok":   GREEN,  "warn":  YELLOW, "error": RED,
            "step": ACCENT, "cmd":   "#4a6070", "info": TEXT,
        }
        color = colors.get(lvl, TEXT)
        bold  = "font-weight: bold;" if lvl in ("step", "ok", "error") else ""
        self._log_box.append(
            f'<span style="color:{color};{bold}">{msg}</span>'
        )
        self._log_box.moveCursor(QTextCursor.MoveOperation.End)

    def _start_install(self):
        self._installing = True
        self._goto(self.PAGE_INSTALLING)
        self._worker = InstallWorker(self._install_dir)
        self._worker.log_line.connect(self._append_log)
        self._worker.progress.connect(self._prog.setValue)
        self._worker.step_changed.connect(
            lambda n, t, title: self._step_lbl.setText(f"Step {n}/{t}: {title}")
        )
        self._worker.finished.connect(self._on_install_done)
        self._worker.start()

    def _on_install_done(self, success, error):
        self._installing = False
        self._success    = success
        self._error      = error
        self._prog.setValue(100)
        if success:
            self._step_lbl.setText("✔  Installation complete!")
            self._step_lbl.setStyleSheet(
                f"color: {GREEN}; font-size: 13px; font-weight: bold; background: transparent;"
            )
            self._fin_btn.setEnabled(True)
            self._fin_btn.setStyleSheet(btn_style(GREEN))
        else:
            self._step_lbl.setText("✘  Installation failed")
            self._step_lbl.setStyleSheet(
                f"color: {RED}; font-size: 13px; font-weight: bold; background: transparent;"
            )
            self._fin_btn.setEnabled(True)
            self._fin_btn.setStyleSheet(btn_style(RED))
            self._fin_btn.setText("Close")

    # ─────────────────────────────────────────────────────────────────────────
    # PAGE 4 — FINISH
    # ─────────────────────────────────────────────────────────────────────────
    def _build_finish_placeholder(self):
        self._finish_widget = QWidget()
        self._finish_widget.setStyleSheet(f"background: {BG};")
        return self._finish_widget

    def _show_finish(self):
        # Rebuild the finish page with real success/error state
        w = self._finish_widget
        # Clear
        for child in w.children():
            if isinstance(child, QWidget):
                child.deleteLater()

        sub = "Installation Complete" if self._success else "Installation Failed"
        self._header_sub.setText(sub)

        if self._success:
            title_lbl = self._label(w, "✔  NetMind is ready!", 18, True, GREEN)
            title_lbl.setGeometry(40, 24, 620, 36)
            steps = (
                "What to do next:\n\n"
                "  1.  Double-click  NetMind  on your Desktop\n"
                "      (or search it in your application menu)\n\n"
                "  2.  Enter your password when prompted\n\n"
                "  3.  Click  Initialize  to scan your network\n\n"
                "  4.  Click  ▶ Start  to begin monitoring\n\n"
                "  5.  Open  http://localhost:3000  for Grafana charts\n\n"
                "  6.  Sign in with your NetMind account when prompted"
            )
            self._label(w, steps, 11, color=MUTED).setGeometry(40, 72, 620, 280)
        else:
            title_lbl = self._label(w, "✘  Installation failed", 18, True, RED)
            title_lbl.setGeometry(40, 24, 620, 36)
            err_lbl = self._label(w, f"Error: {self._error}", 10, color=YELLOW, wrap=True)
            err_lbl.setGeometry(40, 72, 620, 60)
            hint = self._label(w, "Check the log for details.\nRe-run with:  sudo -E ./NetMind-Setup",
                               11, color=MUTED)
            hint.setGeometry(40, 140, 620, 50)

        btn_row = QWidget(w)
        btn_row.setGeometry(0, 402, 700, 56)
        btn_row.setStyleSheet(f"background: {BG};")
        lay = QHBoxLayout(btn_row)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.addStretch()
        lay.addWidget(self._make_sbtn("Close", self.close))
        if self._success:
            lay.addWidget(self._make_btn("Launch NetMind Now", handler=self._launch_now))

        btn_row.show()
        self._goto(self.PAGE_FINISH, sub)

    def _launch_now(self):
        real_home = get_real_home()
        env = os.environ.copy()
        env["DISPLAY"]    = os.environ.get("DISPLAY", ":0")
        env["XAUTHORITY"] = os.environ.get("XAUTHORITY", real_home + "/.Xauthority")
        subprocess.Popen(
            ["/usr/local/bin/netmind-launch"],
            start_new_session=True,
            env=env,
        )
        self.close()


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"

    if not is_root():
        print("[NetMind Setup] Root required — re-launching with pkexec ...")
        _dpy   = os.environ.get("DISPLAY", ":0")
        _xauth = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
        # pkexec shows a GUI password dialog — works when double-clicked
        try:
            os.execvp("pkexec", [
                "pkexec", "env",
                f"DISPLAY={_dpy}",
                f"XAUTHORITY={_xauth}",
                sys.executable,
            ] + sys.argv[1:])
        except Exception:
            pass
        # Fallback: sudo (only works from a terminal)
        try:
            os.execvp("sudo", ["sudo", "-E", sys.executable] + sys.argv)
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,          QColor(BG))
    pal.setColor(QPalette.ColorRole.WindowText,      QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Base,            QColor(BG2))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(BG3))
    pal.setColor(QPalette.ColorRole.Text,            QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Button,          QColor(BG2))
    pal.setColor(QPalette.ColorRole.ButtonText,      QColor(TEXT))
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(ACCENT))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())
