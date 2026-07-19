## Bio Wingman: 安装缺失的 R 包。
## 用法: Rscript install_r_packages.R <CRAN_repo> <BIOC_mirror> <cran_pkgs...> -- <bioc_pkgs...>
##   - CRAN 包用 install.packages;Bioc 包(limma/ComplexHeatmap/clusterProfiler/org.Hs.eg.db 等)
##     用 BiocManager::install。install.ps1 从 config/requirements.json 传入两组清单。
args <- commandArgs(trailingOnly = TRUE)
repo <- if (length(args) >= 1 && nzchar(args[1])) args[1] else "https://mirrors.tuna.tsinghua.edu.cn/CRAN"
bioc_mirror <- if (length(args) >= 2 && nzchar(args[2])) args[2] else "https://mirrors.tuna.tsinghua.edu.cn/bioconductor"

rest <- if (length(args) >= 3) args[-(1:2)] else character(0)
sep <- which(rest == "--")
if (length(sep)) {
  cran_pkgs <- rest[seq_len(sep[1] - 1)]
  bioc_pkgs <- rest[(sep[1] + 1):length(rest)]
} else {
  cran_pkgs <- rest
  bioc_pkgs <- character(0)
}
if (!length(cran_pkgs)) cran_pkgs <- c("ggplot2", "ggrepel", "circlize", "dplyr", "reshape2",
                                       "glmnet", "pROC", "rms", "rmda", "ggpubr", "WGCNA", "BiocManager")
if (!length(bioc_pkgs)) bioc_pkgs <- c("limma", "ComplexHeatmap", "clusterProfiler", "org.Hs.eg.db")

options(repos = c(CRAN = repo))
options(BioC_mirror = bioc_mirror)
cat("  CRAN 源:", repo, "\n  Bioc 镜像:", bioc_mirror, "\n")

installed <- function() rownames(installed.packages())

## ---- CRAN ----
miss <- cran_pkgs[!cran_pkgs %in% installed()]
if (length(miss)) {
  cat(sprintf("  [CRAN] 需装 %d 个:%s\n", length(miss), paste(miss, collapse = ", ")))
  for (p in miss) { cat("   -", p, "\n"); try(install.packages(p), silent = TRUE) }
} else cat("  [CRAN] 全部就绪。\n")

## ---- Bioconductor ----
if (!"BiocManager" %in% installed()) try(install.packages("BiocManager"), silent = TRUE)
if ("BiocManager" %in% installed()) {
  bmiss <- bioc_pkgs[!bioc_pkgs %in% installed()]
  if (length(bmiss)) {
    cat(sprintf("  [Bioc] 需装 %d 个:%s\n", length(bmiss), paste(bmiss, collapse = ", ")))
    try(BiocManager::install(bmiss, update = FALSE, ask = FALSE), silent = TRUE)
  } else cat("  [Bioc] 全部就绪。\n")
} else {
  cat("  ⚠️ BiocManager 未装上,无法安装 Bioconductor 包(limma 等)。请检查网络。\n")
}

still <- c(cran_pkgs, bioc_pkgs)[!c(cran_pkgs, bioc_pkgs) %in% installed()]
if (length(still)) cat("  ⚠️ 仍未装上(检查网络/换源):", paste(still, collapse = ", "), "\n") else
  cat("  ✅ R 包安装完成。\n")
