#!/usr/bin/env pwsh
# =============================================================================
# Retail Intelligencia - Full System Startup Script
# Starts: MQTT Broker -> Data Service -> API Gateway -> Dashboard -> Edge
# =============================================================================
# Usage:
#   .\start_system.ps1               # Start backend stack (no edge)
#   .\start_system.ps1 -Edge         # Start everything including edge camera
#   .\start_system.ps1 -Preview      # Start edge with visual debug window

param(
    [switch]$Edge,
    [switch]$Preview,
    [switch]$StopAll
)

$ErrorActionPreference = "Continue"
$Root = $PSScriptRoot

# -- Banner --------------------------------------------------------------------
function Write-Banner {
    Write-Host ""
    Write-Host "+--------------------------------------------+" -ForegroundColor Cyan
    Write-Host "|       RETAIL INTELLIGENCIA                 |" -ForegroundColor Cyan
    Write-Host "|       SYSTEM STARTUP                       |" -ForegroundColor Cyan
    Write-Host "+--------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Status {
    param($Component, $Status, $Detail = "")
    $color = if ($Status -in @("OK", "READY", "RUNNING", "CONNECTED")) { "Green" } else { "Yellow" }
    Write-Host ("  {0,-20} {1,-12} {2}" -f $Component, $Status, $Detail) -ForegroundColor $color
}

function Stop-All {
    Write-Host "`n[STOP] Stopping all Retail Intelligencia processes..." -ForegroundColor Yellow
    Get-Process | Where-Object { $_.MainWindowTitle -like "*retail*" -or $_.CommandLine -like "*retail*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    $ports = @(1883, 5000, 8000, 3000)
    foreach ($port in $ports) {
        $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($conn) {
            Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
        }
    }
    Write-Host "[STOP] Done." -ForegroundColor Yellow
    exit 0
}

if ($StopAll) { Stop-All }

Write-Banner

# -- Check ports --------------------------------------------------------------
function Test-Port {
    param([int]$Port)
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $conn
}

# -- 1. MQTT Broker ---------------------------------------------------------
Write-Host "> Starting MQTT Broker (port 1883)..." -ForegroundColor Cyan
if (Test-Port 1883) {
    Write-Status "MQTT Broker" "ALREADY_UP" "port 1883"
} else {
    $mqttJob = Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root'; Write-Host '[MQTT] Starting broker...'; " +
        "& '$Root\services\edge\venv\Scripts\python.exe' '$Root\infra\mqtt_broker.py'"
    ) -PassThru -WindowStyle Minimized
    Start-Sleep 3
    if (Test-Port 1883) {
        Write-Status "MQTT Broker" "OK" "pid $($mqttJob.Id) port 1883"
    } else {
        Write-Status "MQTT Broker" "STARTING" "pid $($mqttJob.Id)"
    }
}

# -- 2. Data Service (Node.js / Prisma) ---------------------------------------
Write-Host "> Starting Data Service (port 5000)..." -ForegroundColor Cyan
if (Test-Port 5000) {
    Write-Status "Data Service" "ALREADY_UP" "port 5000"
} else {
    $dataJob = Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root\services\data'; Write-Host '[DATA] Starting TypeScript Data Service...'; " +
        "npm run dev 2>&1"
    ) -PassThru -WindowStyle Minimized
    Start-Sleep 4
    if (Test-Port 5000) {
        Write-Status "Data Service" "OK" "pid $($dataJob.Id) port 5000"
    } else {
        Write-Status "Data Service" "STARTING" "pid $($dataJob.Id) (may take a moment)"
    }
}

# -- 3. API Gateway (FastAPI / uvicorn) ----------------------------------------
Write-Host "> Starting API Gateway (port 8000)..." -ForegroundColor Cyan
if (Test-Port 8000) {
    Write-Status "API Gateway" "ALREADY_UP" "port 8000"
} else {
    $apiJob = Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root\services\api'; Write-Host '[API] Starting FastAPI Gateway...'; " +
        "& '$Root\services\api\venv\Scripts\uvicorn.exe' app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1"
    ) -PassThru -WindowStyle Minimized
    Start-Sleep 4
    if (Test-Port 8000) {
        Write-Status "API Gateway" "OK" "pid $($apiJob.Id) port 8000"
    } else {
        Write-Status "API Gateway" "STARTING" "pid $($apiJob.Id)"
    }
}

# -- 4. Next.js Dashboard ------------------------------------------------------
Write-Host "> Starting Dashboard (port 3000)..." -ForegroundColor Cyan
if (Test-Port 3000) {
    Write-Status "Dashboard" "ALREADY_UP" "port 3000"
} else {
    $webJob = Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root\services\web'; Write-Host '[WEB] Starting Next.js Dashboard...'; " +
        "npm run dev 2>&1"
    ) -PassThru -WindowStyle Minimized
    Start-Sleep 6
    if (Test-Port 3000) {
        Write-Status "Dashboard" "OK" "pid $($webJob.Id) port 3000"
    } else {
        Write-Status "Dashboard" "STARTING" "pid $($webJob.Id) (compiling...)"
    }
}

# -- Wait for backends to stabilize -------------------------------------------
Write-Host "`n  Waiting for services to stabilize..." -ForegroundColor DarkGray
Start-Sleep 5

# -- Health checks -------------------------------------------------------------
Write-Host ""
Write-Host "  Health Checks:" -ForegroundColor White

try {
    $apiHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "API Gateway" "OK HEALTHY" ($apiHealth.status)
} catch {
    Write-Status "API Gateway" "STARTING" "not yet ready - check port 8000"
}

try {
    $dataHealth = Invoke-RestMethod -Uri "http://localhost:5000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Status "Data Service" "OK HEALTHY" ($dataHealth.status)
} catch {
    Write-Status "Data Service" "STARTING" "not yet ready - check port 5000"
}

# -- 5. Edge (optional) --------------------------------------------------------
if ($Edge -or $Preview) {
    Write-Host "`n> Starting Edge AI Node..." -ForegroundColor Cyan
    $edgeArgs = if ($Preview) { "--preview" } else { "" }
    $edgeJob = Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "cd '$Root\services\edge'; Write-Host '[EDGE] Starting Edge AI pipeline...'; " +
        "& '$Root\services\edge\venv\Scripts\python.exe' -m app.main $edgeArgs 2>&1"
    ) -PassThru -WindowStyle Normal
    Write-Status "Edge AI Node" "STARTING" "pid $($edgeJob.Id)"
}

# -- Final summary --------------------------------------------------------------
Write-Host ""
Write-Host "+--------------------------------------------+" -ForegroundColor Green
Write-Host "|           SYSTEM STATUS                    |" -ForegroundColor Green
Write-Host "+--------------------------------------------+" -ForegroundColor Green
Write-Host "|  MQTT Broker    - port 1883                |" -ForegroundColor Green
Write-Host "|  Data Service   - http://localhost:5000    |" -ForegroundColor Green
Write-Host "|  API Gateway    - http://localhost:8000    |" -ForegroundColor Green
Write-Host "|  Dashboard      - http://localhost:3000    |" -ForegroundColor Green
Write-Host "+--------------------------------------------+" -ForegroundColor Green
Write-Host "|  API Docs       http://localhost:8000/docs |" -ForegroundColor Cyan
Write-Host "|  API Health     http://localhost:8000/health|" -ForegroundColor Cyan
Write-Host "+--------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "  To start Edge (camera + AI):  .\start_system.ps1 -Edge" -ForegroundColor Yellow
Write-Host "  To start with debug view:      .\start_system.ps1 -Preview" -ForegroundColor Yellow  
Write-Host "  To stop everything:            .\start_system.ps1 -StopAll" -ForegroundColor Yellow
Write-Host ""
