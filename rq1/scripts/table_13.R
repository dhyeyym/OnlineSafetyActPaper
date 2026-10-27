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
  "Unmatched (non-UK)", "Unmatched", "Unmatched (UK)", "Raw", "Raw (UK)",
  "Matched", "Matched (UK)", "Classified", "Classified (UK)"
)
METRICS <- c("posts", "comments", "total")

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

total <- length(GROUPS) * length(FILTERS) * length(METRICS) * length(MILESTONES)

results <- data.frame()
count <- 0

for (group in GROUPS) {
  for (filter_name in FILTERS) {
    sub <- weekly[weekly$group == group & weekly$filter == filter_name, ]
    sub <- sub[order(sub$week), ]

    if (nrow(sub) == 0) {
      next
    }

    for (milestone in names(MILESTONES)) {
      for (metric in METRICS) {
        count <- count + 1
        cat(sprintf("[%3d/%d] %s | %s | %s | %s ... ", count, total, group, filter_name, metric, milestone))

        r <- run_ci(sub[[metric]], sub$week, MILESTONES[[milestone]])

        if (!is.na(r[1])) {
          cat(sprintf("%+.0f%%%s\n", r[1], significance_stars(r[2])))
        } else {
          cat("NA\n")
        }

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

write.csv(results, file.path(DATA_DIR, "table13_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table13_reproduced.csv (%d rows)\n", nrow(results)))

cat("\nMAIN RESULT 3: Classified content at Age Verification (Jul 2025, total)\n")
cat("\n")

paper_values <- data.frame(
  group = c("VPN", "VPN", "VPN", "VPN", "Politics", "Politics", "Politics", "Politics"),
  filter = c(
    "Classified", "Classified (UK)", "Raw", "Matched",
    "Classified", "Classified (UK)", "Raw", "Matched"
  ),
  paper = c(328, 1265, 75, 82, 1474, 1481, -7, 121),
  stringsAsFactors = FALSE
)

for (i in 1:nrow(paper_values)) {
  expected <- paper_values[i, ]
  row <- results[results$group == expected$group &
                 results$filter == expected$filter &
                 results$metric == "total" &
                 results$milestone == "Jul2025", ]

  if (nrow(row) > 0) {
    ours <- row$relative_effect_pct[1]
    denominator <- max(abs(expected$paper), 1)
    relative_difference <- abs(ours - expected$paper) / denominator * 100
    label <- paste0(expected$group, " ", expected$filter)

    cat(paste0(
      "  >>> ", formatC(label, width = -25),
      ": current script=", sprintf("%+.1f", ours),
      "%  paper=", sprintf("%+.0f", expected$paper),
      "%  (", sprintf("%.1f", relative_difference), "% off)\n"
    ))
  }
}
