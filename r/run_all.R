#!/usr/bin/env Rscript
# =============================================================================
# run_all.R
# Orchestrates all R analysis scripts in order.
# Usage: Rscript r/run_all.R
# =============================================================================

cat("═══════════════════════════════════════════════════════════════\n")
cat("  SUPPLY CHAIN ANALYTICS PLATFORM — R Analysis Suite\n")
cat("═══════════════════════════════════════════════════════════════\n")

# Detect script directory — works with Rscript run_all.R from project root
args     <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)
if (length(file_arg) > 0) {
  r_dir <- dirname(normalizePath(sub("^--file=", "", file_arg)))
} else {
  r_dir <- "r"   # fallback: run from project root with source()
}

scripts <- c(
  file.path(r_dir, "statistical_analysis.R"),
  file.path(r_dir, "time_series.R")
)

for (script in scripts) {
  cat(sprintf("\n▶  Running: %s\n", basename(script)))
  cat("───────────────────────────────────────────────────────────────\n")
  tryCatch(
    source(script, local = FALSE),
    error = function(e) {
      cat(sprintf("❌  Error in %s:\n   %s\n", basename(script), conditionMessage(e)))
    }
  )
}

cat("\n═══════════════════════════════════════════════════════════════\n")
cat("  ✅  All R scripts complete. Check outputs/ for results.\n")
cat("═══════════════════════════════════════════════════════════════\n")
