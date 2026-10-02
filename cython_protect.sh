#!/bin/bash
# Cython-protect NetMind source files
# Compiles /opt/netmind into a protected copy at /tmp/netmind-protected
# Original /opt/netmind is NOT modified — safe to run during development
# Output directory is used by build.sh to create the tarball

set -e

SRC="/opt/netmind"
OUT="/tmp/netmind-protected"

echo "── Cython Protection ────────────────────────────────────────────────────────"
echo "  Source : $SRC"
echo "  Output : $OUT"
echo ""

# ── Preflight ─────────────────────────────────────────────────────────────────
[[ -d "$SRC" ]] || { echo "ERROR: $SRC not found"; exit 1; }
[[ -f "$SRC/NetMindDesktop.py" ]] || { echo "ERROR: NetMindDesktop.py not found in $SRC"; exit 1; }

if ! python3 -c "import Cython" 2>/dev/null; then
  echo "Installing Cython..."
  pip3 install cython --quiet --break-system-packages 2>/dev/null || pip3 install cython --quiet
fi

command -v gcc >/dev/null 2>&1 || { echo "ERROR: gcc not found — install build-essential"; exit 1; }

# ── Python build info ─────────────────────────────────────────────────────────
PY_INC=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
PY_LIB=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")
PY_VER=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('LDVERSION'))")
EXT_SFX=$(python3 -c "import sysconfig; print(sysconfig.get_config_var('EXT_SUFFIX'))")

echo "  Python include : $PY_INC"
echo "  Python lib     : $PY_LIB"
echo "  Extension      : $EXT_SFX"
echo ""

# ── Fresh output directory ────────────────────────────────────────────────────
rm -rf "$OUT"
cp -r "$SRC" "$OUT"
rm -rf "$OUT/core/__pycache__"

compile_so() {
  local pyfile="$1"          # e.g. /tmp/netmind-protected/core/ai.py
  local base="${pyfile%.py}" # strip .py
  local cfile="$base.c"
  local sofile="$base$EXT_SFX"

  cython --3str "$pyfile" -o "$cfile" 2>/dev/null
  gcc -shared -fPIC -O2 \
      -I"$PY_INC" \
      -o "$sofile" \
      "$cfile" \
      -L"$PY_LIB" -lpython"$PY_VER" -lpthread -ldl 2>/dev/null
  rm -f "$cfile" "$pyfile"
  echo "  ✔  $(basename "$sofile")"
}

# ── Compile core modules ──────────────────────────────────────────────────────
echo "Compiling core modules..."
for pyfile in "$OUT/core"/*.py; do
  [ -f "$pyfile" ] || continue
  compile_so "$pyfile"
done

# ── Compile main app as embedded binary ───────────────────────────────────────
echo ""
echo "Compiling NetMindDesktop (embedded binary)..."
MAIN_PY="$OUT/NetMindDesktop.py"
MAIN_C="$OUT/NetMindDesktop.c"
MAIN_BIN="$OUT/NetMindDesktop"

cython --3str --embed "$MAIN_PY" -o "$MAIN_C" 2>/dev/null
gcc -O2 \
    -I"$PY_INC" \
    -o "$MAIN_BIN" \
    "$MAIN_C" \
    -L"$PY_LIB" -Wl,-rpath,"$PY_LIB" \
    -lpython"$PY_VER" -lpthread -ldl -lm -lutil 2>/dev/null
rm -f "$MAIN_C" "$MAIN_PY"
chmod +x "$MAIN_BIN"
echo "  ✔  NetMindDesktop (binary)"

# ── Result ────────────────────────────────────────────────────────────────────
echo ""
echo "Protected files in $OUT:"
find "$OUT" \( -name "*.so" -o -name "NetMindDesktop" -o -name "*.sh" \
              -o -name "*.txt" -o -name "*.yml" -o -name "*.json" \
              -o -name "*.png" \) | grep -v "__pycache__" | sort | sed 's|^|  |'
echo ""
echo "  ✔  Protection complete — no .py source files remain"
echo ""
