#!/usr/bin/env Rscript
# =============================================================================
# statistical_analysis.R
# Supply Chain Statistical Modelling in R
# Covers: descriptive stats, linear regression, ANOVA, correlation analysis
# =============================================================================

library(tidyverse)
library(broom)
library(corrplot)
library(ggplot2)
library(scales)

# ── Paths ─────────────────────────────────────────────────────────────────────
# Works with both: Rscript r/statistical_analysis.R  AND  source("r/statistical_analysis.R")
get_script_dir <- function() {
  # Rscript approach
  args     <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg))))
  }
  # source() approach
  tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) getwd())
}
PROJECT_ROOT <- normalizePath(file.path(get_script_dir(), ".."), mustWork = FALSE)
DATA_PATH    <- file.path(PROJECT_ROOT, "data", "supply_chain_data.csv")
CHARTS_DIR   <- file.path(PROJECT_ROOT, "outputs", "charts")
REPORTS_DIR  <- file.path(PROJECT_ROOT, "outputs", "reports")
dir.create(CHARTS_DIR,  showWarnings = FALSE, recursive = TRUE)
dir.create(REPORTS_DIR, showWarnings = FALSE, recursive = TRUE)

cat("── Loading Data ──────────────────────────────────────────────────────\n")
df <- read_csv(DATA_PATH, show_col_types = FALSE) %>%
  mutate(
    date    = as.Date(date),
    month   = lubridate::month(date),
    quarter = lubridate::quarter(date),
    year    = lubridate::year(date),
    category = as.factor(category),
    region   = as.factor(region),
  )
cat(sprintf("✅ Loaded %s rows, %s columns\n", format(nrow(df), big.mark=","), ncol(df)))

# ═════════════════════════════════════════════════════════════════════════════
# 1. DESCRIPTIVE STATISTICS
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── Descriptive Statistics ───────────────────────────────────────────\n")
desc_stats <- df %>%
  select(demand, inventory_level, units_sold, shipping_cost,
         defect_rate, lead_time_actual, fill_rate, holding_cost) %>%
  summarise(across(everything(), list(
    mean   = ~mean(.x, na.rm=TRUE),
    median = ~median(.x, na.rm=TRUE),
    sd     = ~sd(.x, na.rm=TRUE),
    min    = ~min(.x, na.rm=TRUE),
    max    = ~max(.x, na.rm=TRUE),
    p25    = ~quantile(.x, 0.25, na.rm=TRUE),
    p75    = ~quantile(.x, 0.75, na.rm=TRUE)
  ))) %>%
  pivot_longer(everything(), names_to=c("variable","stat"), names_sep="_(?=[^_]+$)")

cat(format(desc_stats, digits=3))
write_csv(desc_stats, file.path(REPORTS_DIR, "descriptive_stats.csv"))
cat("\n✅ Descriptive stats saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 2. CORRELATION ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── Correlation Analysis ─────────────────────────────────────────────\n")
corr_vars <- df %>%
  select(demand, inventory_level, units_sold, shipping_cost,
         defect_rate, lead_time_actual, stockout, holding_cost,
         reliability_score) %>%
  drop_na()

cor_matrix <- cor(corr_vars, method = "pearson")

png(file.path(CHARTS_DIR, "correlation_matrix.png"),
    width = 800, height = 700, res = 120)
corrplot(cor_matrix,
         method   = "color",
         type     = "upper",
         order    = "hclust",
         tl.cex   = 0.85,
         tl.col   = "black",
         addCoef.col = "black",
         number.cex  = 0.7,
         col      = colorRampPalette(c("#D73027","#FFFFFF","#1A9641"))(200),
         title    = "Supply Chain Variable Correlations",
         mar      = c(0,0,2,0))
dev.off()
cat("✅ Correlation matrix saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 3. LINEAR REGRESSION — Demand Predictors
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── Linear Regression: Demand Predictors ─────────────────────────────\n")
lm_df <- df %>%
  mutate(
    log_demand    = log1p(demand),
    log_inventory = log1p(inventory_level)
  ) %>%
  select(log_demand, log_inventory, shipping_cost, defect_rate,
         lead_time_actual, is_weekend, month, reliability_score) %>%
  drop_na()

lm_model <- lm(log_demand ~ ., data = lm_df)
lm_summary <- tidy(lm_model)
cat(format(lm_summary, digits=4))
cat(sprintf("\n   R²: %.4f  |  Adj. R²: %.4f  |  F-stat p-value: %.2e\n",
            summary(lm_model)$r.squared,
            summary(lm_model)$adj.r.squared,
            pf(summary(lm_model)$fstatistic[1],
               summary(lm_model)$fstatistic[2],
               summary(lm_model)$fstatistic[3],
               lower.tail=FALSE)))

write_csv(lm_summary, file.path(REPORTS_DIR, "regression_coefficients.csv"))
cat("✅ Regression results saved\n")

# Residual plot
png(file.path(CHARTS_DIR, "regression_residuals.png"),
    width = 900, height = 450, res = 120)
par(mfrow = c(1,2))
plot(lm_model, which = c(1, 2), col = "#4575b4", pch = 16, cex = 0.4)
dev.off()
cat("✅ Residual plots saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 4. ONE-WAY ANOVA — Demand by Category
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── ANOVA: Demand by Product Category ────────────────────────────────\n")
anova_model <- aov(demand ~ category, data = df)
anova_summary <- tidy(anova_model)
cat(format(anova_summary, digits=4))

# Tukey's HSD post-hoc
tukey <- TukeyHSD(anova_model)
tukey_df <- as.data.frame(tukey$category) %>%
  rownames_to_column("comparison") %>%
  as_tibble()
write_csv(tukey_df, file.path(REPORTS_DIR, "anova_tukey.csv"))
cat("\n✅ ANOVA + Tukey HSD saved\n")

# Boxplot
p_anova <- ggplot(df %>% sample_n(min(20000, nrow(df))),
                  aes(x = reorder(category, demand, median),
                      y = demand, fill = category)) +
  geom_boxplot(outlier.size = 0.5, outlier.alpha = 0.3) +
  scale_fill_brewer(palette = "Set2") +
  scale_y_continuous(labels = comma) +
  labs(title    = "Demand Distribution by Product Category",
       subtitle = sprintf("One-Way ANOVA: F=%.2f, p=%.3e",
                           anova_summary$statistic[1], anova_summary$p.value[1]),
       x = "Category", y = "Demand (units)") +
  theme_minimal(base_size = 12) +
  theme(legend.position = "none",
        plot.title = element_text(face = "bold"))
ggsave(file.path(CHARTS_DIR, "anova_demand_by_category.png"),
       p_anova, width = 10, height = 6, dpi = 150)
cat("✅ ANOVA boxplot saved\n")

cat("\n── R Statistical Analysis Complete ──────────────────────────────────\n")
