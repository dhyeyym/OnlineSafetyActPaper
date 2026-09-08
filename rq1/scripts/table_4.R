library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

gt_uk <- read.csv(file.path(DATA_DIR, "google_trends_uk.csv"), stringsAsFactors = FALSE, check.names = FALSE)
gt_us <- read.csv(file.path(DATA_DIR, "google_trends_us.csv"), stringsAsFactors = FALSE, check.names = FALSE)
names(gt_uk) <- trimws(names(gt_uk))
names(gt_us) <- trimws(names(gt_us))
gt_uk$week <- as.Date(gt_uk$week)
gt_us$week <- as.Date(gt_us$week)

# Google Trends weeks are Sundays
MILESTONES <- list(Oct2023 = as.Date("2023-10-22"), Mar2025 = as.Date("2025-03-16"), Jul2025 = as.Date("2025-07-20"))

run_ci_nocov <- function(y, weeks, post_start) {
  pre_start <- min(weeks)
  pre_end <- post_start - 7
  post_end <- post_start + 7 * 7
  s <- zoo(y, order.by = weeks)
  set.seed(20260827)
  ci <- CausalImpact(s, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

run_ci_cov <- function(y, cov, weeks, post_start) {
  pre_start <- min(weeks)
  pre_end <- post_start - 7
  post_end <- post_start + 7 * 7
  d <- zoo(data.frame(y = y, x = cov), order.by = weeks)
  set.seed(20260827)
  ci <- CausalImpact(d, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

# Lag-52 covariate
gt_uk$vpn_lag52 <- c(rep(NA, 52), gt_uk$vpn[1:(nrow(gt_uk) - 52)])

# Merge US
merged <- merge(gt_uk, gt_us, by = "week")

results <- data.frame()

# No covariate
for (ms in names(MILESTONES)) {
  cat(sprintf("  No covariate / %s ... ", ms))
  r <- tryCatch(run_ci_nocov(gt_uk$vpn, gt_uk$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  cat(sprintf("%+.1f%%%s\n", r[1], sig))
  results <- rbind(results, data.frame(spec = "No covariate", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
}

# US covariate
for (ms in names(MILESTONES)) {
  cat(sprintf("  US covariate / %s ... ", ms))
  r <- tryCatch(run_ci_cov(merged$vpn, merged$vpn_us, merged$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  cat(sprintf("%+.1f%%%s\n", r[1], sig))
  results <- rbind(results, data.frame(spec = "US covariate", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
}

# Lag-52 covariate
lag_valid <- !is.na(gt_uk$vpn_lag52)
for (ms in names(MILESTONES)) {
  cat(sprintf("  Lag-52 / %s ... ", ms))
  r <- tryCatch(run_ci_cov(gt_uk$vpn[lag_valid], gt_uk$vpn_lag52[lag_valid], gt_uk$week[lag_valid], MILESTONES[[ms]]),
                error = function(e) c(NA, NA))
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  cat(sprintf("%+.1f%%%s\n", r[1], sig))
  results <- rbind(results, data.frame(spec = "Lag-52", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
}

write.csv(results, file.path(DATA_DIR, "table4_reproduced.csv"), row.names = FALSE)
cat("\nSaved:", file.path(DATA_DIR, "table4_reproduced.csv"), "\n")
print(results, row.names = FALSE)
