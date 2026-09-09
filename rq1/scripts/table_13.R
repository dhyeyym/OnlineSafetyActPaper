library(CausalImpact)
library(zoo)

DATA_DIR <- "rq1/data"
MILESTONES <- list(Oct2023 = as.Date("2023-10-23"), Mar2025 = as.Date("2025-03-17"), Jul2025 = as.Date("2025-07-21"))

snap_to_week <- function(target, weeks) {
  candidates <- weeks[weeks >= target]
  if (length(candidates) > 0) return(min(candidates))
  return(max(weeks[weeks < target]))
}

run_ci <- function(y, weeks, treatment_target) {
  td <- snap_to_week(treatment_target, weeks)
  pre_end <- td - 7; post_end <- td + 7 * 7
  idx <- weeks >= min(weeks) & weeks <= post_end
  s <- zoo(y[idx], order.by = weeks[idx])
  if (length(unique(y[idx])) <= 1) return(c(NA, NA))
  set.seed(20260827)
  tryCatch({
    ci <- CausalImpact(s, c(min(weeks), pre_end), c(td, post_end))
    avg <- ci$summary["Average", ]
    c(round(avg[["RelEffect"]] * 100, 1), round(avg[["p"]], 4))
  }, error = function(e) c(NA, NA))
}

weekly <- read.csv(file.path(DATA_DIR, "table13_weekly_series.csv"), stringsAsFactors = FALSE)
weekly$week <- as.Date(weekly$week)
groups <- c("VPN", "Politics")
filters <- c("Unmatched (non-UK)", "Unmatched", "Unmatched (UK)", "Raw", "Raw (UK)",
             "Matched", "Matched (UK)", "Classified", "Classified (UK)")
metrics <- c("posts", "comments", "total")

total <- length(groups) * length(filters) * length(metrics) * length(MILESTONES)

results <- data.frame(); count <- 0
for (grp in groups) {
  for (filt in filters) {
    sub <- weekly[weekly$group == grp & weekly$filter == filt, ]
    sub <- sub[order(sub$week), ]
    if (nrow(sub) == 0) next
    for (ms in names(MILESTONES)) {
      for (met in metrics) {
        count <- count + 1
        cat(sprintf("[%3d/%d] %s | %s | %s | %s ... ", count, total, grp, filt, met, ms))
        r <- run_ci(sub[[met]], sub$week, MILESTONES[[ms]])
        if (!is.na(r[1])) {
          sig <- ifelse(r[2] < 0.05, "**", ifelse(r[2] < 0.10, "*", ""))
          cat(sprintf("%+.0f%%%s\n", r[1], sig))
        } else cat("NA\n")
        results <- rbind(results, data.frame(group = grp, filter = filt, metric = met,
          milestone = ms, relative_effect_pct = r[1], p_value = r[2]))
      }
    }
  }
}
write.csv(results, file.path(DATA_DIR, "table13_reproduced.csv"), row.names = FALSE)
cat(sprintf("\nSaved: table13_reproduced.csv (%d rows)\n", nrow(results)))
