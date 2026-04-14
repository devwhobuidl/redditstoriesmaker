# Build script for RedditVideoMaker (Windows)
# Requirements: Python, FFmpeg in Path OR will be downloaded by app

Write-Host "🚀 Starting Build Process for RedditVideoMaker..." -ForegroundColor Cyan

# 1. Install/Update Flet & Build dependencies
Write-Host "📦 Installing dependencies..."
pip install -r requirements.txt
pip install "flet[all]"

# 2. Run Flet Build
Write-Host "🛠️ Building Windows Executable..."
flet build windows --name "RedditVideoMaker"

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ SUCCESS! App built in build/windows/x64/runner/Release/" -ForegroundColor Green
    Write-Host "💡 You can zip the contents of that folder and share it."
} else {
    Write-Host "❌ Build failed. Check the logs above." -ForegroundColor Red
}
