library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(
  Oct2023 = as.Date("2023-10-23"),
  Mar2025 = as.Date("2025-03-17"),
  Jul2025 = as.Date("2025-07-21")
)

WINDOWS <- c(4, 8, 12)

SERIES <- list(
  list(label = "VPN (all)", group = "VPN", filter = "Classified"),
  list(label = "VPN (UK)", group = "VPN", filter = "Classified (UK)"),
  list(label = "Politics (all)", group = "Politics", filter = "Classified"),
  list(label = "Politics (UK)", group = "Politics", filter = "Classified (UK)")
)

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) {
    return(min(candidates))
  }
  return(max(weeks[weeks < target]))
}

run_ci <- function(y, weeks, treatment_target, window_weeks) {
  treatment_week <- snap_to_week(treatment_target, weeks)
  pre_end <- treatment_week - 7
  post_end <- treatment_week + 7 * (window_weeks - 1)

  in_window <- weeks >= min(weeks) & weeks <= post_end
  series <- zoo(y[in_window], order.by = weeks[in_window])

  if (length(unique(y[in_window])) <= 1) {
    return(c(NA, NA))
  }

  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(series, c(min(weeks), pre_end), c(treatment_week, post_end))
    average <- ci$summary["Average", ]
    c(round(average[["RelEffect"]] * 100, 1), round(average[["p"]], 4))
  }, error = function(e) {
    c(NA, NA)
  })
}

significance_stars <- function(p) {
  if (p < 0.05) {
    return("**")
  }
  if (p < 0.10) {
    return("*")
  }
  return("")
}

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

cat("TABLE 16 — Post-window robustness\n\n")

results <- data.frame()

for (s in SERIES) {
  sub <- weekly[weekly$group == s$group & weekly$filter == s$filter, ]
  sub <- sub[order(sub$week), ]

  if (nrow(sub) == 0) {
    next
  }

  for (milestone in names(MILESTONES)) {
    for (window_weeks in WINDOWS) {
      cat(sprintf("  %s / %s / %dwk ... ", s$label, milestone, window_weeks))

      r <- run_ci(sub$total, sub$week, MILESTONES[[milestone]], window_weeks)

      if (!is.na(r[1])) {
        cat(sprintf("%+.0f%%%s\n", r[1], significance_stars(r[2])))
      } else {
        cat("NA\n")
      }

      results <- rbind(results, data.frame(
        series = s$label,
        milestone = milestone,
        window_weeks = window_weeks,
        relative_effect_pct = r[1],
        p_value = r[2]
      ))
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table16_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table16_reproduced.csv (%d rows)\n", nrow(results)))
