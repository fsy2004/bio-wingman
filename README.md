# Bio Wingman 🧬

面向生物信息学分析的**本地桌面软件**——按数据处理流程组织方法,选方法、填参数、点运行,直接出发表级图表和结果表。与 [Meta Wingman](https://gitee.com/fsy2004/meta-wingman) 同一套原生外壳(Python + Tkinter,原生 Windows 主题),复用经过验证的 R 分析模块,无需写代码、无需搭环境服务。

> 定位:把一套可复用的生信分析脚本包装成"turnkey"桌面工具。不是要发新方法,而是让常规流程**一键可跑、可复现、可出图**。

## 按流程分类的方法

左侧方法树按**数据处理阶段**组织(空阶段自动隐藏):

| 阶段 | 内容 | 首批方法 |
|------|------|----------|
| S0 数据获取 / 导入 | GEO 下载、表达矩阵读入 | (规划中) |
| S1 质控 / 预处理 | 过滤、缺失、离群 | (规划中) |
| S2 标准化 / 批次校正 | 归一化、去批次 | (规划中) |
| **S3 差异分析** | limma 差异表达 | 差异表达分析(limma) |
| **S4 功能富集** | GO / KEGG 过表达 | GO / KEGG 功能富集 |
| **S5 下游分析** | 共表达网络、免疫浸润 | WGCNA 共表达网络、免疫浸润可视化 |
| S6 因果推断 (MR) | 孟德尔随机化 | (规划中) |
| **S7 建模 / 诊断 (ML)** | 特征筛选、诊断模型 | LASSO 特征筛选、诊断模型(ROC/校准/DCA) |
| S8 可视化 / 报告 | 高级图、一键报告 | (报告已内置于结果区) |

首批 6 个方法均已端到端跑通(内置示例数据,`返回码 0`)。

## 亮点

- **原生桌面**:无浏览器、无本地服务;双击 `start.bat` 即用。
- **内存红绿灯**:运行前按数据规模估算内存峰值(WGCNA 随基因数平方增长会预警),避免跑一半 OOM。
- **可复现**:每次运行落地 `reproduce.R` + `data.csv`,一条命令重跑。
- **一键报告**:从产物生成 Word 报告(方法 / 结果 / 参数 / 复现命令 + R `citation()` 真实文献,不臆造)。
- **结果区直用**:图表分标签页;复制图到剪贴板(直接粘进 Word/PPT)、另存 PNG / 矢量 PDF、复制 / 另存表格。
- **中英双语**:界面免重启切换。

## 安装 / 使用

**需要**:Windows + Python 3.9+ + R 4.0+。

1. 下载本仓库(或 `git clone`)。
2. 双击 `install.bat`——自动装 Python 包 + R 包(CRAN 走清华镜像;`limma`/`ComplexHeatmap`/`clusterProfiler`/`org.Hs.eg.db` 等 Bioconductor 包走 BiocManager)。
3. 双击 `start.bat` 启动。
4. 随时体检环境:`python setup/env_check.py`。

首次富集分析(S4)需要本地/联网的注释库(`org.Hs.eg.db`),`install.bat` 会一并装好。

## 分析模块来源

分析逻辑来自可复用生信代码库 `bioinfo-reusable-code`(已 vendor 进 `toolkit/modules/`,含 `_framework/` 发表级绘图主题)。每个方法一个 JSON manifest(`manifests/`)声明入口脚本、参数、产物与内存模型;引擎按 manifest 定位解释器(R / Python)、跑子进程、收产物。

## 架构

```
biowingman/     原生 Tkinter 外壳(与 Meta Wingman 共享:引擎/结果区/报告/项目/i18n/内存 doctor)
manifests/      每个方法一个 JSON(entry / 参数 / 产物 / cite_pkgs / 内存模型 / 流程阶段)
toolkit/modules/  vendor 的分析脚本 + _framework 绘图主题
config/         requirements.json(依赖单一权威源)+ column_shapes.json
setup/          env_check.py(环境体检)+ install.ps1 / install_r_packages.R(装 CRAN + Bioc)
```

## 许可

MIT © 2026 fsy2004。vendor 的分析脚本沿用其原始许可(见各模块)。
