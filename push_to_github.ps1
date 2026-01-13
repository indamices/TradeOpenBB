# PowerShell script to push code to GitHub
# Usage: .\push_to_github.ps1

param(
    [Parameter(Mandatory=$false)]
    [string]$RepositoryUrl = ""
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  推送到 GitHub" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Check if repository URL is provided
if ([string]::IsNullOrWhiteSpace($RepositoryUrl)) {
    Write-Host "请输入你的 GitHub 仓库 URL" -ForegroundColor Yellow
    Write-Host "格式: https://github.com/用户名/仓库名.git`n" -ForegroundColor Gray
    $RepositoryUrl = Read-Host "GitHub 仓库 URL"
}

if ([string]::IsNullOrWhiteSpace($RepositoryUrl)) {
    Write-Host "`n❌ 未提供仓库 URL，退出" -ForegroundColor Red
    exit 1
}

Write-Host "`n[1] 检查 Git 状态..." -ForegroundColor Yellow
$status = git status --porcelain
if ($status) {
    Write-Host "⚠️  有未提交的更改，正在添加..." -ForegroundColor Yellow
    git add .
    $commitMessage = Read-Host "输入提交信息（直接回车使用默认）"
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = "Update: Add cloud deployment configuration"
    }
    git commit -m $commitMessage
} else {
    Write-Host "✅ 所有更改已提交" -ForegroundColor Green
}

Write-Host "`n[2] 检查远程仓库..." -ForegroundColor Yellow
$remote = git remote get-url origin 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "当前远程仓库: $remote" -ForegroundColor Gray
    $update = Read-Host "是否更新为新的 URL? (y/n)"
    if ($update -eq "y" -or $update -eq "Y") {
        git remote set-url origin $RepositoryUrl
        Write-Host "✅ 已更新远程仓库 URL" -ForegroundColor Green
    } else {
        Write-Host "使用现有远程仓库" -ForegroundColor Gray
        $RepositoryUrl = $remote
    }
} else {
    Write-Host "添加远程仓库..." -ForegroundColor Yellow
    git remote add origin $RepositoryUrl
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ 已添加远程仓库" -ForegroundColor Green
    } else {
        Write-Host "❌ 添加远程仓库失败" -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n[3] 检查分支名称..." -ForegroundColor Yellow
$currentBranch = git branch --show-current
if ($currentBranch -eq "master") {
    Write-Host "将分支重命名为 main..." -ForegroundColor Yellow
    git branch -M main
    $currentBranch = "main"
}
Write-Host "当前分支: $currentBranch" -ForegroundColor Gray

Write-Host "`n[4] 推送到 GitHub..." -ForegroundColor Yellow
Write-Host "这可能需要几秒钟，请耐心等待...`n" -ForegroundColor Gray

try {
    git push -u origin $currentBranch
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ 代码已成功推送到 GitHub！" -ForegroundColor Green
        Write-Host "`n仓库地址: $RepositoryUrl" -ForegroundColor Cyan
        Write-Host "`n下一步:" -ForegroundColor Yellow
        Write-Host "  1. 访问你的 GitHub 仓库确认代码已上传" -ForegroundColor White
        Write-Host "  2. 在 Render 创建 Blueprint 并连接此仓库" -ForegroundColor White
        Write-Host "  3. 等待 Render 自动部署`n" -ForegroundColor White
    } else {
        Write-Host "`n❌ 推送失败" -ForegroundColor Red
        Write-Host "`n可能的原因:" -ForegroundColor Yellow
        Write-Host "  • 需要身份验证（使用 Personal Access Token）" -ForegroundColor Gray
        Write-Host "  • 远程仓库已有内容（需要先拉取）" -ForegroundColor Gray
        Write-Host "  • 网络连接问题`n" -ForegroundColor Gray
        Write-Host "请查看错误信息并重试" -ForegroundColor Yellow
    }
} catch {
    Write-Host "`n❌ 推送过程中出现错误: $_" -ForegroundColor Red
    Write-Host "`n请检查:" -ForegroundColor Yellow
    Write-Host "  1. GitHub 仓库 URL 是否正确" -ForegroundColor White
    Write-Host "  2. 是否有推送权限" -ForegroundColor White
    Write-Host "  3. 是否需要身份验证`n" -ForegroundColor White
}

Write-Host ""
