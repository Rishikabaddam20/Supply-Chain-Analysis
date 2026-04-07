#!/bin/bash
# =============================================================================
# setup.sh — One-click environment setup
# Usage: bash setup.sh
# =============================================================================

set -e
echo "════════════════════════════════════════════════════════"
echo "  Supply Chain Analytics Platform — Environment Setup  "
echo "════════════════════════════════════════════════════════"

# ── Python virtual environment ───────────────────────────────────────────────
echo ""
echo "▶ Creating Python virtual environment …"
python3 -m venv venv

# Activate — works on macOS/Linux
source venv/bin/activate 2>/dev/null || . venv/bin/activate

echo "▶ Upgrading pip …"
pip install --upgrade pip --quiet

echo "▶ Installing Python dependencies …"
pip install -r requirements.txt

echo "✅ Python environment ready"
echo "   (Run: source venv/bin/activate  before python python/main.py)"

# ── R packages ───────────────────────────────────────────────────────────────
echo ""
echo "▶ Installing R packages (requires R) …"
Rscript -e "
packages <- c('tidyverse','lubridate','forecast','tseries',
              'corrplot','broom','scales','patchwork')
new_pkgs <- packages[!(packages %in% installed.packages()[,'Package'])]
if (length(new_pkgs)) {
  install.packages(new_pkgs, repos='https://cran.r-project.org', quiet=TRUE)
  cat('✅ R packages installed:', paste(new_pkgs, collapse=', '), '\n')
} else {
  cat('✅ All R packages already installed\n')
}
" 2>/dev/null || echo "⚠️  R not found — skipping R package installation"

# ── Output directories ───────────────────────────────────────────────────────
echo ""
echo "▶ Creating output directories …"
mkdir -p outputs/charts outputs/reports
touch outputs/charts/.gitkeep outputs/reports/.gitkeep

echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ Setup complete!  To run the full pipeline:"
echo ""
echo "     source venv/bin/activate"
echo "     python python/main.py"
echo ""
echo "  To run R analysis:"
echo "     Rscript r/run_all.R"
echo "════════════════════════════════════════════════════════"
