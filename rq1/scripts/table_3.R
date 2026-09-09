library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(
  Oct2023 = as.Date("2023-10-23"),
  Mar2025 = as.Date("2025-03-17"),
  Jul2025 = as.Date("2025-07-21")
)

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) return(min(candidates))
  return(max(weeks[weeks < target]))
}

run_ci <- function(y, weeks, treatment_target) {
  td <- snap_to_week(treatment_target, weeks)
  pre_end <- td - 7; post_end <- td + 7 * 7
  idx <- weeks >= min(weeks) & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(s, c(min(weeks), pre_end), c(td, post_end))
    avg <- ci$summary["Average", ]
    c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
  }, error = function(e) { cat("  ERR:", conditionMessage(e), "\n"); c(NA, NA) })
}

fmt <- function(r) {
  if (is.na(r[1])) return("NA")
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  sprintf("%+.1f%%%s", r[1], sig)
}

# ================================================================
# CONTENT — from table13_weekly_series.csv
# ================================================================
cat("================================================================\n")
cat("TABLE 3 — Content (posts + comments)\n")
cat("================================================================\n\n")

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

content_rows <- list(
  list(group = "VPN",      filter = "Raw"),
  list(group = "VPN",      filter = "Raw (UK)"),
  list(group = "VPN",      filter = "Classified"),
  list(group = "VPN",      filter = "Classified (UK)"),
  list(group = "Politics", filter = "Raw"),
  list(group = "Politics", filter = "Raw (UK)"),
  list(group = "Politics", filter = "Classified"),
  list(group = "Politics", filter = "Classified (UK)")
)

results <- data.frame()
for (cr in content_rows) {
  sub <- weekly[weekly$group == cr$group & weekly$filter == cr$filter, ]
  sub <- sub[order(sub$week), ]
  if (nrow(sub) == 0) { cat("SKIP:", cr$group, cr$filter, "\n"); next }
  for (ms in names(MILESTONES)) {
    cat(sprintf("  %s %s / %s ... ", cr$group, cr$filter, ms))
    r <- run_ci(sub$total, sub$week, MILESTONES[[ms]])
    cat(fmt(r), "\n")
    results <- rbind(results, data.frame(group = cr$group, filter = cr$filter,
      column = "Content", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
  }
}

# ================================================================
# USERS — from table12_user_weekly_series.csv (all filter levels)
# ================================================================
cat("\n================================================================\n")
cat("TABLE 3 — Users (new_users)\n")
cat("================================================================\n\n")

user_file <- file.path(DATA_DIR, "table12_user_weekly_series.csv")
if (!file.exists(user_file)) {
  cat("WARNING: table12_user_weekly_series.csv not found.\n")
  cat("Run rebuild_all_user_timeseries.py first.\n")
} else {
  user_weekly <- read.csv(user_file, stringsAsFactors = FALSE)
  user_weekly$week <- as.Date(user_weekly$week)

  user_rows <- list(
    list(group = "VPN",      filter = "Raw"),
    list(group = "VPN",      filter = "Raw (UK)"),
    list(group = "VPN",      filter = "Classified"),
    list(group = "VPN",      filter = "Classified (UK)"),
    list(group = "Politics", filter = "Raw"),
    list(group = "Politics", filter = "Raw (UK)"),
    list(group = "Politics", filter = "Classified"),
    list(group = "Politics", filter = "Classified (UK)")
  )

  for (ur in user_rows) {
    sub <- user_weekly[user_weekly$group == ur$group & user_weekly$filter == ur$filter, ]
    sub <- sub[order(sub$week), ]
    if (nrow(sub) == 0) { cat("SKIP:", ur$group, ur$filter, "(no data)\n"); next }
    for (ms in names(MILESTONES)) {
      cat(sprintf("  %s %s / %s ... ", ur$group, ur$filter, ms))
      r <- run_ci(sub$new_users, sub$week, MILESTONES[[ms]])
      cat(fmt(r), "\n")
      results <- rbind(results, data.frame(group = ur$group, filter = ur$filter,
        column = "Users", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table3_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table3_reproduced.csv (%d rows)\n", nrow(results)))
print(results, row.names = FALSE)
