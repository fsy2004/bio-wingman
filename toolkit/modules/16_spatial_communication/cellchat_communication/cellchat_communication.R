#!/usr/bin/env Rscript
# 细胞-细胞通讯(CellChat)——按 CellChat 官方最简工作流适配,纯本地运行,不需任何 API。
# 用法: Rscript cellchat_communication.R --counts counts.csv --meta meta.csv \
#        [--celltype_col celltype] [--species human|mouse] --outdir results
suppressWarnings(suppressMessages({library(CellChat); library(ggplot2)}))

parse_args <- function() {
  a <- commandArgs(trailingOnly = TRUE); out <- list(); i <- 1
  while (i <= length(a)) {
    k <- sub("^--", "", a[[i]])
    v <- if (i + 1 <= length(a) && !grepl("^--", a[[i + 1]])) a[[i + 1]] else TRUE
    out[[k]] <- v; i <- i + if (isTRUE(v)) 1 else 2
  }
  out
}
args <- parse_args()
if (is.null(args$counts) || is.null(args$meta) || is.null(args$outdir))
  stop("Usage: --counts counts.csv --meta meta.csv [--celltype_col celltype] --outdir results")
ct_col  <- if (!is.null(args$celltype_col)) args$celltype_col else "celltype"
species <- if (!is.null(args$species)) args$species else "human"
dir.create(args$outdir, recursive = TRUE, showWarnings = FALSE)

cat("Step 1/6: 读表达 + 元数据...\n")
counts <- as.matrix(read.csv(args$counts, row.names = 1, check.names = FALSE))
meta <- read.csv(args$meta, check.names = FALSE)
rownames(meta) <- meta[[1]]                       # 首列=细胞名
meta <- meta[colnames(counts), , drop = FALSE]
if (!ct_col %in% colnames(meta)) stop(sprintf("meta 无细胞类型列 '%s'", ct_col))
meta[[ct_col]] <- as.factor(as.character(meta[[ct_col]]))

cat("Step 2/6: log-归一化(CPM)...\n")
libsize <- pmax(colSums(counts), 1)
data.input <- log1p(sweep(counts, 2, libsize, "/") * 1e4)

cat("Step 3/6: 建 CellChat 对象 + 载 L-R 数据库...\n")
cellchat <- createCellChat(object = data.input, meta = meta, group.by = ct_col)
cellchat@DB <- if (species == "mouse") CellChatDB.mouse else CellChatDB.human
cellchat <- subsetData(cellchat)

cat("Step 4/6: 识别过表达基因/相互作用...\n")
cellchat <- identifyOverExpressedGenes(cellchat)
cellchat <- identifyOverExpressedInteractions(cellchat)

cat("Step 5/6: 推断通讯概率(computeCommunProb)...\n")
cellchat <- computeCommunProb(cellchat, type = "triMean", population.size = TRUE)
cellchat <- filterCommunication(cellchat, min.cells = 5)
cellchat <- computeCommunProbPathway(cellchat)
cellchat <- aggregateNet(cellchat)

cat("Step 6/6: 出图 + 结果表...\n")
gs <- as.numeric(table(cellchat@idents))
# 聚合通讯网络:互作数 + 互作强度 圈图
png(file.path(args$outdir, "communication_count_circle.png"), width = 1000, height = 900, res = 130)
netVisual_circle(cellchat@net$count, vertex.weight = gs, weight.scale = TRUE,
                 label.edge = FALSE, title.name = "Number of interactions")
dev.off()
png(file.path(args$outdir, "communication_weight_circle.png"), width = 1000, height = 900, res = 130)
netVisual_circle(cellchat@net$weight, vertex.weight = gs, weight.scale = TRUE,
                 label.edge = FALSE, title.name = "Interaction strength")
dev.off()
# 配体-受体气泡图(全部 source→target)
try({
  ng <- length(levels(cellchat@idents))
  p <- netVisual_bubble(cellchat, sources.use = seq_len(ng), targets.use = seq_len(ng),
                        remove.isolate = FALSE)
  ggsave(file.path(args$outdir, "LR_bubble.png"), p, width = 8, height = 7, dpi = 200)
}, silent = TRUE)
# 结果表:所有推断出的配体-受体通讯
df <- subsetCommunication(cellchat)
if (is.data.frame(df) && nrow(df)) write.csv(df, file.path(args$outdir, "inferred_communications.csv"), row.names = FALSE)
# 各细胞类型收发强度
out_strength <- data.frame(celltype = rownames(cellchat@net$weight),
                           outgoing = rowSums(cellchat@net$weight),
                           incoming = colSums(cellchat@net$weight))
write.csv(out_strength, file.path(args$outdir, "signaling_strength_by_celltype.csv"), row.names = FALSE)
cat("完成。通讯圈图/气泡图/表见", normalizePath(args$outdir), "\n")
