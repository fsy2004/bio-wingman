# 同步推送到 Gitee 与 GitHub —— 让两个仓库内容保持一致。
# 用法:
#   powershell -ExecutionPolicy Bypass -File dev\push-both.ps1                # 推当前已提交内容
#   powershell -ExecutionPolicy Bypass -File dev\push-both.ps1 "提交说明"      # 先 add+commit 再推
# 说明:Gitee 走 SSH 直连;GitHub 走本地代理 7892(如你无需代理,删掉 -c http.proxy 那段即可)。
param([string]$msg = "")
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
if ($msg -ne "") { git add -A; git commit -m $msg }
$branch = (git branch --show-current)
Write-Host "→ 推送 Gitee ($branch) ..." -ForegroundColor Cyan
git push gitee $branch
Write-Host "→ 推送 GitHub ($branch,经本地代理 7892)..." -ForegroundColor Cyan
git -c http.proxy=http://127.0.0.1:7892 push github $branch
Write-Host "完成。两个仓库已同步。" -ForegroundColor Green
