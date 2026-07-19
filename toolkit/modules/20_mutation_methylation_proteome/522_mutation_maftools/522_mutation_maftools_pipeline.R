#!/usr/bin/env Rscript

# Minimal maftools mutation summary pipeline.

parse_args <- function() {
  args <- commandArgs(trailingOnly = TRUE)
  out <- list()
  i <- 1
  while (i <= length(args)) {
    key <- sub("^--", "", args[[i]])
    val <- if (i + 1 <= length(args) && !grepl("^--", args[[i + 1]])) args[[i + 1]] else TRUE
    out[[key]] <- val
    i <- i + if (isTRUE(val)) 1 else 2
  }
  out
}

args <- parse_args()
if (is.null(args$maf) || is.null(args$outdir)) {
  stop("Usage: Rscript mutation_maftools_pipeline.R --maf cohort.maf --outdir results/mutation")
}
if (!requireNamespace("maftools", quietly = TRUE)) stop("Package 'maftools' is required.")

dir.create(args$outdir, recursive = TRUE, showWarnings = FALSE)
maf <- maftools::read.maf(args$maf)
summary <- maftools::getSampleSummary(maf)
genes <- maftools::getGeneSummary(maf)
write.csv(summary, file.path(args$outdir, "maf_sample_summary.csv"), row.names = FALSE)
write.csv(genes, file.path(args$outdir, "maf_gene_summary.csv"), row.names = FALSE)

# 出 PNG(Bio Wingman 结果区展示;原为 PDF)+ 同时留 PDF 矢量
png(file.path(args$outdir, "maf_oncoplot_top30.png"), width = 1100, height = 900, res = 120)
maftools::oncoplot(maf = maf, top = 30)
dev.off()
pdf(file.path(args$outdir, "maf_oncoplot_top30.pdf"), width = 10, height = 8)
maftools::oncoplot(maf = maf, top = 30)
dev.off()

png(file.path(args$outdir, "maf_summary_plot.png"), width = 1100, height = 900, res = 120)
maftools::plotmafSummary(maf = maf, rmOutlier = TRUE, addStat = "median")
dev.off()
pdf(file.path(args$outdir, "maf_summary_plot.pdf"), width = 10, height = 8)
maftools::plotmafSummary(maf = maf, rmOutlier = TRUE, addStat = "median")
dev.off()
