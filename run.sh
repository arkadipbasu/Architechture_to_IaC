#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  Arch2IaC — Launch Script (macOS)
# ─────────────────────────────────────────────────────────────────

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  🏗️  Arch2IaC — Enterprise Architecture to IaC      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 not found. Install via: brew install python"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# ── Install deps if needed ────────────────────────────────────
echo "📦 Checking dependencies…"
pip3 install -r requirements.txt --break-system-packages -q 2>&1 | tail -5

echo ""
echo "🚀 Starting Arch2IaC on http://localhost:8501"
echo ""
echo "Features:"
echo "  🎨  Visual drag-and-drop architecture canvas"
echo "  ☁️  AWS · Azure · GCP · OpenStack support"
echo "  ⚙️  OpenTofu / Terraform code generation"
echo "  ☁️  CloudFormation template generation (AWS)"
echo "  🤖  AI enhancement via Gemini & OpenAI"
echo "  📦  Full ZIP export with deployment guides"
echo "  📋  Structured logging (file + session)"
echo ""
echo "Press Ctrl+C to stop"
echo "─────────────────────────────────────────────────────────"

# ── Launch ────────────────────────────────────────────────────
streamlit run app.py \
    --server.port 8501 \
    --server.address localhost \
    --browser.gatherUsageStats false \
    --theme.base dark
