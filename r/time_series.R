#!/usr/bin/env Rscript
# =============================================================================
# time_series.R
# Time Series Analysis & Forecasting with R
# Covers: decomposition, ARIMA, ETS (exponential smoothing), STL forecast,
#         seasonal diagnostics, and ggplot2 visualisations
# =============================================================================

suppressPackageStartupMessages({
  library(tidyverse)
  library(lubridate)
  library(forecast)
  library(tseries)
  library(scales)
  library(patchwork)
})

# ── Paths ─────────────────────────────────────────────────────────────────────
# Works with both: Rscript r/time_series.R  AND  source("r/time_series.R")
get_script_dir <- function() {
  args     <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("^--file=", args, value = TRUE)
  if (length(file_arg) > 0) {
    return(dirname(normalizePath(sub("^--file=", "", file_arg))))
  }
  tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) getwd())
}
PROJECT_ROOT <- normalizePath(file.path(get_script_dir(), ".."), mustWork = FALSE)
DATA_PATH    <- file.path(PROJECT_ROOT, "data", "supply_chain_data.csv")
CHARTS_DIR   <- file.path(PROJECT_ROOT, "outputs", "charts")
REPORTS_DIR  <- file.path(PROJECT_ROOT, "outputs", "reports")
dir.create(CHARTS_DIR,  showWarnings = FALSE, recursive = TRUE)
dir.create(REPORTS_DIR, showWarnings = FALSE, recursive = TRUE)

cat("── Loading & Aggregating Data ────────────────────────────────────────\n")
df <- read_csv(DATA_PATH, show_col_types = FALSE) %>%
  mutate(date = as.Date(date))

# Aggregate to weekly total demand (cleaner for time series)
weekly <- df %>%
  mutate(week = floor_date(date, "week")) %>%
  group_by(week) %>%
  summarise(
    total_demand  = sum(demand,           na.rm = TRUE),
    total_revenue = sum(revenue,          na.rm = TRUE),
    avg_inventory = mean(inventory_level, na.rm = TRUE),
    stockout_days = sum(stockout,         na.rm = TRUE),
    .groups = "drop"
  ) %>%
  arrange(week)

cat(sprintf("✅ Weekly series: %d observations\n", nrow(weekly)))

# ═════════════════════════════════════════════════════════════════════════════
# 1. VISUALISE WEEKLY DEMAND
# ═════════════════════════════════════════════════════════════════════════════
p1 <- ggplot(weekly, aes(x = week, y = total_demand)) +
  geom_area(fill = "#4575b4", alpha = 0.25) +
  geom_line(color = "#1F4E79", linewidth = 0.9) +
  geom_smooth(method = "loess", se = TRUE, color = "#D73027",
              fill = "#FDAE61", alpha = 0.3, linewidth = 1.2) +
  scale_x_date(date_breaks = "6 months", date_labels = "%b %Y") +
  scale_y_continuous(labels = comma) +
  labs(title    = "Weekly Aggregate Demand (2022–2025)",
       subtitle = "Blue = actual  |  Red = LOESS trend",
       x = NULL, y = "Total Units Demanded") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"),
        axis.text.x = element_text(angle = 45, hjust = 1))

p2 <- ggplot(weekly, aes(x = week, y = avg_inventory)) +
  geom_line(color = "#1A9641", linewidth = 0.8) +
  geom_hline(yintercept = mean(weekly$avg_inventory), color = "#D73027",
             linetype = "dashed", linewidth = 0.9) +
  scale_x_date(date_breaks = "6 months", date_labels = "%b %Y") +
  scale_y_continuous(labels = comma) +
  labs(title = "Weekly Avg Inventory Level",
       subtitle = "Dashed = overall mean",
       x = NULL, y = "Avg Inventory (units)") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face = "bold"),
        axis.text.x = element_text(angle = 45, hjust = 1))

combined <- p1 / p2
ggsave(file.path(CHARTS_DIR, "weekly_demand_inventory.png"),
       combined, width = 14, height = 10, dpi = 150)
cat("✅ Weekly demand/inventory plot saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 2. TIME SERIES DECOMPOSITION (STL)
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── STL Decomposition ────────────────────────────────────────────────\n")
ts_demand <- ts(weekly$total_demand, frequency = 52)   # weekly, annual seasonality

stl_fit <- stl(ts_demand, s.window = "periodic", robust = TRUE)

png(file.path(CHARTS_DIR, "stl_decomposition.png"),
    width = 1100, height = 700, res = 130)
plot(stl_fit, main = "STL Decomposition of Weekly Demand",
     col = "#1F4E79", col.range = "#4575b4")
dev.off()
cat("✅ STL decomposition plot saved\n")

# Extract & save components
stl_components <- as_tibble(stl_fit$time.series) %>%
  mutate(
    week     = weekly$week,
    original = weekly$total_demand,
    .before  = 1
  )
write_csv(stl_components, file.path(REPORTS_DIR, "stl_components.csv"))
cat("✅ STL components saved to CSV\n")

# ═════════════════════════════════════════════════════════════════════════════
# 3. STATIONARITY TEST (ADF)
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── ADF Stationarity Test ─────────────────────────────────────────────\n")
adf_result <- adf.test(ts_demand, alternative = "stationary")
cat(sprintf("   ADF Statistic : %.4f\n", adf_result$statistic))
cat(sprintf("   p-value       : %.4f\n", adf_result$p.value))
cat(sprintf("   Conclusion    : %s\n",
    ifelse(adf_result$p.value < 0.05, "Series is STATIONARY ✅",
                                       "Series is NON-STATIONARY ⚠️")))

# ═════════════════════════════════════════════════════════════════════════════
# 4. AUTO-ARIMA FORECASTING
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── Auto-ARIMA Forecasting ────────────────────────────────────────────\n")
# Train on first 80%, forecast remaining 20% + 26 weeks ahead
train_n    <- floor(0.8 * length(ts_demand))
ts_train   <- head(ts_demand, train_n)
ts_test    <- tail(ts_demand, length(ts_demand) - train_n)

cat("   Fitting Auto-ARIMA … (this may take a moment)\n")
arima_model <- auto.arima(ts_train, seasonal = TRUE,
                           stepwise = FALSE, approximation = FALSE,
                           trace = FALSE)
cat(sprintf("   Best model: %s\n", arima_model$arma %>%
  {sprintf("ARIMA(%d,%d,%d)(%d,%d,%d)[%d]", .[1],.[6],.[2],.[3],.[7],.[4],.[5])}))

# Forecast 26 weeks ahead
h_ahead     <- 26
arima_fc    <- forecast(arima_model, h = length(ts_test) + h_ahead)

# Accuracy on test set
arima_acc   <- accuracy(arima_fc, ts_test)
cat("\n   ARIMA Test Accuracy:\n")
print(round(arima_acc, 3))

# ═════════════════════════════════════════════════════════════════════════════
# 5. ETS (EXPONENTIAL SMOOTHING)
# ═════════════════════════════════════════════════════════════════════════════
cat("\n── ETS Exponential Smoothing ─────────────────────────────────────────\n")
ets_model <- ets(ts_train, ic = "aicc")
ets_fc    <- forecast(ets_model, h = length(ts_test) + h_ahead)
ets_acc   <- accuracy(ets_fc, ts_test)
cat(sprintf("   ETS Model: %s\n", ets_model$method))
cat("\n   ETS Test Accuracy:\n")
print(round(ets_acc, 3))

# Save accuracy comparison
acc_df <- bind_rows(
  as_tibble(arima_acc) %>% mutate(model = "ARIMA", set = c("Training","Test"), .before=1),
  as_tibble(ets_acc)   %>% mutate(model = "ETS",   set = c("Training","Test"), .before=1)
)
write_csv(acc_df, file.path(REPORTS_DIR, "ts_model_accuracy.csv"))
cat("✅ Time series accuracy saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 6. FORECAST VISUALISATION
# ═════════════════════════════════════════════════════════════════════════════
# Build plot data frames
n_total <- length(ts_demand)
fc_start_idx <- train_n + 1
weeks_full   <- weekly$week

# ARIMA forecast df
arima_fc_df <- tibble(
  week    = seq(weeks_full[fc_start_idx],
                by = "week",
                length.out = length(ts_test) + h_ahead),
  mean    = as.numeric(arima_fc$mean),
  lo80    = as.numeric(arima_fc$lower[,"80%"]),
  hi80    = as.numeric(arima_fc$upper[,"80%"]),
  lo95    = as.numeric(arima_fc$lower[,"95%"]),
  hi95    = as.numeric(arima_fc$upper[,"95%"]),
)

actual_df <- tibble(week = weeks_full, demand = as.numeric(ts_demand))

p_fc <- ggplot() +
  geom_ribbon(data = arima_fc_df, aes(x=week, ymin=lo95, ymax=hi95),
              fill="#FDAE61", alpha=0.4) +
  geom_ribbon(data = arima_fc_df, aes(x=week, ymin=lo80, ymax=hi80),
              fill="#F46D43", alpha=0.4) +
  geom_line(data = actual_df, aes(x=week, y=demand, colour="Actual"), linewidth=0.9) +
  geom_line(data = arima_fc_df, aes(x=week, y=mean, colour="ARIMA Forecast"),
            linewidth=1.1, linetype="dashed") +
  geom_vline(xintercept = as.numeric(weeks_full[train_n]),
             color="#333333", linetype="dotted", linewidth=0.8) +
  annotate("text", x=weeks_full[train_n], y=max(actual_df$demand)*0.95,
           label="Train | Test →", hjust=1, size=3.5, color="#333333") +
  scale_colour_manual(values = c("Actual"="#1F4E79","ARIMA Forecast"="#D73027")) +
  scale_x_date(date_breaks = "6 months", date_labels = "%b %Y") +
  scale_y_continuous(labels = comma) +
  labs(title    = "ARIMA Demand Forecast — 26-Week Horizon",
       subtitle  = "Orange shading = 80% / 95% confidence intervals",
       x = NULL, y = "Weekly Demand (units)",
       colour = NULL) +
  theme_minimal(base_size = 12) +
  theme(plot.title    = element_text(face="bold"),
        legend.position = "top",
        axis.text.x   = element_text(angle=45, hjust=1))

ggsave(file.path(CHARTS_DIR, "arima_forecast.png"),
       p_fc, width=14, height=7, dpi=150)
cat("✅ ARIMA forecast plot saved\n")

# ═════════════════════════════════════════════════════════════════════════════
# 7. SEASONAL HEATMAP
# ═════════════════════════════════════════════════════════════════════════════
monthly_heat <- df %>%
  mutate(month_lbl = month(date, label=TRUE),
         year      = year(date)) %>%
  group_by(year, month_lbl) %>%
  summarise(avg_demand = mean(demand, na.rm=TRUE), .groups="drop")

p_heat <- ggplot(monthly_heat,
                 aes(x = month_lbl, y = factor(year), fill = avg_demand)) +
  geom_tile(colour = "white", linewidth = 0.5) +
  geom_text(aes(label = round(avg_demand, 0)), size = 3) +
  scale_fill_gradientn(colours=c("#313695","#74ADD1","#FEE08B","#F46D43","#A50026"),
                       labels = comma) +
  labs(title = "Seasonal Demand Heatmap (Monthly Avg)",
       x = "Month", y = "Year", fill = "Avg Demand") +
  theme_minimal(base_size = 12) +
  theme(plot.title = element_text(face="bold"))

ggsave(file.path(CHARTS_DIR, "seasonal_heatmap.png"),
       p_heat, width=12, height=5, dpi=150)
cat("✅ Seasonal heatmap saved\n")

cat("\n── R Time Series Analysis Complete ──────────────────────────────────\n")
