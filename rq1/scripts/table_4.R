library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

GT_MILESTONES <- list(
  Oct2023 = as.Date("2023-10-22"),
  Mar2025 = as.Date("2025-03-16"),
  Jul2025 = as.Date("2025-07-20")
)

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) return(min(candidates))
  return(max(weeks[weeks < target]))
}

run_ci_vec <- function(y, weeks, treatment_target) {
  td <- snap_to_week(treatment_target, weeks)
  pre_end <- td - 7; post_end <- td + 7 * 7
  s <- zoo(y, order.by = weeks)
  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(s, c(min(weeks), pre_end), c(td, post_end))
    avg <- ci$summary["Average", ]
    c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
  }, error = function(e) { cat("  ERR:", conditionMessage(e), "\n"); c(NA, NA) })
}

run_ci_cov <- function(y, cov, weeks, treatment_target) {
  td <- snap_to_week(treatment_target, weeks)
  pre_end <- td - 7; post_end <- td + 7 * 7
  d <- zoo(data.frame(y = y, x = cov), order.by = weeks)
  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(d, c(min(weeks), pre_end), c(td, post_end))
    avg <- ci$summary["Average", ]
    c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
  }, error = function(e) { cat("  ERR:", conditionMessage(e), "\n"); c(NA, NA) })
}

fmt <- function(r) {
  if (is.na(r[1])) return("NA")
  sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
  sprintf("%+.1f%%%s", r[1], sig)
}

gt_uk <- read.csv(file.path(DATA_DIR, "google_trends_uk.csv"), stringsAsFactors = FALSE, check.names = FALSE)
gt_us <- read.csv(file.path(DATA_DIR, "google_trends_us.csv"), stringsAsFactors = FALSE, check.names = FALSE)
names(gt_uk) <- trimws(names(gt_uk)); names(gt_us) <- trimws(names(gt_us))
gt_uk$week <- as.Date(gt_uk$week); gt_us$week <- as.Date(gt_us$week)
merged <- merge(gt_uk, gt_us, by = "week")
gt_uk$vpn_lag52 <- c(rep(NA, 52), gt_uk$vpn[1:(nrow(gt_uk) - 52)])
lag_valid <- !is.na(gt_uk$vpn_lag52)

results <- data.frame()
for (ms in names(GT_MILESTONES)) {
  cat(sprintf("  No covariate / %s ... ", ms))
  r <- run_ci_vec(gt_uk$vpn, gt_uk$week, GT_MILESTONES[[ms]]); cat(fmt(r), "\n")
  results <- rbind(results, data.frame(spec = "No covariate", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))

  cat(sprintf("  US covariate / %s ... ", ms))
  r <- run_ci_cov(merged$vpn, merged$vpn_us, merged$week, GT_MILESTONES[[ms]]); cat(fmt(r), "\n")
  results <- rbind(results, data.frame(spec = "US covariate", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))

  cat(sprintf("  Lag-52 / %s ... ", ms))
  r <- run_ci_cov(gt_uk$vpn[lag_valid], gt_uk$vpn_lag52[lag_valid], gt_uk$week[lag_valid], GT_MILESTONES[[ms]]); cat(fmt(r), "\n")
  results <- rbind(results, data.frame(spec = "Lag-52", milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
}

write.csv(results, file.path(DATA_DIR, "table4_reproduced.csv"), row.names = FALSE)
cat("\nSaved: table4_reproduced.csv\n")
print(results, row.names = FALSE)



# ================================================================
# MAIN RESULT 2 — Google Trends Confirms the Displacement
# Paper: No covariate +147%, US covariate +135%, Lag-52 +144%
# ================================================================
cat("\n================================================================\n")
cat("MAIN RESULT 2: Google Trends at Age Verification deadline\n")
cat("Paper values:  No covariate +147%  |  US covariate +135%  |  Lag-52 +144%\n")
cat("================================================================\n")
paper_vals <- data.frame(
  spec = c("No covariate", "US covariate", "Lag-52"),
  paper = c(147, 135, 144),
  stringsAsFactors = FALSE
)
for (i in 1:nrow(paper_vals)) {
  pv <- paper_vals[i, ]
  row <- results[results$spec == pv$spec & results$milestone == "Jul2025", ]
  if (nrow(row) > 0) {
    ours <- row$relative_effect_pct[1]
    rel_diff <- abs(ours - pv$paper) / abs(pv$paper) * 100
    cat(paste0("  >>> ", pv$spec, ": current script=", sprintf("%+.1f", ours),
               "%  paper=", sprintf("%+.0f", pv$paper),
               "%  (", sprintf("%.1f", rel_diff), "% off)\n"))
  }
}
cat("================================================================\n")
