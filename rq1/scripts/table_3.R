library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(
  Oct2023 = as.Date("2023-10-23"),
  Mar2025 = as.Date("2025-03-17"),
  Jul2025 = as.Date("2025-07-21")
)

SERIES <- list(
  list(group = "VPN", filter = "Raw"),
  list(group = "VPN", filter = "Raw (UK)"),
  list(group = "VPN", filter = "Classified"),
  list(group = "VPN", filter = "Classified (UK)"),
  list(group = "Politics", filter = "Raw"),
  list(group = "Politics", filter = "Raw (UK)"),
  list(group = "Politics", filter = "Classified"),
  list(group = "Politics", filter = "Classified (UK)")
)

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) {
    return(min(candidates))
  }
  return(max(weeks[weeks < target]))
}

run_ci <- function(y, weeks, treatment_target) {
  treatment_week <- snap_to_week(treatment_target, weeks)
  pre_end <- treatment_week - 7
  post_end <- treatment_week + 7 * 7

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
    cat("  ERR:", conditionMessage(e), "\n")
    c(NA, NA)
  })
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

run_series <- function(weekly, metric, column_label, skip_note) {
  rows <- data.frame()

  for (s in SERIES) {
    sub <- weekly[weekly$group == s$group & weekly$filter == s$filter, ]
    sub <- sub[order(sub$week), ]

    if (nrow(sub) == 0) {
      cat("SKIP:", s$group, s$filter, skip_note)
      next
    }

    for (milestone in names(MILESTONES)) {
      cat(sprintf("  %s %s / %s ... ", s$group, s$filter, milestone))
      r <- run_ci(sub[[metric]], sub$week, MILESTONES[[milestone]])
      cat(format_result(r), "\n")

      rows <- rbind(rows, data.frame(
        group = s$group,
        filter = s$filter,
        column = column_label,
        milestone = milestone,
        relative_effect_pct = r[1],
        p_value = r[2]
      ))
    }
  }

  rows
}

cat("TABLE 3 — Content (posts + comments)\n")

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

results <- run_series(weekly, "total", "Content", "\n")

cat("TABLE 3 — Users (new_users)\n")

user_file <- file.path(DATA_DIR, "table12_user_weekly_series.csv")

if (!file.exists(user_file)) {
  cat("WARNING: table12_user_weekly_series.csv not found.\n")
  cat("Run build_user_timeseries.py first.\n")
} else {
  user_weekly <- read.csv(user_file, stringsAsFactors = FALSE)
  user_weekly$week <- as.Date(user_weekly$week)

  results <- rbind(results, run_series(user_weekly, "new_users", "Users", "(no data)\n"))
}

write.csv(results, file.path(DATA_DIR, "table3_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table3_reproduced.csv (%d rows)\n", nrow(results)))
print(results, row.names = FALSE)

cat("\nMAIN RESULT 1: Age Verification effect on classified content\n")
cat("Paper values:  VPN Classified +328%  |  VPN Cls(UK) +1265%  |  Politics Classified +1474%\n")
cat("\n")

paper_values <- data.frame(
  group = c("VPN", "VPN", "Politics", "Politics"),
  filter = c("Classified", "Classified (UK)", "Classified", "Classified (UK)"),
  column = c("Content", "Content", "Content", "Content"),
  paper = c(328, 1265, 1474, 1481),
  stringsAsFactors = FALSE
)

for (i in 1:nrow(paper_values)) {
  expected <- paper_values[i, ]
  row <- results[results$group == expected$group &
                 results$filter == expected$filter &
                 results$column == expected$column &
                 results$milestone == "Jul2025", ]

  if (nrow(row) > 0) {
    ours <- row$relative_effect_pct[1]
    relative_difference <- abs(ours - expected$paper) / abs(expected$paper) * 100

    cat(paste0(
      "  >>> ", expected$group, " ", expected$filter,
      ": current script=", sprintf("%+.1f", ours),
      "%  paper=", sprintf("%+.0f", expected$paper),
      "%  (", sprintf("%.1f", relative_difference), "% off)\n"
    ))
  }
}
