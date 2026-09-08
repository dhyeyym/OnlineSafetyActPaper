library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(Oct2023 = as.Date("2023-10-23"), Mar2025 = as.Date("2025-03-17"), Jul2025 = as.Date("2025-07-21"))

run_ci <- function(y, weeks, post_start) {
  pre_start <- min(weeks)
  pre_end   <- post_start - 7
  post_end  <- post_start + 7 * 7
  idx <- weeks >= pre_start & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  if (sum(weeks >= post_start & weeks <= post_end) != 8) return(c(NA, NA))
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  ci <- CausalImpact(s, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

fmt <- function(r) {
  if (is.na(r[1])) return("ERROR")
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  sprintf("%+.0f%%%s", r[1], sig)
}

cat("================================================================\n")
cat("TABLE 12 — User count effects (unique/new/cumulative)\n")
cat("================================================================\n\n")

series <- list(
  list(label = "VPN (all)",            file = "vpn_user_timeseries.csv"),
  list(label = "VPN (UK)",             file = "vpn_uk_user_timeseries.csv"),
  list(label = "VPN (UK strict)",      file = "vpn_user_timeseries_uk_filtered.csv"),
  list(label = "Politics (all)",       file = "politics_user_timeseries.csv"),
  list(label = "Politics (UK)",        file = "politics_uk_user_timeseries.csv"),
  list(label = "Politics (UK strict)", file = "politics_user_timeseries_uk_filtered.csv")
)

metrics <- c("unique_users", "new_users", "cumulative_users")

results <- data.frame()
count <- 0
total <- length(series) * length(metrics) * length(MILESTONES)

for (s in series) {
  path <- file.path(DATA_DIR, s$file)
  if (!file.exists(path)) { cat("SKIP:", s$label, "\n"); next }
  df <- read.csv(path, stringsAsFactors = FALSE)
  df$week <- as.Date(df$week)
  df <- df[order(df$week), ]

  for (met in metrics) {
    if (!(met %in% names(df))) next
    for (ms in names(MILESTONES)) {
      count <- count + 1
      cat(sprintf("[%2d/%d] %s / %s / %s ... ", count, total, s$label, met, ms))
      r <- tryCatch(run_ci(df[[met]], df$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
      cat(fmt(r), "\n")
      results <- rbind(results, data.frame(
        series = s$label, metric = met, milestone = ms,
        relative_effect_pct = r[1], p_value = r[2]))
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table12_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table12_reproduced.csv (%d rows)\n", nrow(results)))