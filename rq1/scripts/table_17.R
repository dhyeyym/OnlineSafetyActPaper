library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

MILESTONES <- list(
  Oct2023 = as.Date("2023-10-23"),
  Mar2025 = as.Date("2025-03-17"),
  Jul2025 = as.Date("2025-07-21")
)

GROUPS <- c("VPN", "Politics")
DEFINITIONS <- c("Raw", "Classified")
THRESHOLDS <- 1:5

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

weekly <- read.csv(file.path(DATA_DIR, "table17_weekly_series.csv"), stringsAsFactors = FALSE, check.names = FALSE)
weekly$week <- as.Date(weekly$week)
weekly$k <- as.integer(weekly$k)

total <- length(GROUPS) * length(DEFINITIONS) * length(THRESHOLDS) * length(MILESTONES)
cat(sprintf("Running %d Table 17 models...\n\n", total))

results <- data.frame()
count <- 0

for (group in GROUPS) {
  for (definition in DEFINITIONS) {
    for (k in THRESHOLDS) {
      sub <- weekly[weekly$group == group & weekly$definition == definition & weekly$k == k, ]
      sub <- sub[order(sub$week), ]

      if (nrow(sub) == 0) {
        next
      }

      for (milestone in names(MILESTONES)) {
        count <- count + 1
        cat(sprintf("[%2d/%d] %s | %s | k>=%d | %s ... ", count, total, group, definition, k, milestone))

        r <- run_ci(sub$total, sub$week, MILESTONES[[milestone]])

        if (!is.na(r[1])) {
          cat(sprintf("%+.1f%%%s\n", r[1], significance_stars(r[2])))
        } else {
          cat("NA\n")
        }

        results <- rbind(results, data.frame(
          group = group,
          definition = definition,
          k = k,
          milestone = milestone,
          relative_effect_pct = r[1],
          p_value = r[2]
        ))
      }
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table17_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table17_reproduced.csv (%d rows)\n", nrow(results)))
