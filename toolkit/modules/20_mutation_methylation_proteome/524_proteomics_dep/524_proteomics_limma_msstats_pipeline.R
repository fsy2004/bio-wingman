#!/usr/bin/env Rscript

# Protein matrix differential analysis template with limma.

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
if (is.null(args$protein_matrix) || is.null(args$metadata) || is.null(args$group_col) || is.null(args$outdir)) {
  stop("Usage: Rscript proteomics_limma_msstats_pipeline.R --protein_matrix protein.tsv --metadata meta.tsv --group_col group --outdir results/proteomics")
}
if (!requireNamespace("limma", quietly = TRUE)) stop("Package 'limma' is required.")

dir.create(args$outdir, recursive = TRUE, showWarnings = FALSE)
sep1 <- if (grepl("\\.csv$", args$protein_matrix, ignore.case = TRUE)) "," else "\t"
sep2 <- if (grepl("\\.csv$", args$metadata, ignore.case = TRUE)) "," else "\t"
mat <- as.matrix(read.table(args$protein_matrix, header = TRUE, row.names = 1, sep = sep1, check.names = FALSE))
meta <- read.table(args$metadata, header = TRUE, row.names = 1, sep = sep2, check.names = FALSE)
common <- intersect(colnames(mat), rownames(meta))
mat <- mat[, common, drop = FALSE]
meta <- meta[common, , drop = FALSE]
group <- factor(meta[[args$group_col]])
design <- model.matrix(~0 + group)
colnames(design) <- levels(group)
fit <- limma::lmFit(mat, design)
contrast <- limma::makeContrasts(contrasts = paste(levels(group)[2], levels(group)[1], sep = "-"), levels = design)
fit2 <- limma::eBayes(limma::contrasts.fit(fit, contrast))
dep <- limma::topTable(fit2, number = Inf, adjust.method = "BH")
write.csv(dep, file.path(args$outdir, "differential_proteins.csv"))

# ---- 补图(Bio Wingman):火山图 + Top 差异蛋白热图 ----
suppressWarnings(suppressMessages(library(ggplot2)))
dep$sig <- ifelse(dep$adj.P.Val < 0.05, ifelse(dep$logFC > 0, "Up (case)", "Down (case)"), "NS")
.pv <- ggplot(dep, aes(logFC, -log10(adj.P.Val), color = sig)) +
  geom_point(size = 1.2, alpha = 0.8) +
  scale_color_manual(values = c("Up (case)" = "#CC79A7", "Down (case)" = "#0072B2", "NS" = "grey80")) +
  labs(x = "logFC (case - control)", y = "-log10(adj.P)", title = "Differential proteins", color = NULL) +
  theme_bw(base_size = 11) + theme(panel.grid = element_blank())
ggsave(file.path(args$outdir, "volcano.png"), .pv, width = 6.5, height = 5.5, dpi = 200)
.top <- head(rownames(dep)[order(dep$adj.P.Val)], 30)
if (length(.top) >= 2 && requireNamespace("pheatmap", quietly = TRUE)) {
  .ann <- data.frame(group = group); rownames(.ann) <- colnames(mat)
  png(file.path(args$outdir, "heatmap_top.png"), width = 1000, height = 900, res = 120)
  pheatmap::pheatmap(mat[.top, , drop = FALSE], annotation_col = .ann, scale = "row",
                     show_rownames = TRUE, fontsize_row = 6, main = "Top 30 differential proteins")
  dev.off()
}
