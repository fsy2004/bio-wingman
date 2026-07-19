# =====================================================================
# Bio Wingman 环境安装(透明·可选镜像源)。
# 源可由参数传入(前端下拉/命令行);不传则用默认清华。是"哑执行器",只按给定源装。
# 生信 R 包分两路:CRAN 包走 install.packages;Bioconductor 包(limma 等)走 BiocManager。
# 用法:
#   powershell -ExecutionPolicy Bypass -File setup\install.ps1
#   powershell -ExecutionPolicy Bypass -File setup\install.ps1 -CranRepo https://mirrors.aliyun.com/CRAN -BiocMirror https://mirrors.aliyun.com/bioconductor
# =====================================================================
param(
  [string]$PipIndex       = "https://pypi.tuna.tsinghua.edu.cn/simple",
  [string]$PipTrustedHost = "pypi.tuna.tsinghua.edu.cn",
  [string]$CranRepo       = "https://mirrors.tuna.tsinghua.edu.cn/CRAN",
  [string]$BiocMirror     = "https://mirrors.tuna.tsinghua.edu.cn/bioconductor"
)
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$req  = Get-Content (Join-Path $root "config\requirements.json") -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "================ Bio Wingman 环境安装 ================" -ForegroundColor Cyan
Write-Host ("  安装源 · pip  = {0}" -f $PipIndex)  -ForegroundColor DarkGray
Write-Host ("  安装源 · CRAN = {0}" -f $CranRepo)  -ForegroundColor DarkGray
Write-Host ("  安装源 · Bioc = {0}" -f $BiocMirror) -ForegroundColor DarkGray
Write-Host ""

# ---- Python(后端,轻)----
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
  Write-Host ("[缺失] 未找到 Python,请先安装 Python {0} 及以上:" -f $req.python_min) -ForegroundColor Yellow
  Write-Host "    winget install Python.Python.3.12    或    https://www.python.org/downloads/"
} else {
  Write-Host ("[就绪] Python:{0}" -f (python --version)) -ForegroundColor Green
  Write-Host ("  计划:pip 安装 {0}(源:{1})" -f ($req.python_packages -join ", "), $PipIndex)
  python -m pip install -i $PipIndex --trusted-host $PipTrustedHost @($req.python_packages)
}
Write-Host ""

# ---- R(10+1 方法)----
# ★与 env_check 一致的离线发现:R 默认安装不加 PATH,若只按 PATH 找会漏装所有 R 包(与面板矛盾)。
function Find-Rscript {
  $c = Get-Command Rscript -ErrorAction SilentlyContinue
  if ($c) { return $c.Source }
  $bases = @("$env:ProgramFiles\R", "${env:ProgramFiles(x86)}\R", "$env:LOCALAPPDATA\Programs\R", "D:\R")
  foreach ($b in $bases) {
    if (Test-Path $b) {
      $hit = Get-ChildItem -Path $b -Recurse -Filter Rscript.exe -ErrorAction SilentlyContinue |
             Sort-Object FullName -Descending | Select-Object -First 1
      if ($hit) { return $hit.FullName }
    }
  }
  return $null
}
$rscript = Find-Rscript
if (-not $rscript) {
  Write-Host ("[缺失] 未找到 R,请先安装 R {0} 及以上:" -f $req.r_min) -ForegroundColor Yellow
  Write-Host "    winget install RProject.R    或    https://mirrors.tuna.tsinghua.edu.cn/CRAN/"
} else {
  $bioc = @($req.r_bioc_packages)
  Write-Host ("[就绪] R:{0}({1})" -f ((& $rscript --version 2>&1 | Select-Object -First 1), $rscript)) -ForegroundColor Green
  Write-Host ("  计划:CRAN 包 {0} 个 + Bioc 包 {1} 个" -f $req.r_packages.Count, $bioc.Count)
  # 传参:CRAN源 Bioc镜像 <cran包...> -- <bioc包...>
  $rargs = @($CranRepo, $BiocMirror) + @($req.r_packages) + @("--") + $bioc
  & $rscript (Join-Path $PSScriptRoot "install_r_packages.R") @rargs
}
Write-Host "================ 完成 ================" -ForegroundColor Cyan
Write-Host "随时可重新体检:python setup\env_check.py"
