# Fix pydantic-core DLL issue
# This script reinstalls pydantic and pydantic-core with compatible versions

Write-Host "Fixing pydantic-core DLL issue..." -ForegroundColor Green

# Step 1: Uninstall current versions
Write-Host "`nStep 1: Uninstalling current pydantic packages..." -ForegroundColor Yellow
python -m pip uninstall -y pydantic pydantic-core 2>&1 | Out-Null

# Step 2: Install compatible versions
Write-Host "Step 2: Installing compatible versions..." -ForegroundColor Yellow
# Try installing specific compatible versions
python -m pip install --no-cache-dir pydantic==2.10.5 pydantic-core==2.27.2 2>&1

# Step 3: Verify installation
Write-Host "`nStep 3: Verifying installation..." -ForegroundColor Yellow
python -c "import pydantic; import pydantic_core; print('✅ pydantic version:', pydantic.__version__); print('✅ pydantic-core version:', pydantic_core.__version__)" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ pydantic-core DLL issue fixed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Installation completed but verification failed." -ForegroundColor Yellow
    Write-Host "Try alternative: Install from wheel file or use Docker" -ForegroundColor Yellow
}
