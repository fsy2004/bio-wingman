#!/usr/bin/env Rscript

# Metabolomics differential matrix template.

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
if (is.null(args$metabolite_matrix) || is.null(args$metadata) || is.null(args$group_col) || is.null(args$outdir)) {
  stop("Usage: Rscript metabolomics_metaboanalystR_pipeline.R --metabolite_matrix metabolite.tsv --metadata meta.tsv --group_col group --outdir results/metabolomics")
}

dir.create(args$outdir, recursive = TRUE, showWarnings = FALSE)
sep1 <- if (grepl("\\.csv$", args$metabolite_matrix, ignore.case = TRUE)) "," else "\t"
sep2 <- if (grepl("\\.csv$", args$metadata, ignore.case = TRUE)) "," else "\t"
mat <- as.matrix(read.table(args$metabolite_matrix, header = TRUE, row.names = 1, sep = sep1, check.names = FALSE))
meta <- read.table(args$metadata, header = TRUE, row.names = 1, sep = sep2, check.names = FALSE)
common <- intersect(colnames(mat), rownames(meta))
mat <- mat[, common, drop = FALSE]
meta <- meta[common, , drop = FALSE]
group <- factor(meta[[args$group_col]])
if (nlevels(group) != 2) stop("This minimal template currently expects exactly two groups.")

pvals <- apply(mat, 1, function(v) t.test(v[group == levels(group)[2]], v[group == levels(group)[1]])$p.value)
logfc <- rowMeans(mat[, group == levels(group)[2], drop = FALSE], na.rm = TRUE) -
  rowMeans(mat[, group == levels(group)[1], drop = FALSE], na.rm = TRUE)
res <- data.frame(metabolite = rownames(mat), logFC = logfc, pvalue = pvals, padj = p.adjust(pvals, "BH"))
res <- res[order(res$padj), ]
write.csv(res, file.path(args$outdir, "differential_metabolites.csv"), row.names = FALSE)

# ---- 补图(Bio Wingman):火山图 + Top 差异代谢物热图 ----
suppressWarnings(suppressMessages(library(ggplot2)))
res$sig <- ifelse(res$padj < 0.05, ifelse(res$logFC > 0, "Up (case)", "Down (case)"), "NS")
.pv <- ggplot(res, aes(logFC, -log10(padj), color = sig)) +
  geom_point(size = 1.2, alpha = 0.8) +
  scale_color_manual(values = c("Up (case)" = "#CC79A7", "Down (case)" = "#0072B2", "NS" = "grey80")) +
  labs(x = "logFC (case - control)", y = "-log10(adj.P)", title = "Differential metabolites", color = NULL) +
  theme_bw(base_size = 11) + theme(panel.grid = element_blank())
ggsave(file.path(args$outdir, "volcano.png"), .pv, width = 6.5, height = 5.5, dpi = 200)
.top <- head(res$metabolite[order(res$padj)], 30)
if (length(.top) >= 2 && requireNamespace("pheatmap", quietly = TRUE)) {
  .ann <- data.frame(group = group); rownames(.ann) <- colnames(mat)
  png(file.path(args$outdir, "heatmap_top.png"), width = 1000, height = 900, res = 120)
  pheatmap::pheatmap(mat[.top, , drop = FALSE], annotation_col = .ann, scale = "row",
                     show_rownames = TRUE, fontsize_row = 6, main = "Top 30 differential metabolites")
  dev.off()
}
