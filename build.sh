#!/bin/bash
# Build NetMind-Setup single-file executable with PyInstaller
# Usage: bash build.sh
# Output: dist/NetMind-Setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARBALL="$SCRIPT_DIR/netmind-app.tar.gz"
INSTALLER="$SCRIPT_DIR/installer.py"
PROTECT="$SCRIPT_DIR/cython_protect.sh"
PROTECTED_DIR="/tmp/netmind-protected"

# ── Preflight checks ──────────────────────────────────────────────────────────
[[ -f "$INSTALLER" ]] || { echo "ERROR: installer.py not found at $INSTALLER"; exit 1; }
[[ -f "$PROTECT"   ]] || { echo "ERROR: cython_protect.sh not found at $PROTECT"; exit 1; }
[[ -d "/opt/netmind" ]] || { echo "ERROR: /opt/netmind not found — app source must exist"; exit 1; }

# ── Cython-protect source ─────────────────────────────────────────────────────
bash "$PROTECT"

# ── Create tarball from protected copy ───────────────────────────────────────
echo "Creating tarball from protected source..."
tar -czf "$TARBALL" -C "$PROTECTED_DIR" .
echo "  Tarball: $(du -sh "$TARBALL" | cut -f1)  →  $TARBALL"

# ── Install PyInstaller if needed ─────────────────────────────────────────────
if ! python3 -c "import PyInstaller" 2>/dev/null; then
  echo "Installing PyInstaller..."
  pip3 install pyinstaller --quiet --break-system-packages 2>/dev/null || \
    pip3 install pyinstaller --quiet
fi

# ── Clean previous build ──────────────────────────────────────────────────────
rm -rf "$SCRIPT_DIR/dist" "$SCRIPT_DIR/build" "$SCRIPT_DIR/NetMind-Setup.spec" 2>/dev/null || true

# ── Build ─────────────────────────────────────────────────────────────────────
echo "Building NetMind-Setup..."
pyinstaller \
  --onefile \
  --name "NetMind-Setup" \
  --add-data "$TARBALL:." \
  --hidden-import tkinter \
  --hidden-import tkinter.ttk \
  --hidden-import tkinter.scrolledtext \
  --hidden-import tkinter.filedialog \
  --strip \
  --clean \
  "$INSTALLER"

# ── Result ────────────────────────────────────────────────────────────────────
EXE="$SCRIPT_DIR/dist/NetMind-Setup"
if [[ -f "$EXE" ]]; then
  chmod +x "$EXE"
  SIZE=$(du -sh "$EXE" | cut -f1)
  echo ""
  echo "  ✔  Build complete: $EXE  ($SIZE)"
  echo ""
  echo "  Distribute the single file: dist/NetMind-Setup"
  echo "  Users run it with:          sudo -E ./NetMind-Setup"
else
  echo "ERROR: Build failed — dist/NetMind-Setup not found."
  exit 1
fi
