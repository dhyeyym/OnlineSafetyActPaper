library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(
  Oct2023 = as.Date("2023-10-23"),
  Mar2025 = as.Date("2025-03-17"),
  Jul2025 = as.Date("2025-07-21")
)

GROUPS <- c("VPN", "Politics")
FILTERS <- c(
  "Unmatched (non-UK)", "Unmatched", "Unmatched (UK)",
  "Raw", "Raw (UK)", "Matched", "Matched (UK)",
  "Classified", "Classified (UK)"
)
METRICS <- c("unique_users", "new_users", "cumulative_users")

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
  sprintf("%+.0f%%%s", r[1], significance_stars(r[2]))
}

weekly <- read.csv(file.path(DATA_DIR, "table12_user_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

total <- length(GROUPS) * length(FILTERS) * length(METRICS) * length(MILESTONES)
cat(sprintf("TABLE 12 — Running %d models...\n\n", total))

results <- data.frame()
count <- 0

for (group in GROUPS) {
  for (filter_name in FILTERS) {
    sub <- weekly[weekly$group == group & weekly$filter == filter_name, ]
    sub <- sub[order(sub$week), ]

    if (nrow(sub) == 0) {
      cat("SKIP:", group, filter_name, "\n")
      next
    }

    for (metric in METRICS) {
      if (!(metric %in% names(sub))) {
        next
      }

      for (milestone in names(MILESTONES)) {
        count <- count + 1
        cat(sprintf("[%3d/%d] %s | %s | %s | %s ... ", count, total, group, filter_name, metric, milestone))

        r <- run_ci(sub[[metric]], sub$week, MILESTONES[[milestone]])
        cat(format_result(r), "\n")

        results <- rbind(results, data.frame(
          group = group,
          filter = filter_name,
          metric = metric,
          milestone = milestone,
          relative_effect_pct = r[1],
          p_value = r[2]
        ))
      }
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table12_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table12_reproduced.csv (%d rows)\n", nrow(results)))
