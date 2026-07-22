#Requires -Version 5.1
<#
    Start Library — one-click launcher for the Library Inventory Management System.

    What it does (safe to run any time):
      1. Makes sure Python and Node.js are installed — and installs them
         automatically (via winget) if they are missing.
      2. On the first run, installs all backend and web-interface dependencies
         and sets up the database, asking you to choose the administrator password.
      3. Starts the system and opens it in your web browser.

    To stop the system, just close this window (or press Ctrl+C).

    NOTE: This starts the app for a single local computer over http://127.0.0.1.
    It runs WITHOUT database encryption, which is fine for a trusted local machine.
    To enable encryption at rest, set an LIBRARY_DB_KEY and install the SQLCipher
    driver (see backend/requirements-encryption.txt), then remove the
    LIBRARY_REQUIRE_ENCRYPTION line below.
#>

$ErrorActionPreference = 'Stop'
Set-Location -Path $PSScriptRoot

$Backend = Join-Path $PSScriptRoot 'backend'
$Frontend = Join-Path $PSScriptRoot 'frontend'
$VenvPy = Join-Path $Backend '.venv\Scripts\python.exe'
$DepsMarker = Join-Path $Backend '.venv\.deps-installed'
$StaticIndex = Join-Path $Backend 'src\static\index.html'
$Port = 8000
$Url = "http://127.0.0.1:$Port"

function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Info($msg) { Write-Host "    $msg" -ForegroundColor Gray }

# --- Local, non-tech-friendly defaults ---------------------------------------
$env:LIBRARY_COOKIE_SECURE = 'false'        # local http (not https)
$env:LIBRARY_REQUIRE_ENCRYPTION = 'false'   # plaintext DB is OK on a trusted PC
$env:LIBRARY_DB_PATH = Join-Path $Backend 'library.db'

# --- Helpers to find/auto-install required software --------------------------
function Update-Path {
    # Pick up software just installed by winget without reopening the window.
    $machine = [System.Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [System.Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Find-Python {
    foreach ($cmd in @('py -3.12', 'py -3', 'python', 'python3')) {
        $parts = $cmd.Split(' ')
        $exe = $parts[0]
        if (Get-Command $exe -ErrorAction SilentlyContinue) {
            try {
                & $exe @($parts[1..($parts.Length - 1)]) --version *> $null
                if ($LASTEXITCODE -eq 0) { return $cmd }
            } catch { }
        }
    }
    return $null
}

function Install-With-Winget($id, $friendlyName) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { return $false }
    Write-Step "Installing $friendlyName (you may see a permission prompt)..."
    winget install --id $id -e --source winget --scope user `
        --accept-package-agreements --accept-source-agreements 2>&1 | Out-Host
    # Some packages only support a machine-wide install; retry without --scope.
    if ($LASTEXITCODE -ne 0) {
        winget install --id $id -e --source winget `
            --accept-package-agreements --accept-source-agreements 2>&1 | Out-Host
    }
    Update-Path
    return $true
}

function Ensure-Python {
    $python = Find-Python
    if ($python) { return $python }
    if (Install-With-Winget 'Python.Python.3.12' 'Python 3.12') {
        $python = Find-Python
    }
    return $python
}

function Ensure-Node {
    if (Get-Command npm -ErrorAction SilentlyContinue) { return $true }
    [void](Install-With-Winget 'OpenJS.NodeJS.LTS' 'Node.js')
    return [bool](Get-Command npm -ErrorAction SilentlyContinue)
}

# --- 1. Make sure Python is available (auto-install if missing) --------------
if (-not (Test-Path $VenvPy)) {
    Write-Step 'Setting up for the first time (this happens only once)...'
    $python = Ensure-Python
    if (-not $python) {
        Write-Host "`nPython could not be installed automatically." -ForegroundColor Red
        Write-Host "Please install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "During install, tick 'Add Python to PATH', then run this again." -ForegroundColor Yellow
        Read-Host "`nPress Enter to close"
        exit 1
    }
    Write-Info "Using Python: $python"
    Write-Info 'Creating a private environment...'
    $pyParts = $python.Split(' ')
    & $pyParts[0] @($pyParts[1..($pyParts.Length - 1)]) -m venv (Join-Path $Backend '.venv')
}

# --- 2. Install/refresh backend dependencies (only when needed) --------------
if (-not (Test-Path $DepsMarker)) {
    Write-Step 'Installing backend components (a few minutes the first time)...'
    & $VenvPy -m pip install --upgrade pip
    & $VenvPy -m pip install -r (Join-Path $Backend 'requirements.txt')
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`nInstalling backend components failed. Please check your internet connection and try again." -ForegroundColor Red
        Read-Host "`nPress Enter to close"
        exit 1
    }
    New-Item -ItemType File -Path $DepsMarker -Force | Out-Null
}

# --- 3. Install web-interface dependencies and build it ----------------------
$NodeModules = Join-Path $Frontend 'node_modules'
$NeedFrontendDeps = -not (Test-Path $NodeModules)
$NeedBuild = -not (Test-Path $StaticIndex)

if ($NeedFrontendDeps -or $NeedBuild) {
    if (-not (Ensure-Node)) {
        Write-Host "`nNode.js could not be installed automatically." -ForegroundColor Red
        Write-Host "Please install Node.js (LTS) from https://nodejs.org/ and run this again." -ForegroundColor Yellow
        Read-Host "`nPress Enter to close"
        exit 1
    }
    Push-Location $Frontend
    try {
        if ($NeedFrontendDeps) {
            Write-Step 'Installing web-interface components (first time only)...'
            npm install
            if ($LASTEXITCODE -ne 0) { throw 'npm install failed' }
        }
        if ($NeedBuild) {
            Write-Step 'Building the web interface (first time only)...'
            npm run build
            if ($LASTEXITCODE -ne 0) { throw 'npm run build failed' }
        }
    } catch {
        Pop-Location
        Write-Host "`nPreparing the web interface failed: $_" -ForegroundColor Red
        Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
        Read-Host "`nPress Enter to close"
        exit 1
    }
    Pop-Location
}

# --- 4. Prepare the database + administrator account -------------------------
Write-Step 'Preparing the database...'
Push-Location $Backend
try {
    & $VenvPy -m src.core.schema_init
    # First run only: this asks you to choose the administrator password.
    # (On later runs it detects the existing account and does nothing.)
    & $VenvPy -m src.core.setup
} finally { Pop-Location }

# --- 5. Start the server, open the browser, and wait -------------------------
Write-Step "Starting the Library system..."
Push-Location $Backend
$server = Start-Process -FilePath $VenvPy `
    -ArgumentList @('-m', 'uvicorn', 'src.main:app', '--host', '127.0.0.1', '--port', "$Port") `
    -PassThru -NoNewWindow
Pop-Location

try {
    # Wait until the server answers before opening the browser.
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "$Url/healthz" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
    }

    if ($ready) {
        Write-Host "`n============================================================" -ForegroundColor Green
        Write-Host "  The Library system is running at:  $Url" -ForegroundColor Green
        Write-Host "  Your browser should open automatically." -ForegroundColor Green
        Write-Host "  Keep this window open. Close it to stop the system." -ForegroundColor Green
        Write-Host "============================================================`n" -ForegroundColor Green
        Start-Process $Url
    } else {
        Write-Host "The server did not start in time. Open $Url manually." -ForegroundColor Yellow
    }

    # Keep running until the server stops or the window is closed.
    Wait-Process -Id $server.Id
} finally {
    if ($server -and -not $server.HasExited) {
        Write-Host "`nStopping the Library system..." -ForegroundColor Cyan
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
    }
}
