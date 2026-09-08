library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

gt_uk <- read.csv(file.path(DATA_DIR, "google_trends_uk.csv"), stringsAsFactors = FALSE, check.names = FALSE)
names(gt_uk) <- trimws(names(gt_uk))
gt_uk$week <- as.Date(gt_uk$week)

run_ci <- function(y, weeks, post_start) {
  pre_start <- min(weeks)
  pre_end <- post_start - 7
  post_end <- post_start + 7 * 7
  s <- zoo(y, order.by = weeks)
  set.seed(20260827)
  ci <- CausalImpact(s, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

# ================================================================
# Table 14: Placebo-date pre-trend test
# ================================================================
cat("TABLE 14 — Placebo-date pre-trend test\n\n")

placebo_dates <- list(
  "12 weeks before" = as.Date("2025-04-27"),
  "10 weeks before" = as.Date("2025-05-11"),
  "8 weeks before"  = as.Date("2025-05-25"),
  "6 weeks before"  = as.Date("2025-06-08"),
  "4 weeks before"  = as.Date("2025-06-22")
)

t14 <- data.frame()
for (label in names(placebo_dates)) {
  d <- placebo_dates[[label]]
  cat(sprintf("  %s (%s) ... ", label, d))
  r <- tryCatch(run_ci(gt_uk$vpn, gt_uk$week, d), error = function(e) c(NA, NA))
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  cat(sprintf("%+.1f%%%s (p=%.2f)\n", r[1], sig, r[2]))
  t14 <- rbind(t14, data.frame(fake_date = as.character(d), weeks_before = label,
                                relative_effect_pct = r[1], p_value = r[2]))
}
write.csv(t14, file.path(DATA_DIR, "table14_reproduced.csv"), row.names = FALSE)

# ================================================================
# Table 15: Date-sensitivity test
# ================================================================
cat("\nTABLE 15 — Date-sensitivity test\n\n")

# All platform dates fall in same Sunday-indexed GT week (20 Jul)
compliance_dates <- list(
  "Discord (21 Jul)"  = as.Date("2025-07-20"),
  "Aylo (24 Jul)"     = as.Date("2025-07-20"),
  "Reddit (25 Jul)"   = as.Date("2025-07-20"),
  "X (26 Jul)"        = as.Date("2025-07-20")
)

t15 <- data.frame()
for (label in names(compliance_dates)) {
  d <- compliance_dates[[label]]
  cat(sprintf("  %s ... ", label))
  r <- tryCatch(run_ci(gt_uk$vpn, gt_uk$week, d), error = function(e) c(NA, NA))
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", "")
  cat(sprintf("%+.1f%%%s\n", r[1], sig))
  t15 <- rbind(t15, data.frame(treatment_date = label, relative_effect_pct = r[1], p_value = r[2]))
}
write.csv(t15, file.path(DATA_DIR, "table15_reproduced.csv"), row.names = FALSE)

cat("\nSaved table14_reproduced.csv and table15_reproduced.csv\n")
