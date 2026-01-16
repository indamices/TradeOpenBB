# Local Smart Test Runner with Auto-Diagnostic & Fix
# This script automatically detects and fixes common environment issues

$ErrorActionPreference = "Continue"
$script:issues = @()
$script:fixes = @()
$script:testErrors = @()

function Write-Status {
    param([string]$Message, [string]$Color = "White")
    Write-Host "  $Message" -ForegroundColor $Color
}

function Add-Issue {
    param([string]$Issue)
    $script:issues += $Issue
    Write-Status "⚠️  $Issue" "Yellow"
}

function Add-Fix {
    param([string]$Fix)
    $script:fixes += $Fix
    Write-Status "🔧 $Fix" "Green"
}

function Test-PythonVersion {
    Write-Host "`n[1/7] Checking Python version..." -ForegroundColor Cyan
    
    try {
        $pythonVersion = python --version 2>&1
        Write-Status "Found: $pythonVersion" "Gray"
        
        if ($pythonVersion -match "(\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            
            if ($major -eq 3 -and $minor -ge 11) {
                if ($pythonVersion -match "a|b|rc|alpha|beta") {
                    Add-Issue "Python is an alpha/beta version: $pythonVersion"
                    Add-Issue "Recommendation: Use Python 3.11.9+ stable release"
                    Write-Status "⚠️  Alpha versions may have compatibility issues" "Yellow"
                    return $false
                }
                Write-Status "✅ Python version OK" "Green"
                return $true
            } else {
                Add-Issue "Python version too old: $pythonVersion (need 3.11+)"
                return $false
            }
        }
        Add-Issue "Could not parse Python version"
        return $false
    } catch {
        Add-Issue "Python not found or not in PATH"
        return $false
    }
}

function Test-VirtualEnv {
    Write-Host "`n[2/7] Checking virtual environment..." -ForegroundColor Cyan
    
    if ($env:VIRTUAL_ENV) {
        Write-Status "✅ Virtual environment active: $env:VIRTUAL_ENV" "Green"
        return $true
    } else {
        $venvPath = Join-Path $PSScriptRoot "..\backend\venv"
        if (Test-Path $venvPath) {
            $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
            if (Test-Path $activateScript) {
                Write-Status "Activating virtual environment..." "Yellow"
                & $activateScript
                if ($env:VIRTUAL_ENV) {
                    Add-Fix "Activated virtual environment"
                    return $true
                }
            }
        }
        Write-Status "ℹ️  No virtual environment (not required, but recommended)" "Gray"
        return $true  # Not critical
    }
}

function Test-Dependencies {
    Write-Host "`n[3/7] Checking dependencies..." -ForegroundColor Cyan
    
    $requirementsFile = Join-Path $PSScriptRoot "..\backend\requirements.txt"
    if (-not (Test-Path $requirementsFile)) {
        Add-Issue "requirements.txt not found"
        return $false
    }
    
    $requiredPackages = @(
        @{Name="pytest"; Module="pytest"},
        @{Name="pytest-asyncio"; Module="pytest_asyncio"},
        @{Name="httpx"; Module="httpx"},
        @{Name="fastapi"; Module="fastapi"},
        @{Name="sqlalchemy"; Module="sqlalchemy"},
        @{Name="pydantic"; Module="pydantic"}
    )
    $missingPackages = @()
    
    foreach ($pkg in $requiredPackages) {
        $installed = python -c "import sys; sys.path.insert(0, '.'); import $($pkg.Module); print('OK')" 2>&1
        if ($LASTEXITCODE -ne 0) {
            $missingPackages += $pkg.Name
            Add-Issue "Missing package: $($pkg.Name)"
        } else {
            Write-Status "✅ $($pkg.Name) installed" "Gray"
        }
    }
    
    if ($missingPackages.Count -gt 0) {
        Write-Status "Installing missing packages..." "Yellow"
        $backendPath = Join-Path $PSScriptRoot "..\backend"
        Set-Location $backendPath
        
        # Install all requirements (more reliable than individual packages)
        python -m pip install --upgrade pip --quiet 2>&1 | Out-Null
        python -m pip install -r requirements.txt --quiet 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Add-Fix "Installed all requirements from requirements.txt"
            Set-Location $PSScriptRoot
            return $true
        } else {
            Add-Issue "Failed to install some dependencies"
            Set-Location $PSScriptRoot
            return $false
        }
    } else {
        Write-Status "✅ All required packages installed" "Green"
        return $true
    }
}

function Test-DatabaseConfig {
    Write-Host "`n[4/7] Checking database configuration..." -ForegroundColor Cyan
    
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    $envFile = Join-Path $backendPath ".env"
    
    # Create .env if it doesn't exist (same as GitHub Actions)
    if (-not (Test-Path $envFile)) {
        Write-Status "Creating .env file..." "Yellow"
        $envContent = @"
DATABASE_URL=sqlite:///./test.db
ENCRYPTION_KEY=test_key_12345678901234567890123456789012
"@
        $envContent | Out-File -FilePath $envFile -Encoding utf8 -Force
        Add-Fix "Created .env file with test configuration"
    } else {
        Write-Status "✅ .env file exists" "Green"
    }
    
    # Try to initialize database
    Write-Status "Initializing test database..." "Gray"
    Set-Location $backendPath
    $initResult = python -c "from database import init_db; init_db(); print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ Database initialized" "Green"
        Set-Location $PSScriptRoot
        return $true
    } else {
        Add-Issue "Database initialization failed"
        Write-Status "Error: $initResult" "Red"
        Set-Location $PSScriptRoot
        return $false
    }
}

function Run-Tests {
    Write-Host "`n[5/7] Running tests..." -ForegroundColor Cyan
    
    $backendPath = Join-Path $PSScriptRoot "..\backend"
    Set-Location $backendPath
    
    # Run pytest with same options as GitHub Actions
    Write-Status "Running: pytest tests/ -v --cov=. --cov-report=xml --tb=short" "Gray"
    
    $testOutputFull = @()
    python -m pytest tests/ -v --cov=. --cov-report=xml --tb=short 2>&1 | ForEach-Object {
        $testOutputFull += $_
        Write-Host $_
    }
    $testExitCode = $LASTEXITCODE
    
    Set-Location $PSScriptRoot
    $script:testErrors = $testOutputFull
    
    if ($testExitCode -eq 0) {
        Write-Status "✅ All tests passed!" "Green"
        return $true
    } else {
        Write-Status "❌ Some tests failed (exit code: $testExitCode)" "Red"
        return $false
    }
}

function Analyze-TestErrors {
    Write-Host "`n[6/7] Analyzing test errors..." -ForegroundColor Cyan
    
    if ($script:testErrors.Count -eq 0) {
        return
    }
    
    $errorText = $script:testErrors -join "`n"
    
    # Common error patterns
    $patternsFound = @()
    
    if ($errorText -match "ImportError.*typing\.Self|ModuleNotFoundError.*typing_extensions") {
        Add-Issue "Missing typing.Self or typing_extensions (Python version issue)"
        Write-Status "💡 Recommendation: Use Python 3.11.9+ stable release" "Yellow"
        $patternsFound += "typing_issue"
    }
    
    if ($errorText -match "ModuleNotFoundError.*(\w+)") {
        $moduleName = $matches[1]
        if ($moduleName -notmatch "test|pytest|typing") {
            Add-Issue "Missing module: $moduleName"
            Write-Status "💡 Try: python -m pip install $moduleName" "Yellow"
        }
    }
    
    if ($errorText -match "ValueError.*Out of range float|not JSON compliant") {
        Add-Issue "JSON serialization error (should be fixed in code)"
        Write-Status "💡 Check: backend/utils/json_serializer.py is being used" "Yellow"
    }
    
    if ($errorText -match "429.*Too Many Requests") {
        Add-Issue "Rate limiting in tests (should be disabled for pytest)"
        Write-Status "💡 Check: backend/middleware.py pytest detection" "Yellow"
    }
    
    if ($errorText -match "KeyError.*'id'") {
        Add-Issue "Test accessing response.json()['id'] without checking status_code"
        Write-Status "💡 Need to check response.status_code before accessing JSON" "Yellow"
    }
    
    # Save error log
    $errorLogPath = Join-Path $PSScriptRoot "..\test_errors.log"
    $errorText | Out-File -FilePath $errorLogPath -Encoding utf8 -Force
    Write-Status "Error log saved to: test_errors.log" "Gray"
}

function Generate-Report {
    Write-Host "`n[7/7] Generating report..." -ForegroundColor Cyan
    
    Write-Host "`n" + "="*60 -ForegroundColor Cyan
    Write-Host "  Test Diagnostic Report" -ForegroundColor Cyan
    Write-Host "="*60 -ForegroundColor Cyan
    
    Write-Host "`n📋 Issues Found: $($script:issues.Count)" -ForegroundColor Yellow
    if ($script:issues.Count -eq 0) {
        Write-Status "No issues detected" "Green"
    } else {
        foreach ($issue in $script:issues) {
            Write-Status "  • $issue" "Yellow"
        }
    }
    
    Write-Host "`n🔧 Fixes Applied: $($script:fixes.Count)" -ForegroundColor Green
    if ($script:fixes.Count -eq 0) {
        Write-Status "No fixes were needed" "Gray"
    } else {
        foreach ($fix in $script:fixes) {
            Write-Status "  ✓ $fix" "Green"
        }
    }
    
    Write-Host "`n💡 Next Steps:" -ForegroundColor Cyan
    if ($script:testErrors.Count -gt 0) {
        Write-Status "1. Review test_errors.log for detailed errors" "White"
        Write-Status "2. Check if Python version is 3.11.9+ stable (not alpha)" "White"
        Write-Status "3. Try: python -m pip install --upgrade -r backend/requirements.txt" "White"
        Write-Status "4. Consider using Docker: .\scripts\test_auto.ps1 (with Docker)" "White"
        return $false
    } else {
        Write-Status "All tests passed! Safe to push to GitHub." "Green"
        return $true
    }
}

# Main execution
Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "  Local Smart Test Runner" -ForegroundColor Cyan
Write-Host "  Auto Diagnostic & Fix Mode" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

# Change to project root
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptRoot
Set-Location ..

# Run diagnostic steps
$pythonOk = Test-PythonVersion
$venvOk = Test-VirtualEnv
$depsOk = Test-Dependencies
$dbOk = Test-DatabaseConfig

# Run tests even if some checks failed
$testsOk = Run-Tests

# Analyze errors
if (-not $testsOk) {
    Analyze-TestErrors
}

# Generate report
$finalResult = Generate-Report

# Exit with appropriate code
if ($finalResult) {
    exit 0
} else {
    exit 1
}
