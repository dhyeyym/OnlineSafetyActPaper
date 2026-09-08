library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

MILESTONES <- list(Oct2023 = as.Date("2023-10-23"), Mar2025 = as.Date("2025-03-17"), Jul2025 = as.Date("2025-07-21"))
WINDOWS <- c(4, 8, 12)

# Table 16 series from the paper
series_map <- list(
  list(label = "VPN (all)",      group = "VPN",      filter = "Classified"),
  list(label = "VPN (UK)",       group = "VPN",      filter = "Classified (UK)"),
  list(label = "Politics (all)", group = "Politics",  filter = "Classified"),
  list(label = "Politics (UK)",  group = "Politics",  filter = "Classified (UK)")
)

run_ci <- function(y, weeks, post_start, window_weeks) {
  pre_start <- min(weeks)
  pre_end <- post_start - 7
  post_end <- post_start + 7 * (window_weeks - 1)
  idx <- weeks >= pre_start & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  n_post <- sum(weeks >= post_start & weeks <= post_end)
  if (n_post != window_weeks) return(c(NA, NA))
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  ci <- CausalImpact(s, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

cat("TABLE 16 — Post-window robustness (4/8/12 weeks)\n\n")

results <- data.frame()
for (s in series_map) {
  sub <- weekly[weekly$group == s$group & weekly$filter == s$filter, ]
  sub <- sub[order(sub$week), ]
  if (nrow(sub) == 0) { cat("SKIP:", s$label, "\n"); next }
  for (ms in names(MILESTONES)) {
    for (w in WINDOWS) {
      cat(sprintf("  %s / %s / %dwk ... ", s$label, ms, w))
      r <- tryCatch(run_ci(sub$total, sub$week, MILESTONES[[ms]], w), error = function(e) c(NA, NA))
      if (!is.na(r[1])) {
        sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
        cat(sprintf("%+.0f%%%s\n", r[1], sig))
      } else { cat("ERROR\n") }
      results <- rbind(results, data.frame(series = s$label, milestone = ms, window_weeks = w,
                                            relative_effect_pct = r[1], p_value = r[2]))
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table16_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: %s (%d rows)\n", file.path(DATA_DIR, "table16_reproduced.csv"), nrow(results)))
