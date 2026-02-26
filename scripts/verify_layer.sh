#!/bin/bash
# ============================================================
# Lambda Layer Verification Script
# ============================================================
#
# Lambda Layer Structure (required by AWS Lambda runtime):
#
#   backend/layers/shared/           # ContentUri for SAM
#   ├── requirements.txt              # Python dependencies (bcrypt)
#   └── shared/                       # Importable as "from shared import ..."
#       ├── __init__.py
#       ├── db.py                     # DynamoDB client + Decimal serializer
#       ├── response.py               # success() / error() response helpers
#       └── auth_middleware.py         # authenticate(), require_auth, require_admin
#
# When SAM builds the layer (BuildMethod: python3.12), it:
#   1. Installs requirements.txt into python/ (bcrypt, etc.)
#   2. Copies everything else from ContentUri into python/
#   Result: python/shared/db.py, python/bcrypt/, etc.
#
# At runtime, Lambda adds /opt/python to sys.path, so:
#   - "from shared.db import get_item" works
#   - "import bcrypt" works (installed via requirements.txt)
#
# ============================================================

set -e

LAYER_DIR="backend/layers/shared"
SHARED_DIR="$LAYER_DIR/shared"

echo "=== Lambda Layer Verification ==="
echo ""

ERRORS=0

# Check directory structure
echo "Checking directory structure..."
for dir in "$LAYER_DIR" "$SHARED_DIR"; do
    if [ -d "$dir" ]; then
        echo "  ✓ $dir exists"
    else
        echo "  ✗ $dir MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check required files
echo ""
echo "Checking required files..."
REQUIRED_FILES=(
    "$LAYER_DIR/requirements.txt"
    "$SHARED_DIR/__init__.py"
    "$SHARED_DIR/db.py"
    "$SHARED_DIR/response.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ✗ $file MISSING"
        ERRORS=$((ERRORS + 1))
    fi
done

# Check optional files (created in later units)
echo ""
echo "Checking optional files (may not exist yet)..."
OPTIONAL_FILES=(
    "$SHARED_DIR/auth_middleware.py"
)

for file in "${OPTIONAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✓ $file"
    else
        echo "  ○ $file (not yet created)"
    fi
done

# Check requirements.txt has bcrypt
echo ""
echo "Checking requirements.txt..."
if grep -q "bcrypt" "$LAYER_DIR/requirements.txt"; then
    echo "  ✓ bcrypt dependency found"
else
    echo "  ✗ bcrypt dependency MISSING"
    ERRORS=$((ERRORS + 1))
fi

# Summary
echo ""
if [ $ERRORS -eq 0 ]; then
    echo "=== All checks passed ✓ ==="
else
    echo "=== $ERRORS check(s) FAILED ✗ ==="
    exit 1
fi
