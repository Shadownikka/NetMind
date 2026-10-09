#!/bin/bash
# Build NetMind binaries with Nuitka (fully self-contained, no Python required on target)
# Usage: bash build.sh
# Output: dist/NetMind-Setup, dist/NetMind-Uninstaller

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="/opt/netmind"
INSTALLER_SRC="$SCRIPT_DIR/installer.py"
UNINSTALLER_SRC="$SCRIPT_DIR/uninstaller.py"
# Legacy builds kept this in /tmp, which is wiped on reboot. If the repo copy
# is missing but the old /tmp one exists, pull it into the repo so the source
# is persistent and version-controlled.
if [[ ! -f "$UNINSTALLER_SRC" && -f /tmp/uninstaller.py ]]; then
  cp /tmp/uninstaller.py "$UNINSTALLER_SRC"
fi
TARBALL="$SCRIPT_DIR/netmind-app.tar.gz"
BUILD_DIST="/tmp/netmind-nuitka-dist"
BUILD_WORK="/tmp/netmind-nuitka-build"

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ -d "$SRC"             ]] || { echo "ERROR: $SRC not found"; exit 1; }
[[ -f "$INSTALLER_SRC"   ]] || { echo "ERROR: installer.py not found"; exit 1; }
[[ -f "$UNINSTALLER_SRC" ]] || { echo "ERROR: uninstaller.py not found at $UNINSTALLER_SRC"; exit 1; }

# ── Source backup ─────────────────────────────────────────────────────────────
echo "Creating source backup..."
tar -czf "$SCRIPT_DIR/netmind-source-code.tar.gz" \
  --exclude="*.so" --exclude="__pycache__" --exclude="*.pyc" \
  --exclude="NetMindDesktop" --exclude="uninstaller" \
  -C "$SRC" .
echo "  ✔  Source backup done"

# ── Install patchelf (required by Nuitka onefile on Linux) ────────────────────
if ! command -v patchelf >/dev/null 2>&1; then
  echo "Installing patchelf..."
  apt-get install -y -q patchelf 2>/dev/null || \
    dnf install -y patchelf 2>/dev/null || \
    pacman -S --noconfirm patchelf 2>/dev/null || true
fi
command -v patchelf >/dev/null 2>&1 || { echo "ERROR: patchelf not found — run: sudo apt install patchelf"; exit 1; }

# ── Install Nuitka if needed ──────────────────────────────────────────────────
if ! python3 -c "import nuitka" 2>/dev/null; then
  echo "Installing Nuitka..."
  pip3 install nuitka ordered-set zstandard --quiet \
    --break-system-packages 2>/dev/null || \
    pip3 install nuitka ordered-set zstandard --quiet
fi
echo "  ✔  Nuitka ready"

# ── Install app requirements on build machine (Nuitka needs them to bundle) ───
if [[ -f "$SRC/requirements.txt" ]]; then
  echo "Installing app requirements for bundling..."
  pip3 install -r "$SRC/requirements.txt" --quiet \
    --break-system-packages 2>/dev/null || \
    pip3 install -r "$SRC/requirements.txt" --quiet
  echo "  ✔  Requirements ready"
fi

# ── Prepare clean source dir for Nuitka (no .so files — use .py source) ───────
NUITKA_SRC="$BUILD_WORK/src"
rm -rf "$BUILD_DIST" "$BUILD_WORK"
mkdir -p "$BUILD_DIST" "$BUILD_WORK"
cp -r "$SRC" "$NUITKA_SRC"
find "$NUITKA_SRC" -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "  ✔  Source prepared at $NUITKA_SRC"

# ── Restore core .so files from backup if /opt/netmind/core/ is empty ────────
BACKUP_CORE="/home/mahdi/Desktop/netmind-source-backup./core"
if ls "$NUITKA_SRC/core"/*.so 2>/dev/null | grep -qv __init__; then
  echo "  ✔  Core .so files already present"
elif [[ -d "$BACKUP_CORE" ]] && ls "$BACKUP_CORE"/*.so 2>/dev/null | grep -q .; then
  echo "  Core .so missing from $SRC/core/ — restoring from backup..."
  cp "$BACKUP_CORE"/*.so "$NUITKA_SRC/core/"
  # Also restore to /opt/netmind/core/ for future builds
  cp "$BACKUP_CORE"/*.so "$SRC/core/" 2>/dev/null || true
  echo "  ✔  Restored $(ls "$NUITKA_SRC/core"/*.so | wc -l) core modules"
else
  echo "  WARNING: No core .so files found — core modules will not be bundled"
fi

# ── Detect core modules from .so files (Cython-compiled, Python 3.12) ─────────
CORE_INCLUDES=""
for sofile in "$NUITKA_SRC/core"/*.so; do
  [ -f "$sofile" ] || continue
  modname=$(basename "$sofile" | cut -d. -f1)
  [[ "$modname" == "__init__" ]] && continue
  CORE_INCLUDES="$CORE_INCLUDES --include-module=$modname"
done
echo "  ✔  Core modules: $CORE_INCLUDES"

# ── Bundle libpython3.12.so.1.0 (needed by Cython core modules at runtime) ───
LIBPYTHON_PATH=$(find /usr/lib /usr/lib64 -name "libpython3.12.so.1.0" 2>/dev/null | head -1)
if [[ -z "$LIBPYTHON_PATH" ]]; then
  echo "ERROR: libpython3.12.so.1.0 not found — is python3.12-dev installed?"
  exit 1
fi
echo "  ✔  Bundling $LIBPYTHON_PATH"
LIBPYTHON_INCLUDE="--include-data-files=$LIBPYTHON_PATH=libpython3.12.so.1.0"

# ── Build NetMindDesktop ──────────────────────────────────────────────────────
echo ""
echo "Building NetMindDesktop (this takes a few minutes)..."
cd "$NUITKA_SRC"
PYTHONPATH="$NUITKA_SRC/core" python3 -m nuitka \
  --onefile \
  --enable-plugin=pyqt6 \
  $CORE_INCLUDES \
  $LIBPYTHON_INCLUDE \
  --include-package=termcolor \
  --include-package=ollama \
  --include-package=httpx \
  --include-package=pydantic \
  --output-filename=NetMindDesktop \
  --output-dir="$BUILD_DIST" \
  --remove-output \
  --quiet \
  "$NUITKA_SRC/NetMindDesktop.py"
chmod +x "$BUILD_DIST/NetMindDesktop"
echo "  ✔  NetMindDesktop built: $(du -sh "$BUILD_DIST/NetMindDesktop" | cut -f1)"

# ── Build Uninstaller ─────────────────────────────────────────────────────────
echo ""
echo "Building NetMind-Uninstaller..."
python3 -m nuitka \
  --onefile \
  --enable-plugin=pyqt6 \
  --output-filename=NetMind-Uninstaller \
  --output-dir="$BUILD_DIST" \
  --remove-output \
  --quiet \
  "$UNINSTALLER_SRC"
chmod +x "$BUILD_DIST/NetMind-Uninstaller"
echo "  ✔  Uninstaller built: $(du -sh "$BUILD_DIST/NetMind-Uninstaller" | cut -f1)"

# ── Build app tarball ─────────────────────────────────────────────────────────
echo ""
echo "Building app tarball..."
APP_STAGE="$BUILD_WORK/app"
mkdir -p "$APP_STAGE"
cp "$BUILD_DIST/NetMindDesktop"      "$APP_STAGE/NetMindDesktop"
cp "$BUILD_DIST/NetMind-Uninstaller" "$APP_STAGE/uninstaller"
chmod +x "$APP_STAGE/NetMindDesktop" "$APP_STAGE/uninstaller"
[ -d "$SRC/assets"       ] && cp -r "$SRC/assets"       "$APP_STAGE/"
[ -d "$SRC/observability" ] && cp -r "$SRC/observability" "$APP_STAGE/"
[ -f "$SRC/start.sh"     ] && cp "$SRC/start.sh"     "$APP_STAGE/" && chmod +x "$APP_STAGE/start.sh"
[ -f "$SRC/stop.sh"      ] && cp "$SRC/stop.sh"      "$APP_STAGE/" && chmod +x "$APP_STAGE/stop.sh"
tar -czf "$TARBALL" -C "$APP_STAGE" .
echo "  Tarball: $(du -sh "$TARBALL" | cut -f1)  →  $TARBALL"

# ── Build Installer ───────────────────────────────────────────────────────────
echo ""
echo "Building NetMind-Setup..."
python3 -m nuitka \
  --onefile \
  --enable-plugin=pyqt6 \
  --include-data-files="$TARBALL=netmind-app.tar.gz" \
  --output-filename=NetMind-Setup \
  --output-dir="$BUILD_DIST" \
  --remove-output \
  --quiet \
  "$INSTALLER_SRC"
chmod +x "$BUILD_DIST/NetMind-Setup"
echo "  ✔  NetMind-Setup built: $(du -sh "$BUILD_DIST/NetMind-Setup" | cut -f1)"

# ── Copy to project dist/ ─────────────────────────────────────────────────────
mkdir -p "$SCRIPT_DIR/dist"
cp "$BUILD_DIST/NetMind-Setup"       "$SCRIPT_DIR/dist/NetMind-Setup"
cp "$BUILD_DIST/NetMind-Uninstaller" "$SCRIPT_DIR/dist/NetMind-Uninstaller"
chmod +x "$SCRIPT_DIR/dist/"*

# ── Copy to NetMind-Release ───────────────────────────────────────────────────
RELEASE_DIR="/home/$(logname 2>/dev/null || echo mahdi)/Desktop/NetMind-Release"
if [[ -d "$RELEASE_DIR" ]]; then
  cp "$SCRIPT_DIR/dist/NetMind-Setup" "$RELEASE_DIR/NetMind-Setup"
  chmod +x "$RELEASE_DIR/NetMind-Setup"
  echo "  ✔  Copied to $RELEASE_DIR/NetMind-Setup"
fi

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
echo "  ✔  dist/NetMind-Setup        $(du -sh "$SCRIPT_DIR/dist/NetMind-Setup"        | cut -f1)  — installer"
echo "  ✔  dist/NetMind-Uninstaller  $(du -sh "$SCRIPT_DIR/dist/NetMind-Uninstaller"  | cut -f1)  — bundled inside tarball"
echo ""
echo "  Upload NetMind-Release/NetMind-Setup to GitHub Releases"
echo "  Users install with:  sudo -E ./NetMind-Setup"
