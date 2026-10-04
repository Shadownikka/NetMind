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
UNINSTALLER_SRC="/opt/netmind/uninstaller.py"
BUILD_WORK="/tmp/netmind-pyi-build"
BUILD_DIST="/tmp/netmind-pyi-dist"

# ── Preflight checks ──────────────────────────────────────────────────────────
[[ -f "$INSTALLER"       ]] || { echo "ERROR: installer.py not found at $INSTALLER"; exit 1; }
[[ -f "$PROTECT"         ]] || { echo "ERROR: cython_protect.sh not found at $PROTECT"; exit 1; }
[[ -d "/opt/netmind"     ]] || { echo "ERROR: /opt/netmind not found — app source must exist"; exit 1; }
[[ -f "$UNINSTALLER_SRC" ]] || { echo "ERROR: uninstaller.py not found at $UNINSTALLER_SRC"; exit 1; }

# ── Source backup (Python files only — no .so binaries) ──────────────────────
echo "Creating source backup (Python files only)..."
SOURCE_BACKUP="$SCRIPT_DIR/netmind-source-code.tar.gz"
tar -czf "$SOURCE_BACKUP" \
  --exclude="*.so" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude="*.c" \
  --exclude="NetMindDesktop" \
  --exclude="uninstaller" \
  -C /opt/netmind \
  .
echo "  Source backup: $(du -sh "$SOURCE_BACKUP" | cut -f1)  →  $SOURCE_BACKUP"

# ── Cython-protect source ─────────────────────────────────────────────────────
bash "$PROTECT"

# ── Install PyInstaller if needed ─────────────────────────────────────────────
if ! python3 -c "import PyInstaller" 2>/dev/null; then
  echo "Installing PyInstaller..."
  pip3 install pyinstaller --quiet --break-system-packages 2>/dev/null || \
    pip3 install pyinstaller --quiet
fi

# ── Clean previous build ──────────────────────────────────────────────────────
rm -rf "$BUILD_WORK" "$BUILD_DIST" \
       "$SCRIPT_DIR/NetMind-Setup.spec" "$SCRIPT_DIR/NetMind-Uninstaller.spec" 2>/dev/null || true
# Also wipe project dist/ in case it's root-owned from a previous sudo run
rm -rf "$SCRIPT_DIR/dist" 2>/dev/null || true
mkdir -p "$BUILD_WORK" "$BUILD_DIST"

# ── Build uninstaller binary (self-contained, no Python needed on target) ─────
echo "Building NetMind-Uninstaller (standalone binary)..."
pyinstaller \
  --onefile \
  --name "NetMind-Uninstaller" \
  --distpath "$BUILD_DIST" \
  --workpath "$BUILD_WORK/uninstaller" \
  --specpath "$SCRIPT_DIR" \
  --strip \
  --clean \
  "$UNINSTALLER_SRC"

UNINSTALLER_BIN="$BUILD_DIST/NetMind-Uninstaller"
[[ -f "$UNINSTALLER_BIN" ]] || { echo "ERROR: Uninstaller build failed"; exit 1; }
chmod +x "$UNINSTALLER_BIN"
echo "  ✔  Uninstaller built: $(du -sh "$UNINSTALLER_BIN" | cut -f1)"

# ── Inject standalone uninstaller into protected dir before creating tarball ──
echo "Injecting uninstaller binary into protected dir..."
cp "$UNINSTALLER_BIN" "$PROTECTED_DIR/uninstaller"
chmod +x "$PROTECTED_DIR/uninstaller"
echo "  ✔  Injected as $PROTECTED_DIR/uninstaller"

# ── Create tarball from protected copy (now includes standalone uninstaller) ──
echo "Creating tarball from protected source..."
tar -czf "$TARBALL" -C "$PROTECTED_DIR" .
echo "  Tarball: $(du -sh "$TARBALL" | cut -f1)  →  $TARBALL"

# ── Build installer ───────────────────────────────────────────────────────────
echo "Building NetMind-Setup..."
pyinstaller \
  --onefile \
  --name "NetMind-Setup" \
  --distpath "$BUILD_DIST" \
  --workpath "$BUILD_WORK/installer" \
  --specpath "$SCRIPT_DIR" \
  --add-data "$TARBALL:." \
  --hidden-import tkinter \
  --hidden-import tkinter.ttk \
  --hidden-import tkinter.scrolledtext \
  --hidden-import tkinter.filedialog \
  --strip \
  --clean \
  "$INSTALLER"

# ── Copy outputs to project dist/ ────────────────────────────────────────────
EXE="$BUILD_DIST/NetMind-Setup"
UN="$BUILD_DIST/NetMind-Uninstaller"
[[ -f "$EXE" ]] || { echo "ERROR: Build failed — NetMind-Setup not found."; exit 1; }

mkdir -p "$SCRIPT_DIR/dist"
cp "$EXE" "$SCRIPT_DIR/dist/NetMind-Setup"
cp "$UN"  "$SCRIPT_DIR/dist/NetMind-Uninstaller"
chmod +x "$SCRIPT_DIR/dist/NetMind-Setup" "$SCRIPT_DIR/dist/NetMind-Uninstaller"

# ── Copy to NetMind-Release ───────────────────────────────────────────────────
RELEASE_DIR="$HOME/Desktop/NetMind-Release"
if [[ -d "$RELEASE_DIR" ]]; then
  cp "$SCRIPT_DIR/dist/NetMind-Setup" "$RELEASE_DIR/NetMind-Setup"
  chmod +x "$RELEASE_DIR/NetMind-Setup"
  echo "  ✔  Copied to $RELEASE_DIR/NetMind-Setup"
else
  echo "  ⚠  $RELEASE_DIR not found — skipping release copy"
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
echo "  ✔  dist/NetMind-Setup        $(du -sh "$SCRIPT_DIR/dist/NetMind-Setup"        | cut -f1)  — installer"
echo "  ✔  dist/NetMind-Uninstaller  $(du -sh "$SCRIPT_DIR/dist/NetMind-Uninstaller"  | cut -f1)  — bundled inside installer tarball"
echo ""
echo "  Release folder:   $RELEASE_DIR/NetMind-Setup"
echo "  Upload that file to GitHub Releases"
echo "  Users install with:  sudo -E ./NetMind-Setup  (or double-click)"
