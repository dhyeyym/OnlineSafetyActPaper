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
  if (length(candidates) > 0) {
    return(min(candidates))
  }
  return(max(weeks[weeks < target]))
}

fit_causal_impact <- function(data, weeks, treatment_target) {
  treatment_week <- snap_to_week(treatment_target, weeks)
  pre_end <- treatment_week - 7
  post_end <- treatment_week + 7 * 7

  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(data, c(min(weeks), pre_end), c(treatment_week, post_end))
    average <- ci$summary["Average", ]
    c(round(average[["RelEffect"]] * 100, 1), round(average[["p"]], 4))
  }, error = function(e) {
    cat("  ERR:", conditionMessage(e), "\n")
    c(NA, NA)
  })
}

run_ci_vec <- function(y, weeks, treatment_target) {
  series <- zoo(y, order.by = weeks)
  fit_causal_impact(series, weeks, treatment_target)
}

run_ci_cov <- function(y, covariate, weeks, treatment_target) {
  series <- zoo(data.frame(y = y, x = covariate), order.by = weeks)
  fit_causal_impact(series, weeks, treatment_target)
}

significance_stars <- function(p) {
  if (is.na(p)) {
    return("")
  }
  if (p < 0.05) {
    return("**")
  }
  if (p < 0.10) {
    return("*")
  }
  return("")
}

format_result <- function(r) {
  if (is.na(r[1])) {
    return("NA")
  }
  sprintf("%+.1f%%%s", r[1], significance_stars(r[2]))
}

result_row <- function(spec, milestone, r) {
  data.frame(spec = spec, milestone = milestone, relative_effect_pct = r[1], p_value = r[2])
}

gt_uk <- read.csv(file.path(DATA_DIR, "google_trends_uk.csv"), stringsAsFactors = FALSE, check.names = FALSE)
gt_us <- read.csv(file.path(DATA_DIR, "google_trends_us.csv"), stringsAsFactors = FALSE, check.names = FALSE)

names(gt_uk) <- trimws(names(gt_uk))
names(gt_us) <- trimws(names(gt_us))

gt_uk$week <- as.Date(gt_uk$week)
gt_us$week <- as.Date(gt_us$week)

merged <- merge(gt_uk, gt_us, by = "week")

gt_uk$vpn_lag52 <- c(rep(NA, 52), gt_uk$vpn[1:(nrow(gt_uk) - 52)])
has_lag <- !is.na(gt_uk$vpn_lag52)

results <- data.frame()

for (milestone in names(GT_MILESTONES)) {
  target <- GT_MILESTONES[[milestone]]

  cat(sprintf("  No covariate / %s ... ", milestone))
  r <- run_ci_vec(gt_uk$vpn, gt_uk$week, target)
  cat(format_result(r), "\n")
  results <- rbind(results, result_row("No covariate", milestone, r))

  cat(sprintf("  US covariate / %s ... ", milestone))
  r <- run_ci_cov(merged$vpn, merged$vpn_us, merged$week, target)
  cat(format_result(r), "\n")
  results <- rbind(results, result_row("US covariate", milestone, r))

  cat(sprintf("  Lag-52 / %s ... ", milestone))
  r <- run_ci_cov(gt_uk$vpn[has_lag], gt_uk$vpn_lag52[has_lag], gt_uk$week[has_lag], target)
  cat(format_result(r), "\n")
  results <- rbind(results, result_row("Lag-52", milestone, r))
}

write.csv(results, file.path(DATA_DIR, "table4_reproduced.csv"), row.names = FALSE)
cat("\nSaved: table4_reproduced.csv\n")
print(results, row.names = FALSE)

cat("\nMAIN RESULT 2: Google Trends at Age Verification deadline\n")
cat("Paper values:  No covariate +147%  |  US covariate +135%  |  Lag-52 +144%\n")
cat("\n")

paper_values <- data.frame(
  spec = c("No covariate", "US covariate", "Lag-52"),
  paper = c(147, 135, 144),
  stringsAsFactors = FALSE
)

for (i in 1:nrow(paper_values)) {
  expected <- paper_values[i, ]
  row <- results[results$spec == expected$spec & results$milestone == "Jul2025", ]

  if (nrow(row) > 0) {
    ours <- row$relative_effect_pct[1]
    relative_difference <- abs(ours - expected$paper) / abs(expected$paper) * 100

    cat(paste0(
      "  >>> ", expected$spec,
      ": current script=", sprintf("%+.1f", ours),
      "%  paper=", sprintf("%+.0f", expected$paper),
      "%  (", sprintf("%.1f", relative_difference), "% off)\n"
    ))
  }
}
