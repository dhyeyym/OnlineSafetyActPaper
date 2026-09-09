library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"
MILESTONES <- list(Oct2023 = as.Date("2023-10-23"), Mar2025 = as.Date("2025-03-17"), Jul2025 = as.Date("2025-07-21"))
WINDOWS <- c(4, 8, 12)

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) return(min(candidates))
  return(max(weeks[weeks < target]))
}

run_ci <- function(y, weeks, treatment_target, window_weeks) {
  td <- snap_to_week(treatment_target, weeks)
  pre_end <- td - 7; post_end <- td + 7 * (window_weeks - 1)
  idx <- weeks >= min(weeks) & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(s, c(min(weeks), pre_end), c(td, post_end))
    avg <- ci$summary["Average", ]
    c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
  }, error = function(e) c(NA, NA))
}

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

series_map <- list(
  list(label = "VPN (all)",      group = "VPN",      filter = "Classified"),
  list(label = "VPN (UK)",       group = "VPN",      filter = "Classified (UK)"),
  list(label = "Politics (all)", group = "Politics",  filter = "Classified"),
  list(label = "Politics (UK)",  group = "Politics",  filter = "Classified (UK)")
)

cat("TABLE 16 — Post-window robustness\n\n")
results <- data.frame()
for (s in series_map) {
  sub <- weekly[weekly$group == s$group & weekly$filter == s$filter, ]
  sub <- sub[order(sub$week), ]
  if (nrow(sub) == 0) next
  for (ms in names(MILESTONES)) {
    for (w in WINDOWS) {
      cat(sprintf("  %s / %s / %dwk ... ", s$label, ms, w))
      r <- run_ci(sub$total, sub$week, MILESTONES[[ms]], w)
      if (!is.na(r[1])) {
        sig <- ifelse(r[2] < 0.05, "**", ifelse(r[2] < 0.10, "*", ""))
        cat(sprintf("%+.0f%%%s\n", r[1], sig))
      } else cat("NA\n")
      results <- rbind(results, data.frame(series = s$label, milestone = ms, window_weeks = w,
        relative_effect_pct = r[1], p_value = r[2]))
    }
  }
}
write.csv(results, file.path(DATA_DIR, "table16_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table16_reproduced.csv (%d rows)\n", nrow(results)))
