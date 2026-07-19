# Bio Wingman 建库计划(全库普查产出 2026-07-19)

## totals
纳入(include=true)总模块 ≈ 99;其中【已完成·有manifest】6(007/010/012/016/021/054);【待建】93。排除 45(见 excluded)。

需【新 vendor 的类】14 个:01/07/08/09/12/13/15/16/17/19/20/21/22/23(02/03/04/05/06/11 已整类 vendor,文件已在 toolkit/modules/ 下,只差 manifest)。

按批:B1=12(已vendor·high·依赖多已装), B2=6(已vendor·需装依赖), B3=3(已vendor·低置信/需改造), B4=25(新vendor·纯CRAN+示例·high), B5=27(新vendor·需装依赖 Bioc/github/pip), B6=20(新vendor·无示例/需大数据/需改造·low)。

需装 Bioconductor 依赖的模块 ≈ 12:559/546/541/542/545/557/558/084/522/047 等(muscat/scater/edgeR/Banksy/SpatialExperiment/nnSVG/scran/scuttle/miloR/SPOTlight/ConsensusClusterPlus/sccomp/voomCLR/maftools/RcisTarget/MOFA2/mixOmics)。需 github 装:hdWGCNA/copykat/spacexr/CWGCNA/nichenetr/TwoSampleMR/MRPRESSO/MRcare/MRBEE/plinkbinr/CytoTRACE2/BayesPrism。需 pip 装:prolif/MDAnalysis/rdkit/squidpy/scanpy/liana/paste-bio/palantir/scvelo/cellrank/commot/tangram/decoupler/mapie/posebusters。

★关键事实修正:07 类普查声称 docking 022「已实现(现有6方法之一)」为误——ground truth: toolkit/modules 无 07 目录、manifests 仅 6 个无 docking;022 须新 vendor(归 B5)。

## vendor_plan
需【新 vendor】14 个类(02/03/04/05/06/11 已整类 vendor, 文件已在 bio-wingman/toolkit/modules/ 下, 仅缺 manifest):
01_network_pharmacology(源 2.1M, 7 模块)、07_molecular_docking(源 4.5M, 4 模块)、08_singlecell_spatial_trajectory(源 166M ★见下)、09_mendelian_randomization(8 模块, 弃 legacy)、12_tcga_prognosis(6 模块)、13_tf_regulation_circos(4 模块)、15_drug_perturbation(2 模块)、16_spatial_communication(源 6.9M, 12 模块)、17_advanced_figures(7 模块)、19_multiomics_integration(2 模块)、20_mutation_methylation_proteome(4 散脚本)、21_disease_burden_gbd(源 20M ★见下)、22_metabolism(1 模块)、23_uncertainty_conformal(1 模块)。

★★通用精简规则(实测 ground truth):vendor 时逐模块只带【脚本 + example_data + README】, 一律 SKIP 模块内的 results/ 与 assets/ 残留输出目录——bloat 主要来自 results/, 不是 example_data。实证:08 类 166M 里 146M 全是 560_copykat 的 results/(旧 copyKAT 运行残留), 其 example_data 仅 1M。剥掉 results/ 后 08 turnkey 10 模块合计仅几 MB。

★大 example 精简要点:
- 08:只 vendor 10 个 turnkey 模块目录, 且 560 剥 results/(146M→保留 example ~1M+truth 6.5K);跳过被排除的 491_sctour_extra_files(5.7M)/506_scVI(1.9M)/062/scSurvival 等 DL/legacy 目录。542/541/543/558 example 各 1-2.8M 可保留。
- 18:整类 137M 全排除(不 vendor)。
- 21:源 20M 主要是 99_external_sources/(git-ignored 上游克隆), vendor 时跳过, 只取 527/528/529/530 四个模块目录+其小 csv example(保持 21_.../0X_GBD 等子目录相对结构)。
- 09:只 vendor 8 个现代 turnkey(032/508/519/533/534/535/536/537), 全弃 legacy VCF/gwasglue 脚本(无 example/需大 VCF)。537 须连带 vendor/SharePro/ 源码目录。

★结构约束:所有模块靠 .find_fw() 向上找 modules/_framework(已 vendored), vendor 时务必保持 modules/_framework + modules/<类>/<模块> 相对层级(21 类含 0X_子类 中间层, 靠向上 6 级循环找到 _framework, 勿打平)。

★共性依赖坑(vendor 后接引擎前处理):(1) 多个模块主输入是【目录】(003/005/006/011/015/035/056)——UI/manifest 需支持选目录而非单文件;(2) 一批模块不支持 --outdir 写死模块 results/(512/513/514/515/527/528/529/530/517/543/547/556/555/511/510 等)——引擎需 patch 成 glob 模块自身 results/, 或逐个补 outdir 形参;(3) 一批 input=none 或未解析 --input(508/509/511/510/516/518/521/533/536/537/545/558)——示例模式验 rc=0 无碍, 接『我的数据』需补 bio_args/getarg。

## deps_to_install
【R · CRAN】UpSetR, e1071, randomForest, RobustRankAggreg, GOplot, caret(+gbm,nnet,kknn,pls,LogitBoost), kernelshap, shapviz, xgboost, igraph, Boruta, Hmisc, NetRep, SmCCNet, ggraph, ggrepel, reshape2, survival, survminer, timeROC, aorsf, randomForestSRC, survex, ranger, riskRegression, dcurves, prodlim, data.table, ggalluvial, ggdist, ggridges, circlize(已装), MendelianRandomization, metafor, glmnet(已装), NMF, bio3d, Seurat, SCpubr, dplyr, survey, lme4, tidyr, scatterpie, uwot, RcppML, ieugwasr, visNetwork, networkD3, aricode/mclust, leidenAlg, ggbeeswarm。

【R · Bioconductor】muscat, SingleCellExperiment, scater, scuttle, edgeR, scran, enrichplot, ggtangle, aplot, ggtree, Banksy, SpatialExperiment, SummarizedExperiment, S4Vectors, nnSVG, miloR, BiocNeighbors, sccomp, voomCLR, SPOTlight, ConsensusClusterPlus, ComplexHeatmap(已装), maftools, RcisTarget, MOFA2, mixOmics, mistyR。(已装于首批 6 法:limma, ComplexHeatmap, clusterProfiler, org.Hs.eg.db, DOSE, WGCNA, rms, rmda, pROC, ggpubr, glmnet)

【R · GitHub(gh-proxy/remotes)】hdWGCNA(smorabit), copykat(navinlabcode), spacexr(dmcable), CWGCNA(yuabrahamliu, 可选), nichenetr(saeyslab), TwoSampleMR, MRPRESSO, MRcare, MRBEE(noahlorinczcomi), plinkbinr, CytoTRACE2, BayesPrism(Danko-Lab)。★这些 github 装易失败, 且 533/540/504 等对缺失有降级/可选处理。

【R · 其他】cmdstanr + cmdstan(557, 首跑编译 Stan, 慢, 需 C++ 工具链)。

【Python · pip】prolif, MDAnalysis, rdkit, posebusters, pandas, squidpy, scanpy, anndata, palantir, liana(>=1.7), plotnine, paste-bio(1.4.0), POT==0.9.4(★与 POT>=0.9.5 不兼容, 与其它 py 模块隔离或建独立 venv), scvelo, cellrank, commot, tangram, decoupler(+omnipath 联网), mapie(1.4.x), scikit-learn, scipy, statsmodels, numpy, matplotlib, pyscenic/arboreto/ctxcore/dask。

★装包优先级建议:先装 B1/B2 的 CRAN(UpSetR/e1071/randomForest/RRA/GOplot/NetRep/SmCCNet) → B2 Bioc(muscat 全家/enrichplot) → B4 无需装(纯 CRAN 多已随首批) → B5 分 R-Bioc/github 与 python-pip 两条线并行 → B6 大数据/编译类最后。用户环境安装依赖前需先征询(遵循 execution_workflow 规则)。

## excluded
共排除 45 个(include=false 或命中【深度学习】/【MD 模拟】/不可 turnkey):

【DL(torch/GPU/transformer, 用户 07-19 明确排除)】550 TabPFN(05), 062 sctour VAE/491 其教程杂项(08), 506 scVI/scANVI(08), 497 scSurvival PyTorch MIL-Cox(12), 070 chemCPA(15), 071 scDrug 重模型(15), 18 类 ai_scientific_figures(torch+SAM3+外部 LLM API+web 服务)。

【MD 模拟/需服务器二进制】086 Vina+GROMACS+gmx_MMPBSA 管道(07)。

【交互 GUI(非批处理出图)】061 scFOCAL Shiny(08)。

【live 联网 API/无 CLI/硬编码】493 OpenTargets/DGIdb/ChEMBL(01, 基因列表硬编码不产 csv)。

【CIBERSORT 引擎/IOBR stub(硬编码 setwd/无 example/需 LM22)】017, 018, 492(06)。

【legacy 硬编码 setwd + 无 bio_args/example + 需外部 GSE/VCF 原始数据(08)】023, 024, 025, 026, 027, 044, 049, 050, 051, 058。

【legacy MR(gwasglue 已停维+VariantAnnotation+VCF, 或走 OpenGWAS API 已被封, 或纯模板)(09)】028, 029, 030, 031, 033, 043, 055(legacy); 075(name=value 非 --flag 无 example), 079(无 example, MVMR github), 499(sem 调用全注释=纯模板不产图)。

【04 类模板/片段】045(自标 TEMPLATE-NOT-RUNNABLE), 059(硬编码 setwd 无 example), 496(28 行 usage-snippet 主体全注释, Mime github)。

【10_twas_sceqtl 整类】036/037/038/039(R 函数定义非 CLI, 无 png/csv 产出), 040/041/042(FUSION 封装需 plink2R[仅 GitHub]+GB LD 参考+预算权重+GWAS sumstats, 无 example)——整类 🔴 Heavy, 需大参考数据+受限 OneK1K 基因型, 普通电脑无法一跑 rc=0。

【20 类 md-only】526 CNV 说明文档(无 .R/.py entry, GISTIC2/CNVkit 需外部环境)。

注:07 类 022 docking 普查误标『已实现』, 实为未 vendor, 已改为纳入(B5)而非排除。

## risks
1. ★普查数据硬伤已核实并修正:07 类 022 docking 被误标『已实现(现有6方法之一)』。ground truth: bio-wingman/toolkit/modules 无 07 目录, manifests 仅 6 个(deg_limma/diag_model/enrich_go_kegg/immune_infiltration_viz/ml_lasso/wgcna), 均无 docking。真正已实现 6 法=007/010/012/016/021/054。022 须新 vendor(已归 B5)。建库时勿信『已实现』字样, 以 toolkit/manifests 实况为准。

2. ★引擎 --outdir 契约缺口:相当一批模块(尤其 17/21 类出图模块、508/509/510/511/516/517/518/521/533/536/537/543/545/547/555/556/558 等)不接 --outdir 或不解析 --input, 写死模块自身 results/assets 或只跑合成 demo。示例模式验 rc=0 不受影响, 但『我的数据』模式失效。落地前须定引擎策略:要么统一 patch 引擎为『glob 模块自身 results/*.png,*.csv』兜底, 要么逐个给脚本补 --outdir/getarg(任务只读未改, 需后续单独改造)。建议在 manifest 层标 needs_dir_input / no_outdir / demo_only 元字段, UI 据此提示。

3. 目录型主输入(003/005/006/011/015/035/056)与引擎『主输入替换成用户单文件』模型不契合, UI 需支持选目录/多文件。

4. 依赖安装是最大不确定性:github 包(hdWGCNA/copykat/spacexr/nichenetr/TwoSampleMR/MRcare/MRBEE/BayesPrism)在国内网易失败(需 gh-proxy);POT==0.9.4 强约束与其它 py 空间模块冲突(建议 544/PASTE 独立 venv);cmdstanr(557)首跑编 Stan 慢+需 C++ 工具链;paste-bio/liana/squidpy 版本敏感。安装前须征询用户(execution_workflow 规则:ask before installing deps)。

5. B6 一批无 example_data(082/087/047/081/072-080/077/083/522-525), 无法一跑即验;需先补小示例或改 arg 解析。20 类 4 脚本还需补 volcano/heatmap 绘图(当前只出 csv/PDF)才满足『每方法出 png』约定。

6. 部分模块含内部 QC/对照/阴性边界(559 pseudobulk 防伪、533 赢家诅咒、536 Type-I error、544 诚实基线等)——按 feedback_no_preemptive_defense, 这些是内部质控, manifest/UI 文案勿当卖点反复拎出。

7. 建议验证顺序严格按 B1→B6:B1/B2/B3 零 vendor(文件已在)只写 manifest, 可最快把可跑方法数从 6 推到 ~27;之后再逐类新 vendor。整体待建 93 个, 工作量大, 分批推进。

## 建库批次(build_batches)

### [B1-已vendor类·high·依赖多已随首批装(最先, 只写 manifest+验 rc=0)]  (12 方法)
这12个模块所在类(02/03/04/05/06/11)已整类 vendor(文件在 toolkit/modules/ 下, _framework 已就位), 依赖以 base R / 已装包(limma/ComplexHeatmap/rms/pROC/WGCNA)或轻量 CRAN(e1071/randomForest/UpSetR/GOplot/RobustRankAggreg)为主, turnkey=high, 示例齐全。零 vendor 工作, 写 manifest 即可逐个验 rc=0, 最快出成果。注意 015/035/056 主输入为【目录】(内含≥2份csv), UI/manifest 需支持选目录;502 需先小改补 bio_args 解析 --input/--group/--candidates/--outdir(当前硬编码 example_data)。
- go-...                             | GOplot 富集环形/和弦高级图 | S4 | 02_enrichment/549_goplot_chord_enrichment | Rscript | triple+ | vendor=False | deps=CRAN: GOplot(自带EC示例, 完全离线) | high
- geo-expr-matrix-tidy               | GEO 表达矩阵整理(探针→基因) | S0 | 03_transcriptomics_deg/008_geo_expression_matrix | Rscript | dual | vendor=False | deps=无(base R)。仅出 csv 无 png | high
- geo-sample-grouping                | GEO 样本分组整理+归一化 | S2 | 03_transcriptomics_deg/009_geo_sample_grouping | Rscript | dual | vendor=False | deps=已装 limma。仅出 csv | high
- geo-multicohort-batch-correction   | GEO 多队列合并+批次校正 | S2 | 03_transcriptomics_deg/056_geo_multicohort_batch_correction | Rscript | single | vendor=False | deps=已装 limma + CRAN reshape2。★--input 为目录(≥2份csv) | high
- svm-rfe-feature-selection          | SVM-RFE 递归特征消除排名 | S7 | 04_ml_feature_selection/013_svm_rfe_feature_selection | Rscript | dual | vendor=False | deps=CRAN: e1071 | high
- randomforest-feature-selection     | 随机森林 Gini 重要性排名 | S7 | 04_ml_feature_selection/014_randomforest_feature_selection | Rscript | dual | vendor=False | deps=CRAN: randomForest | high
- ml-feature-intersection            | 多方法特征基因交集(Venn/UpSet) | S7 | 04_ml_feature_selection/015_ml_feature_intersection_venn_upset | Rscript | single | vendor=False | deps=CRAN: UpSetR。★--input 为目录(多份基因列表) | high
- ml-combo-intersection              | 多方法组合交集排序选优 | S7 | 04_ml_feature_selection/035_ml_combination_intersection | Rscript | single | vendor=False | deps=CRAN: UpSetR。★--input 为目录;--pick 不可超方法文件数 | high
- rra-consensus-features             | 稳健秩聚合(RRA)共识特征选择 | S7 | 04_ml_feature_selection/554_rra_consensus_features | Rscript | single | vendor=False | deps=CRAN: RobustRankAggreg (ComplexHeatmap 已装, 缺则降级跳2图) | high
- biomarker-triple-vote              | 生物标志物三法投票筛选 | S7 | 04_ml_feature_selection/502_biomarker_triple_vote | Rscript | triple+ | vendor=False | deps=CRAN: igraph/Boruta/Hmisc。★需小改补 bio_args 解析 --input/--group/--candidates/--outdir(当前硬编码 example_data) | high
- geo-diagnostic-external-validation | GEO 诊断模型外部验证(训练/验证 ROC+校准) | S7 | 05_diagnostic_models/063_geo_diagnostic_validation | Rscript | triple+ | vendor=False | deps=已装 rms/pROC (+ggplot2)。primary=--train, --valid/--genes 回退示例 | high
- cwgcna-causal-module               | CWGCNA 模块因果方向(中介)推断 | S5 | 11_wgcna/540_cwgcna_causal_module | Rscript | dual | vendor=False | deps=已装 WGCNA (CWGCNA github 可选, 缺则优雅降级 WGCNA+lm) | high

### [B2-已vendor类·需装依赖(Bioc/新CRAN/多算法包)]  (6 方法)
同为已 vendor 类(无需 vendor 工作), 但依赖需新装:559 muscat 全家(Bioc 重), 546 enrichplot/ggtangle(cnetplot 已迁 ggtangle, 需对版本), 034/052 caret + 一堆算法子包(缺包 tryCatch 跳过但要全跑须预装), 538/539 CRAN NetRep/SmCCNet。装完 deps 后 turnkey 高(示例齐全)。
- enrichplot-emap-cnet-tree          | 富集高级图 dotplot/cnet/emap/tree | S4 | 02_enrichment/546_enrichplot_emap_cnet_tree | Rscript | single | vendor=False | deps=Bioc/CRAN: enrichplot,ggtangle,aplot,ggtree(clusterProfiler/org.Hs.eg.db/DOSE 已装)。★版本坑:cnetplot 已迁 ggtangle;org.db 缺则回退合成 | high
- muscat-pseudobulk-ds               | 单细胞 pseudobulk 差异状态(muscat) | S3 | 03_transcriptomics_deg/559_muscat_pseudobulk_ds | Rscript | single | vendor=False | deps=Bioc: muscat,SingleCellExperiment,scater,edgeR(limma 已装)。装包量最大 | high
- multi-ml-feature-selection         | 多机器学习方法比较+特征交集 | S7 | 04_ml_feature_selection/034_multi_ml_feature_selection | Rscript | single | vendor=False | deps=CRAN: caret,pROC,UpSetR + 算法包 gbm/nnet/kknn/pls/e1071/LogitBoost/randomForest(缺则该法自动跳过) | medium
- shap-interpretation                | SHAP 机器学习模型解释 | S7 | 04_ml_feature_selection/052_shap_interpretation | Rscript | single | vendor=False | deps=CRAN: caret,kernelshap,shapviz,xgboost,e1071,randomForest,pROC。★样本后缀默认 _con/_tra(非 _tre) | medium
- netrep-module-preservation         | NetRep 跨队列模块保守性置换检验 | S5 | 11_wgcna/538_netrep_module_preservation | Rscript | triple+ | vendor=False | deps=CRAN: NetRep (+ggplot2)。可配 054 模块产出做外验 | high
- smccnet-multiomics-network         | SmCCNet 表型驱动多组学稀疏典则相关网络 | S5 | 11_wgcna/539_smccnet_multiomics_network | Rscript | triple+ | vendor=False | deps=CRAN: SmCCNet,igraph,ggraph,ggrepel,reshape2 | high

### [B3-已vendor类·低置信/需改造(github 包或无 --input/--outdir)]  (3 方法)
已 vendor 类里的3个 low:503 硬编码读 cohorts.rds、不用 bio_args(需补 arg 解析);504 hdWGCNA 从 github 装+硬编码路径(需补 CLI);520 BayesPrism github 装+代码不解析 --reference/--bulk(永远跑合成 demo)。均 CPU 可跑, 示例/合成模式能出图验 rc=0, 但接『我的数据』须改造, 故排在已 vendor 类最后。
- generalization-robustness-lodo-meta | 跨队列泛化诚实三件套(REML meta+LODO) | S7 | 05_diagnostic_models/503_generalization_robustness | Rscript | single | vendor=False | deps=CRAN: metafor,glmnet,pROC。★无 --input/--outdir(硬编码读 cohorts.rds/写 results), 需补 arg 解析+定义 .rds schema | low
- hdwgcna-single-cell                | hdWGCNA 单细胞共表达网络(metacell) | S5 | 11_wgcna/504_hdwgcna_single_cell | Rscript | single | vendor=False | deps=github: hdWGCNA(smorabit) + CRAN Seurat + 已装 WGCNA。★无 bio_args, DIR/DDAT/DRES 硬编码, 需补 CLI。示例 rds 仅130K | low
- bayesprism-deconvolution           | BayesPrism 贝叶斯细胞类型反卷积 | S5 | 06_immune_infiltration/520_bayesprism_deconvolution | Rscript | triple+ | vendor=False | deps=github: BayesPrism(Danko-Lab)。★代码不解析 --reference/--labels/--bulk, 始终跑自合成 demo, 需补 bio_args | low

### [B4-新vendor·易(纯CRAN+自带示例·high, vendor 后写 manifest 即验)]  (25 方法)
14 个新类中最易落地的一批:纯 base R / 轻量 CRAN(ggplot2/survival/survminer/timeROC/circlize/ggalluvial/ggdist/ggridges/ggrepel/MendelianRandomization/survey/lme4/igraph/ggraph), 自带小示例, turnkey=high。vendor 时按类新建 modules/<类>/<模块> 目录+_framework 已在。★多数出图模块(17/21 类、508、053除外)不接 --outdir, 写死模块自身 results/assets——示例模式验 rc=0 无碍, 但『我的数据』/引擎 outdir 需 patch 或每模块补 outdir 形参。★venn 类(003/005/006/011)与 060 主输入为目录或三输入。
- ctd-compound-targets               | CTD 化合物靶点提取 | S0 | 01_network_pharmacology/001_ctd_compound_targets | Rscript | single | vendor=True | deps=无(base R)。仅出 csv | high
- swisstarget-compound-targets       | SwissTargetPrediction 化合物靶点提取 | S0 | 01_network_pharmacology/002_swisstarget_compound_targets | Rscript | single | vendor=True | deps=无(base R, 同 001 模板) | high
- genecards-disease-targets          | GeneCards 疾病靶点提取 | S0 | 01_network_pharmacology/004_genecards_disease_targets | Rscript | single | vendor=True | deps=无(base R, 同 001 模板) | high
- ctd-swiss-target-venn              | CTD∪SwissTarget 靶点交并集 Venn | S5 | 01_network_pharmacology/003_ctd_swiss_target_union_venn | Rscript | single | vendor=True | deps=CRAN: ggplot2(UpSetR 仅≥3集)。★--input 为目录 | high
- omim-genecards-target-venn         | OMIM∪GeneCards 疾病靶点交并集 Venn | S5 | 01_network_pharmacology/005_omim_genecards_target_venn | Rscript | single | vendor=True | deps=CRAN: ggplot2。★--input 为目录(同 003 模板) | high
- disease-compound-target-venn       | 疾病∩化合物核心靶点 Venn | S5 | 01_network_pharmacology/006_disease_compound_target_venn | Rscript | single | vendor=True | deps=CRAN: ggplot2。★--input 为目录 | high
- deg-drug-target-intersection       | DEG∩药物∩疾病靶点多集交集 | S5 | 01_network_pharmacology/011_deg_drug_target_intersection | Rscript | single | vendor=True | deps=CRAN: ggplot2,UpSetR(3集触发 UpSet)。★--input 为目录 | high
- mr-twosamplemr                     | 自包含双样本 MR 因果推断(IVW/Egger/WM) | S6 | 09_mendelian_randomization/032_mr_twosamplemr | Rscript | single | vendor=True | deps=无(自包含 IVW/Egger/WM + ggplot2, 不依赖 TwoSampleMR/LD 服务)。本类最佳纳入项 | high
- mr-twostep-mediation               | 两步(网络)中介 MR(Sobel/Delta/MC) | S6 | 09_mendelian_randomization/508_twostep_mediation_mr | Rscript | dual | vendor=True | deps=无(base R 自实现 + ggplot2)。★无 bio_args/--outdir, 双输入硬编码文件名, 示例可跑, 自定义输入需补参数解析 | high
- mvmr-cml                           | 约束极大似然多变量 MR(MVMR-cML-DP) | S6 | 09_mendelian_randomization/534_mvmr_cml_constrained | Rscript | single | vendor=True | deps=CRAN: MendelianRandomization(易装)。bio_args+示例齐备 | high
- tcga-single-gene-survival          | TCGA 单基因多终点生存曲线 | S7 | 12_tcga_prognosis/048_tcga_single_gene_survival | Rscript | single | vendor=True | deps=CRAN: survival,survminer | high
- tcga-prognostic-risk-model         | TCGA 预后风险模型五件套 | S7 | 12_tcga_prognosis/057_tcga_prognostic_risk_model | Rscript | single | vendor=True | deps=CRAN: survminer,timeROC(ComplexHeatmap/circlize 已装) | high
- tcga-immune-butterfly              | 单基因-免疫双蝴蝶相关图 | S5 | 12_tcga_prognosis/060_tcga_immune_butterfly | Rscript | triple+ | vendor=True | deps=CRAN: ggplot2(base stats 相关)。primary=--expr, immune/checkpoints 回退示例;目标基因须在表达矩阵行名 | high
- chromosome-circos                  | 基因染色体圈图(circlize ideogram) | S8 | 13_tf_regulation_circos/053_circlize_chromosome_circos | Rscript | single | vendor=True | deps=CRAN: circlize。支持 --input/--outdir。★hg38 首跑联网取 cytoband, 离线用 --genome hg19 | high
- faers-pharmacovigilance            | FAERS 药物警戒信号挖掘(ROR/PRR/IC/EBGM) | S5 | 15_drug_perturbation/078_faers_pharmacovigilance | Rscript | single | vendor=True | deps=CRAN: ggplot2(四种不相称性算法 base R 手写)。支持 --input/--outdir | high
- beyondcell-drug-response           | beyondcell 单细胞药物响应异质性 | S5 | 15_drug_perturbation/518_beyondcell_drug_response | Rscript | none | vendor=True | deps=CRAN: ggplot2(UCell 式打分 base R 重实现)。★input=none 纯合成 demo, 无 bio_args | high
- alluvial-sankey                    | ggalluvial 桑基/冲积图 | S8 | 17_advanced_figures/498_ggalluvial_sankey | Rscript | single | vendor=True | deps=CRAN: ggalluvial,ggplot2。支持 --outdir(本批少数支持 outdir 者) | high
- raincloud-plot                     | 云雨图(半小提琴+箱线+抖动点) | S8 | 17_advanced_figures/512_raincloud_plot | Rscript | single | vendor=True | deps=CRAN: ggdist,ggplot2。★不支持 --outdir(写死模块 assets/results), 纳入需补 outdir 形参 | high
- ridgeline-plot                     | 山脊图/joyplot | S8 | 17_advanced_figures/513_ridgeline_plot | Rscript | single | vendor=True | deps=CRAN: ggridges,ggplot2。★不支持 --outdir | high
- dumbbell-slope-plot                | 哑铃图+斜率图(配对前后变化) | S8 | 17_advanced_figures/514_dumbbell_slope_plot | Rscript | single | vendor=True | deps=CRAN: ggrepel,ggplot2。★不支持 --outdir。一模块出两图 | high
- chord-diagram                      | 弦图(关系/流量环形图) | S8 | 17_advanced_figures/515_chord_diagram | Rscript | single | vendor=True | deps=CRAN: circlize。★不支持 --outdir。--input 为方阵 csv | high
- gbd-burden-trend                   | GBD 疾病负担趋势(ASR/EAPC/Das Gupta/SDI) | S5 | 21_disease_burden_gbd/01_GBD/527_gbd_burden_trend | Rscript | triple+ | vendor=True | deps=CRAN: dplyr,ggplot2。★无 --outdir(写死 DIR/results+assets)。三输入自带示例 | high
- nhanes-survey-weighted             | NHANES 复杂抽样加权分析 | S5 | 21_disease_burden_gbd/02_NHANES/528_nhanes_survey_weighted | Rscript | single | vendor=True | deps=CRAN: survey,dplyr,ggplot2。★无 --outdir。权重列名 NHANES 契约硬编码 | high
- charls-longitudinal-cohort         | CHARLS 纵向队列(等值化/LMM/Cox+KM) | S5 | 21_disease_burden_gbd/03_CHARLS/529_charls_longitudinal_cohort | Rscript | single | vendor=True | deps=CRAN: lme4,survival,tidyr,dplyr,ggplot2。★无 --outdir;生存表始终合成(不随 --input 变), UI 需提示 | high
- comorbidity-network                | 共病网络(疾病对关联→igraph→Louvain) | S5 | 21_disease_burden_gbd/04_comorbidity_network/530_comorbidity_network | Rscript | single | vendor=True | deps=CRAN: igraph,ggraph,dplyr,ggplot2。★无 --outdir | high

### [B5-新vendor·需装依赖(Bioc/github/pip, high~medium)]  (27 方法)
新类中依赖较重但 turnkey 尚可(多数自带示例/合成回退, argparse 或 bio_args 规范)的一批。装包是主要时间成本:Bioc(Banksy/SpatialExperiment/nnSVG/scran/scuttle/miloR/SPOTlight/ConsensusClusterPlus)、github(TwoSampleMR/MRPRESSO/MRcare/MRBEE/copykat/plinkbinr)、pip(prolif/MDAnalysis/rdkit/posebusters/squidpy/scanpy/liana/paste-bio/mapie)。★docking 022 归此批(07 类须新建, 修正普查误标『已实现』)。★POT 版本冲突(544 须 POT==0.9.4)与 SCpubr/Seurat 依赖树重(532)是坑。多个 Python 模块(543/547/556/536/537/521/555)不支持 --outdir 或 input=none, 引擎按固定 results glob 或示例模式取产物。
- docking-binding-energy-viz         | 分子对接结合能可视化(热图+排序气泡) | S8 | 07_molecular_docking/022_docking_binding_energy_viz | Rscript | single | vendor=True | deps=已装 ComplexHeatmap/circlize/ggplot2。★07 类未 vendor 需新建;普查误标『已实现』, 实际无 07 目录无 docking manifest | high
- bio3d-dccm-pca-rmsf                | bio3d 系综/MD 分析:DCCM+PCA+RMSF | S5 | 07_molecular_docking/548_bio3d_md_dccm_pca | Rscript | single | vendor=True | deps=CRAN: bio3d,ggplot2。零下载(内置 transducin 系综)。★主输入 flag=--pdb(非 --input), 支持 --outdir | high
- prolif-interaction-fingerprint     | ProLIF 蛋白-配体相互作用指纹 | S5 | 07_molecular_docking/547_prolif_interaction_fingerprint | python | dual | vendor=True | deps=pip: prolif,MDAnalysis,rdkit。★无 --outdir(写死 results);example 仅 README, demo 用 prolif 自带 datafiles | medium
- posebusters-validity-panel         | PoseBusters 对接 pose 物理有效性面板 | S5 | 07_molecular_docking/556_posebusters_validity_panel | python | single | vendor=True | deps=pip: posebusters,rdkit,pandas。★无 --outdir。无输入自动生成好/坏构象 demo | high
- scrna-pub-figures                  | 单细胞发表级图(Seurat 标准流程) | S5 | 08_singlecell_spatial_trajectory/046_scrna_publication_figures | Rscript | single | vendor=True | deps=CRAN: Seurat,ggplot2,dplyr。bio_args 完整, UMAP 失败降级 tSNE | high
- vector-trajectory-direction        | VECTOR 表达潜能分化方向矢量场 | S5 | 08_singlecell_spatial_trajectory/517_vector_trajectory_direction | Rscript | dual | vendor=True | deps=CRAN: ggplot2(VECTOR 核心重实现, 免装 niche 包)。★无 --outdir(写死 results) | high
- banksy-spatial-domains             | BANKSY 空间域识别(vs 非空间基线 ARI) | S5 | 08_singlecell_spatial_trajectory/541_banksy_spatial_domains | Rscript | single | vendor=True | deps=Bioc: Banksy,SpatialExperiment,SummarizedExperiment,S4Vectors + CRAN aricode/mclust/igraph/leidenAlg。支持 --input/--outdir | medium
- nnsvg-spatial-svg                  | nnSVG 空间可变基因(vs HVG 基线) | S5 | 08_singlecell_spatial_trajectory/542_nnsvg_spatial_svg | Rscript | dual | vendor=True | deps=Bioc: nnSVG,SpatialExperiment,SingleCellExperiment,scran,scater,scuttle。支持 --outdir | medium
- squidpy-spatial-stats              | squidpy 空间统计工具箱(Moran/邻域/共现/Ripley) | S5 | 08_singlecell_spatial_trajectory/543_squidpy_spatial_statistics | python | single | vendor=True | deps=pip: squidpy,scanpy,anndata。★无 --outdir(写死 results)。默认合成 ~500 spot | high
- milo-neighborhood-da               | Milo KNN 邻域差异丰度 | S5 | 08_singlecell_spatial_trajectory/558_milo_neighborhood_da | Rscript | none | vendor=True | deps=Bioc: miloR,SingleCellExperiment,BiocNeighbors + CRAN igraph,ggbeeswarm。miloR 缺则降级。input=none 合成 demo, 支持 --outdir | high
- copykat-scrna-cnv                  | copyKAT scRNA 拷贝数/非整倍体推断 | S5 | 08_singlecell_spatial_trajectory/560_copykat_scrna_cnv | Rscript | dual | vendor=True | deps=github: copykat(navinlabcode) + CRAN ggplot2,uwot。★vendor 时务必 skip 该模块 146M 的 results/ 残留, 只带 ~1M example_data | medium
- mr-local-pipeline                  | 纯本地两样本 MR 全流程(零 OpenGWAS API) | S6 | 09_mendelian_randomization/519_local_mr_pipeline | Rscript | dual | vendor=True | deps=github: TwoSampleMR,MRPRESSO,plinkbinr + CRAN ieugwasr,ggplot2。--bfile(1000G, 大文件)可选留空跳 clump。符合用户纯本地环境 | medium
- mr-winnerscurse-care               | 赢家诅咒校正 MR(CARE/RIVW)vs 朴素基线 | S6 | 09_mendelian_randomization/533_mrcare_winnerscurse_mr | Rscript | none | vendor=True | deps=github: MRcare(可选, 缺则降级 TwoSampleMR/base R)。input=none 合成 demo, 无外部数据 | high
- mrbee-cis-mr                       | MRBEE 偏差校正估计方程 MR vs 朴素 IVW | S6 | 09_mendelian_randomization/535_mrbee_cis_mr | Rscript | dual | vendor=True | deps=github: MRBEE(noahlorinczcomi, 硬 require 缺则报错, 不含 MRBEEX)。bio_args+示例齐备 | medium
- mrlink2-region-cis                 | MR-link-2 单区域 cis-MR(因果+多效性) | S6 | 09_mendelian_randomization/536_mrlink2_region_cis_mr | python | none | vendor=True | deps=pip: numpy,scipy,statsmodels,matplotlib,pandas(mrlink2 可选, 缺则本地等价 eigh+似然比)。input=none 合成, argparse --outdir 就绪 | high
- sharepro-coloc                     | SharePro effect-group 共定位 vs 经典单因果 coloc | S6 | 09_mendelian_randomization/537_sharepro_coloc | python | none | vendor=True | deps=pip: numpy,scipy,pandas,matplotlib(SharePro 源码已 vendored 到 vendor/SharePro)。input=none, argparse --outdir/--K 就绪 | high
- aorsf-oblique-survival             | 斜分裂随机生存森林(aorsf)+诚实基线 | S7 | 12_tcga_prognosis/551_aorsf_oblique_survival | Rscript | single | vendor=True | deps=CRAN: aorsf,randomForestSRC,timeROC,survival。已硬编码 n_thread=1(本环境多线程段错误) | medium
- survex-survshap-explain            | 生存模型可解释 SurvSHAP(t)/SurvLIME | S7 | 12_tcga_prognosis/552_survex_survshap_explain | Rscript | single | vendor=True | deps=CRAN: survex(>=1.2),survival,ranger,ggplot2 | medium
- riskregression-dca-calibration     | 生存模型诚实评估:校准+DCA+时变AUC/Brier | S7 | 12_tcga_prognosis/553_riskregression_dca_calibration | Rscript | single | vendor=True | deps=CRAN: riskRegression(依赖链长),dcurves,survival,prodlim,ggplot2,data.table | medium
- communication-functional-loop      | 细胞通讯功能闭环:配体活性→UCell→富集→Venn | S5 | 16_spatial_communication/509_communication_functional_loop | Rscript | none | vendor=True | deps=CRAN: ggplot2(UCell/NicheNet 式全 base R 重写, 免大下载)。★input=none, 是 077 nichenet 的 turnkey 替身, 优先纳入 | high
- spatialglue-multiomics-baseline    | SpatialGlue 空间多组学域识别(CPU 诚实基线) | S5 | 16_spatial_communication/521_spatialglue_multiomics | python | none | vendor=True | deps=pip: scikit-learn,numpy(仅 CPU 基线 PCA+kmeans, GNN 不执行)。input=none 合成 | high
- liana-consensus-cci                | LIANA+ 多方法共识细胞-细胞通讯 | S5 | 16_spatial_communication/531_liana_consensus_cci | python | single | vendor=True | deps=pip: liana>=1.7,scanpy,anndata,plotnine。argparse --input/--groupby/--outdir 规范, 自带示例 | high
- paste-slice-alignment              | PASTE 最优传输空间切片对齐/3D 堆叠 | S5 | 16_spatial_communication/544_paste2_slice_alignment | python | dual | vendor=True | deps=pip: paste-bio(1.4.0)+POT==0.9.4(★与 POT>=0.9.5 不兼容),anndata,numpy。argparse 规范 | high
- spotlight-deconvolution            | SPOTlight(NMF+NNLS)空间 spot 细胞类型去卷积 | S5 | 16_spatial_communication/545_spotlight_deconvolution | Rscript | none | vendor=True | deps=Bioc: SPOTlight,SingleCellExperiment,scran,scuttle + CRAN scatterpie,ggplot2。input=none 合成, 支持 --outdir+合成参数 | high
- scpubr-publication-figures         | SCpubr 单细胞出版级图集+色盲安检 | S8 | 17_advanced_figures/532_scpubr_publication_figures | Rscript | single | vendor=True | deps=CRAN: SCpubr(>=3.0),Seurat,ggplot2(依赖树重, 首装慢)。支持 --input/--outdir, 示例 rds 420K | medium
- nmf-consensus-subtyping            | NMF+共识聚类分子分型 | S5 | 19_multiomics_integration/084_nmf_consensus_clustering | Rscript | single | vendor=True | deps=Bioc: ConsensusClusterPlus,ComplexHeatmap(已装) + CRAN NMF,circlize。完全 turnkey bio_args | high
- conformal-prediction-uq            | 共形预测不确定性量化 | S7 | 23_uncertainty_conformal/555_conformal_prediction_uq | python | single | vendor=True | deps=pip: mapie(1.4.x 新接口, 版本敏感),scikit-learn,scipy。★无 --outdir(写死 results/assets), 需补 --outdir | medium

### [B6-新vendor·低置信/无示例/需大数据/需改造(最后)]  (20 方法)
最难落地的一批, 共性阻塞任一:(a)无 example_data 无法一跑即验(082/087/047/081/072/073/074/076/077/080/083/522/523/524/525);(b)需 GB 级参考数据下载(047/081 cisTarget feather DB)或数百 MB rds(077 ligand_target_matrix);(c)legacy 薄封装用 --adata/--output-dir 且只出 h5ad/csv 不出 png(072-080);(d)无 --input/--outdir 硬编码固定路径需改造(505/510/511/516);(e)重环境/慢编译(557 cmdstanr 编 Stan)。建议先补小示例/改 arg 解析再验, 或标 low 仅演示。
- sccomp-composition-da              | sccomp 细胞组成差异检验(beta-binomial 贝叶斯) | S5 | 08_singlecell_spatial_trajectory/557_sccomp_composition_da | Rscript | single | vendor=True | deps=Bioc: sccomp,voomCLR,limma,edgeR + cmdstanr/cmdstan(★首跑编译 Stan 慢, 有缓存路径 hack)。有 --input/--outdir+示例 | low
- trajectory-slingshot-tradeseq-cytotrace2 | 轨迹共识(Slingshot/tradeSeq/CytoTRACE2) | S5 | 08_singlecell_spatial_trajectory/082_trajectory_multimethod_slingshot_tradeseq_cytotrace2 | Rscript | single | vendor=True | deps=Bioc: slingshot,tradeSeq,SingleCellExperiment + github CytoTRACE2 + CRAN Seurat。★无 example, flag=--seurat_rds 需真 Seurat rds | low
- palantir-branch-probability        | Palantir 拟时序+分支概率+熵 | S5 | 08_singlecell_spatial_trajectory/087_palantir_branch_probability | python | triple+ | vendor=True | deps=pip: palantir,scanpy。★无 example, --h5ad/--root_cell required 无回退, 仅出 csv 无图 | low
- tf-convergence-score               | 转录因子三证据收口(regulon×JASPAR×DepMap) | S5 | 13_tf_regulation_circos/511_tf_convergence_depmap_jaspar | Rscript | none | vendor=True | deps=CRAN: ggplot2,ggrepel。★无 --input/--outdir(固定读 example_data/合成), 仅演示, 需补 bio_args 才接用户数据 | high
- rcistarget-tf-motif-network        | RcisTarget motif-TF 调控网络 | S5 | 13_tf_regulation_circos/047_rcistarget_tf_motif_network | Rscript | triple+ | vendor=True | deps=Bioc: RcisTarget + CRAN igraph/visNetwork/networkD3。★需 ~1GB motif feather DB + motifAnnotations RData, 无 example, 硬编码 setwd, 出部分 HTML。vendor 只带脚本不带 DB | low
- pyscenic-regulon-activity          | pySCENIC 调控子 GRN+AUCell TF 活性 | S5 | 13_tf_regulation_circos/081_pyscenic_regulon_tf_activity | python | triple+ | vendor=True | deps=pip: pyscenic,arboreto,ctxcore,dask。★需 GB cisTarget ranking DB + TF list + motif annotations, 无 example, subprocess 包装不直接出 png | low
- spatial-advanced-rctd-niche        | 空间高级套件:RCTD 去卷积+NMF 生态位+共定位 | S5 | 16_spatial_communication/505_spatial_advanced | Rscript | single | vendor=True | deps=github: spacexr + Bioc mistyR + CRAN RcppML,ggplot2。★无 --input/--outdir(读/合成 spatial_demo.rds), 需改造接真实 rds。有小示例可演示 | medium
- cellrank-fate-drivers              | scVelo+CellRank 细胞命运概率与驱动基因 | S5 | 16_spatial_communication/072_cellrank_fate_drivers | python | single | vendor=True | deps=pip: scanpy,scvelo,cellrank。★legacy 薄封装, 无 example, --adata/--output-dir, 只出 h5ad+csv 不出 png, 需改造+补示例 | low
- commot-spatial-communication       | COMMOT 空间配体-受体细胞通讯 | S5 | 16_spatial_communication/073_commot_spatial_communication | python | single | vendor=True | deps=pip: commot,scanpy。★legacy, 无 example, 只出 h5ad+csv, 需空间坐标数据+改造 | low
- tangram-sc-to-spatial              | Tangram 单细胞映射到空间 | S5 | 16_spatial_communication/074_tangram_sc_to_spatial | python | dual | vendor=True | deps=pip: tangram,scanpy(device=cpu 可跑)。★legacy, 无 example, 只出 h5ad+csv, 需改造 | low
- decoupler-tf-pathway-activity      | decoupler TF/通路活性推断 | S4 | 16_spatial_communication/076_decoupler_tf_pathway_activity | python | single | vendor=True | deps=pip: decoupler,scanpy(★get_collectri/progeny 需联网 omnipath)。legacy, 无 example, 只出 h5ad+csv | low
- nichenet-ligand-target             | NicheNet 配体活性与配体-靶链接 | S5 | 16_spatial_communication/077_nichenet_ligand_target | Rscript | triple+ | vendor=True | deps=github: nichenetr。★需从 Zenodo 下数百 MB ligand_target_matrix.rds, 4 必填输入, 无 example, 只出 csv。509 是其 turnkey 替身(优先 509) | low
- cell2location-squidpy-niche        | cell2location 丰度+Squidpy 邻域生态位 | S5 | 16_spatial_communication/080_cell2location_squidpy_niche | python | single | vendor=True | deps=pip: squidpy,scanpy(cell2location 训练被规避, 仅跑 Squidpy 邻域 CPU)。★legacy, 无 example, --spatial_h5ad, 只出 h5ad+csv | low
- composite-multipanel               | 复合多panel图(Figure1: UMAP+火山+热图+森林) | S8 | 17_advanced_figures/516_composite_multipanel | Rscript | none | vendor=True | deps=CRAN: patchwork,ggrepel,ggplot2。★无 --input/--outdir 全合成模板, 用户无法喂数据, 仅演示拼版(rc=0 易但价值有限) | high
- mofa-diablo-multiomics             | MOFA2/mixOmics DIABLO 多组学潜变量整合 | S5 | 19_multiomics_integration/083_mofa_diablo_multiomics | Rscript | triple+ | vendor=True | deps=Bioc: MOFA2(+reticulate python mofapy2),mixOmics。★无 example, 自写 parse_args --mode/--views name=path, 无 png 输出。建议只留 DIABLO 分支+补示例 | low
- mutation-maftools-summary          | 体细胞突变 maftools 汇总(oncoplot) | S5 | 20_mutation_methylation_proteome/20_mutation_methylation_proteome | Rscript | single | vendor=True | deps=Bioc: maftools。★无 example(需补小 MAF), 出 PDF 非 png(需改 png), 自写 parse_args | low
- methylation-limma-dmp              | 甲基化差异探针(beta 矩阵 limma) | S3 | 20_mutation_methylation_proteome/20_mutation_methylation_proteome | Rscript | dual | vendor=True | deps=已装 limma。★无 example, 只出 csv(heatmap 未实现需补图), 自写 parse_args, --group_col 必填 | low
- proteomics-limma-dep               | 蛋白质组差异分析(蛋白矩阵 limma) | S3 | 20_mutation_methylation_proteome/20_mutation_methylation_proteome | Rscript | dual | vendor=True | deps=已装 limma。★无 example, 只出 csv(volcano/heatmap 未实现), 自写 parse_args | low
- metabolomics-ttest-dam             | 代谢组差异分析(代谢物矩阵 t 检验) | S3 | 20_mutation_methylation_proteome/20_mutation_methylation_proteome | Rscript | dual | vendor=True | deps=无(base R t.test+BH)。★无 example, 只出 csv, 限两组, 补示例+volcano 后可升 medium | low
- scmetabolism-pathway-activity      | 单细胞代谢通路活性(scMetabolism/AUCell 式) | S5 | 22_metabolism/510_scmetabolism_pathway_activity | Rscript | triple+ | vendor=True | deps=CRAN: ggplot2(打分 base R 重实现)。★脚本未解析 --expr/--meta/--outdir, 只跑内置合成 demo, 需补 getarg 才接用户数据。示例可验 rc=0 | high