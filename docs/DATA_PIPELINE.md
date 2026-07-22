# Bio Wingman 数据流水线

## 目标

用户只负责从 GEO、TCGA、10x、GWAS 等权威数据库下载原始或官方整理文件。格式识别、样本分组表、分析中间表和下游接线应尽量在 Bio Wingman 内完成。内置示例只用于演示,不能与用户项目数据混跑。

## 已接通的 GEO / bulk 主链路

```text
GEO series_matrix.txt + GPL 注释
  → 探针映射与基因聚合
  → geneMatrix.csv
  → 软件内样本分组（对照 / 病例）
  → 归一化 Sample_Type_Matrix.csv + sample_traits.csv
  ├─→ limma 差异分析 → DE_significant_genes.csv
  │    ├─→ GO / KEGG
  │    ├─→ LASSO / RF / SVM-RFE
  │    └─→ 诊断模型
  └─→ WGCNA
```

- 所有辅助输入都在方法页可见。
- 运行自己的数据时,缺少任何输入会禁用运行按钮并就地提示。
- `auto_from` 由 manifest 声明可复用的上游文件名;方法切换时从 Bio Wingman 运行目录选择最新匹配产物。
- 样本分组属于研究者必须确认的语义选择。软件提供批量标记并自动写出分组与数值性状文件,不擅自猜病例 / 对照。

## 当前覆盖边界

| 来源 / 数据 | 当前方式 |
|---|---|
| GEO bulk 芯片 | 已端到端:series matrix + GPL → 分组 → 归一化 → 差异 / 富集 / WGCNA / ML |
| 常规 counts / 表达矩阵 | 对应方法直接读取;多输入逐项显示 |
| 10x / Seurat / H5AD | 对应单细胞或空间方法直接读取已下载对象 / 矩阵 |
| MAF | 突变方法直接读取 `.maf` / `.maf.gz` |
| 甲基化、蛋白质组、代谢组 | 矩阵与样本注释均可在同一方法页选择,不再固定内置注释 |
| TCGA 临床 + 表达 | 当前读取已下载并对应好的表;自动合并导入器待补 |
| GWAS / MR | 当前读取 harmonized 汇总数据;VCF/原始 summary statistics 自动 harmonization 待补 |

新增来源时应复用成熟包或现有模块,通过新的 S0/S1 导入器产出稳定资产文件,再在 manifest 中用 `auto_from` 接到下游;不在 UI 中重写统计方法。
