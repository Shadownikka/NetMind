#!/usr/bin/env python3
"""
NetMind Uninstall Wizard — PyQt6 GUI uninstaller
Run:  pkexec /usr/local/bin/netmind-uninstall
"""

import os
import sys
import pwd
import shutil
import subprocess
import time

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QTextEdit, QStackedWidget, QHBoxLayout, QVBoxLayout, QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCursor

APP_VERSION  = "2.1.10"
INSTALL_DIR  = "/opt/netmind"
LAUNCHER_BIN = "/usr/local/bin/netmind-launch"
UNLAUNCHER   = "/usr/local/bin/netmind-uninstall"
POLKIT_FILE  = "/usr/share/polkit-1/actions/com.netmind.app.policy"
POLKIT_UN    = "/usr/share/polkit-1/actions/com.netmind.uninstall.policy"
DESKTOP_SYS  = "/usr/share/applications/netmind.desktop"
DESKTOP_UN   = "/usr/share/applications/netmind-uninstall.desktop"
ICON_DIRS    = [
    "/usr/share/icons/hicolor/256x256/apps/netmind.png",
    "/usr/share/icons/hicolor/512x512/apps/netmind.png",
]
SAVED_DATA   = "/root/.netmind"
LOCK_FILE    = "/tmp/netmind-app.lock"
PROFILE_FILE = "/root/.netmind_profile.json"

BG      = "#0f1729"
BG2     = "#1a2540"
BG3     = "#1e2d4a"
ACCENT  = "#0066ff"
GREEN   = "#10b981"
RED     = "#ef4444"
YELLOW  = "#f59e0b"
TEXT    = "#e2e8f0"
MUTED   = "#94a3b8"


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

def _lighten(hex_color, amount=20):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = min(255, r + amount); g = min(255, g + amount); b = min(255, b + amount)
    return f"#{r:02x}{g:02x}{b:02x}"


class UninstallWorker(QThread):
    log_line = pyqtSignal(str, str)
    finished = pyqtSignal(bool, str)

    def __init__(self, opts):
        super().__init__()
        self.opts      = opts
        self.real_user = get_real_user()
        self.real_home = get_real_home()

    def log(self, msg, lvl="info"):
        self.log_line.emit(msg, lvl)

    def _rm(self, path):
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
            self.log(f"  Removed  {path}", "ok")
        elif os.path.exists(path):
            try:
                os.remove(path)
                self.log(f"  Removed  {path}", "ok")
            except Exception as e:
                self.log(f"  Skip {path}: {e}", "warn")
        else:
            self.log(f"  Not found (already gone): {path}", "warn")

    def _run(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, env=os.environ.copy(),
            )
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self.log(f"  {line}", "cmd")
            proc.wait()
            return proc.returncode
        except Exception as e:
            self.log(f"  Error: {e}", "error")
            return 1

    def run(self):
        try:
            self.log("\n── Stopping NetMind processes...", "step")
            subprocess.run(["pkill", "-f", "NetMindDesktop"], capture_output=True)
            subprocess.run(["pkill", "-f", "netmind-launch"],  capture_output=True)
            time.sleep(1)
            self.log("  Processes stopped", "ok")

            self.log("\n── Removing observability stack...", "step")
            obs = os.path.join(INSTALL_DIR, "observability", "docker-compose.yml")
            if os.path.exists(obs):
                self._run(["docker", "compose", "-f", obs, "down",
                           "--remove-orphans", "--volumes"])
            self.log("  Observability stack removed", "ok")

            self.log("\n── Removing application files...", "step")
            self._rm(INSTALL_DIR)

            self.log("\n── Removing system files...", "step")
            self._rm(LAUNCHER_BIN)
            self._rm(UNLAUNCHER)
            self._rm(POLKIT_FILE)
            self._rm(POLKIT_UN)
            try:
                os.remove(LOCK_FILE)
            except Exception:
                pass

            self.log("\n── Removing desktop entries and icons...", "step")
            self._rm(DESKTOP_SYS)
            self._rm(DESKTOP_UN)
            for icon in ICON_DIRS:
                self._rm(icon)
            try:
                xdg = subprocess.check_output(
                    ["sudo", "-u", self.real_user, "xdg-user-dir", "DESKTOP"],
                    text=True, timeout=5
                ).strip()
                user_desktop = xdg if xdg and os.path.isdir(xdg) else \
                               os.path.join(self.real_home, "Desktop")
            except Exception:
                user_desktop = os.path.join(self.real_home, "Desktop")
            for name in ("NetMind.desktop", "netmind.desktop", "NetMind-Uninstall.desktop"):
                self._rm(os.path.join(user_desktop, name))
            subprocess.run(["gtk-update-icon-cache", "-f", "-t",
                            "/usr/share/icons/hicolor/"], capture_output=True)
            subprocess.run(["update-desktop-database",
                            "/usr/share/applications/"], capture_output=True)

            if self.opts.get("remove_data"):
                self.log("\n── Removing saved account data...", "step")
                self._rm(SAVED_DATA)
                self._rm(PROFILE_FILE)

            if self.opts.get("remove_ollama"):
                self.log("\n── Removing Ollama and AI models...", "step")
                subprocess.run(["pkill", "-x", "ollama"], capture_output=True)
                time.sleep(1)
                self._run(["sh", "-c",
                           "curl -fsSL https://ollama.com/install.sh | OLLAMA_UNINSTALL=1 sh"])
                for d in ("/usr/local/lib/ollama", "/usr/share/ollama",
                          os.path.join(self.real_home, ".ollama")):
                    self._rm(d)
                self.log("  Ollama removed", "ok")

            if self.opts.get("remove_docker"):
                self.log("\n── Removing Docker...", "step")
                self._run(["apt-get", "remove", "-y", "--purge",
                           "docker-ce", "docker-ce-cli", "containerd.io",
                           "docker-buildx-plugin", "docker-compose-plugin"])
                self._rm("/var/lib/docker")
                self._rm("/etc/docker")
                self.log("  Docker removed", "ok")

            self.finished.emit(True, "")

        except Exception as exc:
            import traceback
            self.log(f"\nFATAL: {exc}\n{traceback.format_exc()}", "error")
            self.finished.emit(False, str(exc))


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


class MainWindow(QMainWindow):
    PAGE_CONFIRM      = 0
    PAGE_UNINSTALLING = 1
    PAGE_DONE         = 2

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"NetMind {APP_VERSION} Uninstaller")
        self.setFixedSize(700, 540)
        self.setStyleSheet(f"background: {BG}; color: {TEXT};")
        self._success      = False
        self._error        = ""
        self._uninstalling = False

        self._header_bar = QWidget(self)
        self._header_bar.setGeometry(0, 0, 700, 72)
        self._header_bar.setStyleSheet(f"background: {RED};")
        lbl = QLabel("NetMind Uninstaller", self._header_bar)
        lbl.setGeometry(24, 8, 500, 32)
        lbl.setStyleSheet("color: white; font-size: 20px; font-weight: bold; background: transparent;")
        self._header_sub = QLabel("", self._header_bar)
        self._header_sub.setGeometry(24, 44, 500, 20)
        self._header_sub.setStyleSheet("color: #ffcccc; font-size: 11px; background: transparent;")
        QLabel(APP_VERSION, self._header_bar).setGeometry(650, 8, 40, 20)

        self._stack = QStackedWidget(self)
        self._stack.setGeometry(0, 72, 700, 468)
        self._stack.setStyleSheet(f"background: {BG};")
        self._stack.addWidget(self._build_confirm())
        self._stack.addWidget(self._build_uninstalling())
        self._stack.addWidget(self._build_done_placeholder())
        self._goto(self.PAGE_CONFIRM)

    def closeEvent(self, event):
        event.ignore() if self._uninstalling else event.accept()

    def _goto(self, page, subtitle=""):
        subs = [
            "Remove NetMind from your system",
            "Uninstalling NetMind...",
            "Uninstall Complete" if self._success else "Uninstall Failed",
        ]
        self._header_sub.setText(subtitle or subs[page])
        self._stack.setCurrentIndex(page)

    @staticmethod
    def _lbl(parent, text, size=11, bold=False, color=TEXT, wrap=False):
        l = QLabel(text, parent)
        l.setStyleSheet(
            f"color: {color}; font-size: {size}px; "
            f"font-weight: {'bold' if bold else 'normal'}; background: transparent;"
        )
        if wrap: l.setWordWrap(True)
        return l

    @staticmethod
    def _btn(text, bg=ACCENT, fg="white", handler=None):
        b = QPushButton(text)
        b.setStyleSheet(btn_style(bg, fg))
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if handler: b.clicked.connect(handler)
        return b

    @staticmethod
    def _sbtn(text, handler=None):
        b = QPushButton(text)
        b.setStyleSheet(sbtn_style())
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        if handler: b.clicked.connect(handler)
        return b

    def _build_confirm(self):
        w = QWidget(); w.setStyleSheet(f"background: {BG};")
        self._lbl(w, "Uninstall NetMind", 18, True, RED).setGeometry(40, 24, 620, 36)
        self._lbl(w, "The following will be permanently removed from your system:",
                  11, color=MUTED).setGeometry(40, 68, 620, 22)
        self._lbl(w,
            "  •  NetMind application  (/opt/netmind)\n"
            "  •  Launch scripts and polkit policy\n"
            "  •  Desktop shortcuts and icons\n"
            "  •  Grafana / Prometheus observability stack",
            11, color=TEXT).setGeometry(40, 98, 620, 88)

        sep = QWidget(w); sep.setGeometry(40, 192, 620, 1)
        sep.setStyleSheet(f"background: {BG3};")
        self._lbl(w, "Optional removals:", 11, True).setGeometry(40, 204, 200, 22)

        def chk(text, y):
            c = QCheckBox(text, w)
            c.setGeometry(40, y, 560, 26)
            c.setStyleSheet(f"color: {MUTED}; font-size: 11px; background: transparent;")
            return c

        self._chk_data   = chk("Remove saved account data  (/root/.netmind  +  profile)", 234)
        self._chk_ollama = chk("Remove Ollama and Llama 3.1 AI model  (~4.9 GB freed)", 264)
        self._chk_docker = chk("Remove Docker and all containers", 294)
        self._lbl(w, "⚠  This action cannot be undone.", 11, True, YELLOW
                  ).setGeometry(40, 334, 620, 22)

        btn_row = QWidget(w); btn_row.setGeometry(0, 402, 700, 56)
        btn_row.setStyleSheet(f"background: {BG};")
        lay = QHBoxLayout(btn_row); lay.setContentsMargins(20, 8, 20, 8)
        lay.addStretch()
        lay.addWidget(self._sbtn("Cancel", self.close))
        lay.addWidget(self._btn("Uninstall  ▶", bg=RED, handler=self._start_uninstall))
        return w

    def _build_uninstalling(self):
        w = QWidget(); w.setStyleSheet(f"background: {BG};")
        self._step_lbl = QLabel("Removing NetMind...", w)
        self._step_lbl.setGeometry(40, 12, 620, 26)
        self._step_lbl.setStyleSheet(
            f"color: {TEXT}; font-size: 13px; font-weight: bold; background: transparent;"
        )
        self._log_box = QTextEdit(w)
        self._log_box.setGeometry(40, 46, 620, 332)
        self._log_box.setReadOnly(True)
        self._log_box.setStyleSheet(
            f"background: #060e1c; color: #9bb5cc; border: none; "
            "font-family: monospace; font-size: 9pt;"
        )
        self._fin_btn = QPushButton("Close  →", w)
        self._fin_btn.setGeometry(548, 398, 114, 42)
        self._fin_btn.setEnabled(False)
        self._fin_btn.setStyleSheet(btn_style(BG3))
        self._fin_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._fin_btn.clicked.connect(self._show_done)
        return w

    def _append_log(self, msg, lvl):
        colors = {"ok": GREEN, "warn": YELLOW, "error": RED,
                  "step": ACCENT, "cmd": "#4a6070", "info": TEXT}
        color = colors.get(lvl, TEXT)
        bold  = "font-weight: bold;" if lvl in ("step", "ok", "error") else ""
        self._log_box.append(f'<span style="color:{color};{bold}">{msg}</span>')
        self._log_box.moveCursor(QTextCursor.MoveOperation.End)

    def _start_uninstall(self):
        self._uninstalling = True
        opts = {
            "remove_data":   self._chk_data.isChecked(),
            "remove_ollama": self._chk_ollama.isChecked(),
            "remove_docker": self._chk_docker.isChecked(),
        }
        self._goto(self.PAGE_UNINSTALLING)
        self._worker = UninstallWorker(opts)
        self._worker.log_line.connect(self._append_log)
        self._worker.finished.connect(self._on_done)
        self._worker.start()

    def _on_done(self, success, error):
        self._uninstalling = False
        self._success = success
        self._error   = error
        if success:
            self._step_lbl.setText("✔  NetMind has been removed")
            self._step_lbl.setStyleSheet(
                f"color: {GREEN}; font-size: 13px; font-weight: bold; background: transparent;"
            )
        else:
            self._step_lbl.setText("✘  Uninstall encountered errors")
            self._step_lbl.setStyleSheet(
                f"color: {RED}; font-size: 13px; font-weight: bold; background: transparent;"
            )
        self._fin_btn.setEnabled(True)
        self._fin_btn.setStyleSheet(btn_style(GREEN if success else RED))

    def _build_done_placeholder(self):
        self._done_widget = QWidget()
        self._done_widget.setStyleSheet(f"background: {BG};")
        return self._done_widget

    def _show_done(self):
        w = self._done_widget
        for child in w.children():
            if isinstance(child, QWidget):
                child.deleteLater()
        sub = "Uninstall Complete" if self._success else "Uninstall Failed"
        self._header_sub.setText(sub)
        if self._success:
            self._lbl(w, "✔  NetMind has been removed", 18, True, GREEN
                      ).setGeometry(40, 24, 620, 36)
            self._lbl(w,
                "NetMind has been successfully uninstalled.\n\n"
                "  •  Application files removed\n"
                "  •  System shortcuts and icons removed\n"
                "  •  Observability stack stopped and removed\n\n"
                "Thank you for using NetMind.",
                11, color=MUTED).setGeometry(40, 72, 620, 200)
        else:
            self._lbl(w, "✘  Some items could not be removed", 18, True, RED
                      ).setGeometry(40, 24, 620, 36)
            self._lbl(w, f"Error: {self._error}", 10, color=YELLOW, wrap=True
                      ).setGeometry(40, 72, 620, 60)
            self._lbl(w,
                "Check the log for details. You may need to remove\n"
                "remaining files manually.",
                11, color=MUTED).setGeometry(40, 140, 620, 50)

        btn_row = QWidget(w); btn_row.setGeometry(0, 402, 700, 56)
        btn_row.setStyleSheet(f"background: {BG};")
        lay = QHBoxLayout(btn_row); lay.setContentsMargins(20, 8, 20, 8)
        lay.addStretch()
        lay.addWidget(self._sbtn("Close", self.close))
        btn_row.show()
        self._goto(self.PAGE_DONE, sub)


if __name__ == "__main__":
    if not os.environ.get("DISPLAY"):
        os.environ["DISPLAY"] = ":0"
    if not is_root():
        print("[NetMind Uninstaller] Root required — re-launching with pkexec ...")
        _dpy   = os.environ.get("DISPLAY", ":0")
        _xauth = os.environ.get("XAUTHORITY", os.path.expanduser("~/.Xauthority"))
        try:
            os.execvp("pkexec", ["pkexec", "env",
                                  f"DISPLAY={_dpy}", f"XAUTHORITY={_xauth}",
                                  sys.executable] + sys.argv[1:])
        except Exception:
            pass
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
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(RED))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("white"))
    app.setPalette(pal)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
