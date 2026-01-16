# Auto Test Runner - Most Reliable Solution
# Priority: Docker (matches GitHub Actions) > Local Smart Diagnostic
# Usage: .\scripts\test_auto.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "  Auto Test Runner - Most Reliable Solution" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan
Write-Host ""

# Get script directory
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Join-Path $scriptRoot ".."

# Function to test Docker availability
function Test-DockerAvailable {
    try {
        $dockerVersion = docker --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker found: $dockerVersion" -ForegroundColor Green
            
            # Test if Docker daemon is running - try multiple methods
            $dockerPsResult = docker ps 2>&1 | Out-String
            $dockerPsSuccess = $LASTEXITCODE -eq 0
            
            # Also try docker info as a more reliable check
            $dockerInfoResult = docker info 2>&1 | Out-String
            $dockerInfoSuccess = $LASTEXITCODE -eq 0
            
            if ($dockerPsSuccess -or $dockerInfoSuccess) {
                Write-Host "✅ Docker daemon is running" -ForegroundColor Green
                return $true
            } else {
                # Check if it's just an API version mismatch (can still build images)
                if ($dockerPsResult -match "API version" -or $dockerInfoResult -match "API version") {
                    Write-Host "⚠️  Docker API version mismatch, but will attempt to use Docker anyway" -ForegroundColor Yellow
                    Write-Host "   Will try to build and run tests..." -ForegroundColor Yellow
                    return $true  # Still try to use Docker
                } else {
                    Write-Host "⚠️  Docker installed but daemon may not be running properly" -ForegroundColor Yellow
                    Write-Host "   Start Docker Desktop and try again" -ForegroundColor Yellow
                    return $false
                }
            }
        }
    } catch {
        Write-Host "❌ Docker not found or not accessible" -ForegroundColor Red
        return $false
    }
    return $false
}

# Function to run tests with Docker (most reliable, matches GitHub Actions)
function Run-TestsWithDocker {
    Write-Host "`n🐳 Running tests with Docker..." -ForegroundColor Cyan
    Write-Host "   (This matches GitHub Actions environment exactly)" -ForegroundColor Gray
    Write-Host ""
    
    Set-Location $projectRoot
    
    $backendPath = Join-Path $projectRoot "backend"
    $dockerfilePath = Join-Path $backendPath "Dockerfile.test"
    
    if (-not (Test-Path $dockerfilePath)) {
        Write-Host "❌ Dockerfile.test not found at: $dockerfilePath" -ForegroundColor Red
        return $false
    }
    
    # Build test image
    Write-Host "📦 Building test Docker image..." -ForegroundColor Yellow
    docker build -f $dockerfilePath -t tradeopenbb-test:latest $backendPath 2>&1 | ForEach-Object {
        Write-Host "  $_" -ForegroundColor Gray
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker build failed!" -ForegroundColor Red
        return $false
    }
    
    Write-Host "✅ Docker image built successfully" -ForegroundColor Green
    Write-Host ""
    
    # Run tests in container
    Write-Host "🧪 Running tests in Docker container..." -ForegroundColor Yellow
    Write-Host ""
    
    docker run --rm tradeopenbb-test:latest
    
    $testExitCode = $LASTEXITCODE
    
    if ($testExitCode -eq 0) {
        Write-Host "`n✅ All tests passed in Docker!" -ForegroundColor Green
        Write-Host "   This environment matches GitHub Actions exactly." -ForegroundColor Gray
        return $true
    } else {
        Write-Host "`n❌ Some tests failed in Docker" -ForegroundColor Red
        Write-Host "   This is the same result you'll get on GitHub Actions." -ForegroundColor Yellow
        return $false
    }
}

# Function to run tests locally with smart diagnostic
function Run-TestsLocally {
    Write-Host "`n💻 Falling back to local test runner with smart diagnostic..." -ForegroundColor Cyan
    Write-Host ""
    
    $localTestScript = Join-Path $scriptRoot "test_local_smart.ps1"
    
    if (-not (Test-Path $localTestScript)) {
        Write-Host "❌ Local test script not found: $localTestScript" -ForegroundColor Red
        return $false
    }
    
    & $localTestScript
    return $LASTEXITCODE -eq 0
}

# Main logic: Try Docker first, fallback to local
Write-Host "🎯 Strategy: Docker (priority) → Local Smart Diagnostic (fallback)" -ForegroundColor Cyan
Write-Host ""

$useDocker = Test-DockerAvailable

if ($useDocker) {
    Write-Host "🐳 Using Docker for testing (most reliable, matches GitHub Actions)" -ForegroundColor Green
    Write-Host ""
    
    $success = Run-TestsWithDocker
    
    if ($success) {
        Write-Host "`n" + "="*60 -ForegroundColor Green
        Write-Host "  ✅ SUCCESS: All tests passed!" -ForegroundColor Green
        Write-Host "  Safe to push to GitHub." -ForegroundColor Green
        Write-Host "="*60 -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n" + "="*60 -ForegroundColor Red
        Write-Host "  ❌ FAILED: Tests failed in Docker" -ForegroundColor Red
        Write-Host "  These same failures will occur on GitHub Actions." -ForegroundColor Yellow
        Write-Host "="*60 -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Next steps:" -ForegroundColor Cyan
        Write-Host "  1. Review the error messages above" -ForegroundColor White
        Write-Host "  2. Fix the issues in your code" -ForegroundColor White
        Write-Host "  3. Run this script again to verify fixes" -ForegroundColor White
        exit 1
    }
} else {
    Write-Host "💻 Docker not available, using local smart diagnostic..." -ForegroundColor Yellow
    Write-Host "   (Note: Local environment may differ from GitHub Actions)" -ForegroundColor Gray
    Write-Host ""
    
    $success = Run-TestsLocally
    
    if ($success) {
        Write-Host "`n" + "="*60 -ForegroundColor Green
        Write-Host "  ✅ SUCCESS: All tests passed locally!" -ForegroundColor Green
        Write-Host "  However, Docker is recommended for exact GitHub Actions match." -ForegroundColor Yellow
        Write-Host "="*60 -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`n" + "="*60 -ForegroundColor Red
        Write-Host "  ❌ FAILED: Tests failed locally" -ForegroundColor Red
        Write-Host "  Review errors above and fix issues." -ForegroundColor Yellow
        Write-Host "="*60 -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Recommendations:" -ForegroundColor Cyan
        Write-Host "  1. Install Docker Desktop for most reliable testing" -ForegroundColor White
        Write-Host "  2. Review test_errors.log for detailed errors" -ForegroundColor White
        Write-Host "  3. Fix issues and run this script again" -ForegroundColor White
        exit 1
    }
}
