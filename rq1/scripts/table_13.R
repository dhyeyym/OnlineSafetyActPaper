library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)

MILESTONES <- list(Oct2023 = as.Date("2023-10-23"), Mar2025 = as.Date("2025-03-17"), Jul2025 = as.Date("2025-07-21"))

groups <- c("VPN", "Politics")
filters <- c("Unmatched (non-UK)", "Unmatched", "Unmatched (UK)", "Raw", "Raw (UK)",
             "Matched", "Matched (UK)", "Classified", "Classified (UK)")
metrics <- c("posts", "comments", "total")

run_ci <- function(y, weeks, post_start) {
  pre_start <- min(weeks)
  pre_end <- post_start - 7
  post_end <- post_start + 7 * 7
  idx <- weeks >= pre_start & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  if (sum(weeks >= post_start & weeks <= post_end) != 8) return(c(NA, NA))
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  ci <- CausalImpact(s, c(pre_start, pre_end), c(post_start, post_end))
  avg <- ci$summary["Average", ]
  c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
}

total <- length(groups) * length(filters) * length(metrics) * length(MILESTONES)
cat(sprintf("Running %d Table 13 models...\n\n", total))

results <- data.frame()
count <- 0

for (grp in groups) {
  for (filt in filters) {
    sub <- weekly[weekly$group == grp & weekly$filter == filt, ]
    sub <- sub[order(sub$week), ]
    if (nrow(sub) == 0) next
    for (ms in names(MILESTONES)) {
      for (met in metrics) {
        count <- count + 1
        cat(sprintf("[%3d/%d] %s | %s | %s | %s ... ", count, total, grp, filt, met, ms))
        r <- tryCatch(run_ci(sub[[met]], sub$week, MILESTONES[[ms]]), error = function(e) c(NA, NA))
        if (!is.na(r[1])) {
          sig <- ifelse(!is.na(r[2]) & r[2] < 0.05, "**", ifelse(!is.na(r[2]) & r[2] < 0.10, "*", ""))
          cat(sprintf("%+.0f%%%s\n", r[1], sig))
        } else { cat("ERROR\n") }
        results <- rbind(results, data.frame(group = grp, filter = filt, metric = met,
                                              milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
      }
    }
  }
}

write.csv(results, file.path(DATA_DIR, "table13_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: %s (%d rows)\n", file.path(DATA_DIR, "table13_reproduced.csv"), nrow(results)))
