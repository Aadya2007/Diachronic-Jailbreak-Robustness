# publish_to_github.ps1
# Automates pushing the project to https://github.com/Aadya2007/diachronic-jailbreak-robustness

$RepoName = "diachronic-jailbreak-robustness"
$Account = "Aadya2007"
$RemoteUrl = "https://github.com/$Account/$RepoName.git"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Publishing to GitHub: $Account/$RepoName" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Check git status
git branch -M main

# Set remote origin
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Updating remote origin to $RemoteUrl..." -ForegroundColor Yellow
    git remote set-url origin $RemoteUrl
} else {
    Write-Host "Adding remote origin $RemoteUrl..." -ForegroundColor Yellow
    git remote add origin $RemoteUrl
}

# Stage and commit
Write-Host "Staging and committing files..." -ForegroundColor Green
git add .
git commit -m "feat: complete diachronic and dialectal jailbreak robustness pilot study and IEEE manuscript"

# Push to GitHub
Write-Host "`nPushing main branch to $RemoteUrl..." -ForegroundColor Green
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n Successfully published! View your repository at:" -ForegroundColor Cyan
    Write-Host "https://github.com/$Account/$RepoName" -ForegroundColor Yellow
    Start-Process "https://github.com/$Account/$RepoName"
} else {
    Write-Host "`n Note: If authentication failed, either:" -ForegroundColor Red
    Write-Host "1. Run 'gh auth login' and log in as $Account" -ForegroundColor Yellow
    Write-Host "2. Or create the empty repository at https://github.com/new under $Account, then re-run this script." -ForegroundColor Yellow
}
