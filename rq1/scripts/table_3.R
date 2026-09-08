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
  sprintf("%+.1f%%%s", r[1], sig)
}

# ================================================================
# CONTENT — from table13_weekly_series.csv
# Paper Table 3 rows: Raw, Raw (UK), Classified, Classified (UK)
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
    r <- tryCatch(run_ci(sub$total, sub$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
    cat(fmt(r), "\n")
    results <- rbind(results, data.frame(
      group = cr$group, filter = cr$filter, column = "Content",
      milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
  }
}

# ================================================================
# USERS — from individual user timeseries files (new_users metric)
# ================================================================
cat("\n================================================================\n")
cat("TABLE 3 — Users (new_users)\n")
cat("================================================================\n\n")

user_rows <- list(
  list(label = "VPN",      filter = "Raw",              file = "vpn_user_timeseries.csv"),
  list(label = "VPN",      filter = "Raw (UK)",         file = "vpn_uk_user_timeseries.csv"),
  list(label = "VPN",      filter = "Classified",       file = "vpn_user_timeseries.csv"),
  list(label = "VPN",      filter = "Classified (UK)",  file = "vpn_user_timeseries_uk_filtered.csv"),
  list(label = "Politics", filter = "Raw",              file = "politics_user_timeseries.csv"),
  list(label = "Politics", filter = "Raw (UK)",         file = "politics_uk_user_timeseries.csv"),
  list(label = "Politics", filter = "Classified",       file = "politics_user_timeseries.csv"),
  list(label = "Politics", filter = "Classified (UK)",  file = "politics_user_timeseries_uk_filtered.csv")
)

for (ur in user_rows) {
  path <- file.path(DATA_DIR, ur$file)
  if (!file.exists(path)) { cat("SKIP:", ur$label, ur$filter, "(", ur$file, ")\n"); next }
  df <- read.csv(path, stringsAsFactors = FALSE)
  df$week <- as.Date(df$week)
  df <- df[order(df$week), ]

  for (ms in names(MILESTONES)) {
    cat(sprintf("  %s %s / %s ... ", ur$label, ur$filter, ms))
    r <- tryCatch(run_ci(df$new_users, df$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
    cat(fmt(r), "\n")
    results <- rbind(results, data.frame(
      group = ur$label, filter = ur$filter, column = "Users",
      milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
  }
}

write.csv(results, file.path(DATA_DIR, "table3_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table3_reproduced.csv (%d rows)\n", nrow(results)))
print(results, row.names = FALSE)