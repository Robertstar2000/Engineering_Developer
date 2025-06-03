# engineering-partner-flask/run_app.ps1
<#
.SYNOPSIS
    Activates the Python virtual environment (if present in ./.venv)
    and runs the Engineering Partner Flask application.
.DESCRIPTION
    This script checks for a '.venv' virtual environment in the current directory,
    attempts to activate it, verifies that the GEMINI_API_KEY is set (as a basic check),
    and then starts the Flask application by running 'python app.py'.
.NOTES
    Author: AI Assistant (Generated)
    Version: 1.0
#>

Write-Host "--- Starting Engineering Partner Flask Application ---" -ForegroundColor Yellow

# Check for virtual environment in the current script's directory
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
$venvPath = Join-Path $PSScriptRoot ".venv\Scripts\Activate.ps1"

if (Test-Path $venvPath) {
    Write-Host "Attempting to activate Python virtual environment: $venvPath"
    try {
        & $venvPath
        Write-Host "Virtual environment should be active. Check your prompt for '(.venv)'." -ForegroundColor Green
    } catch {
        Write-Warning "Failed to activate virtual environment using '$venvPath'."
        Write-Warning "Please ensure it's created and try activating it manually if the app fails to find packages."
    }
} else {
    Write-Warning "Virtual environment activation script not found at '$venvPath'."
    Write-Warning "If you have a venv elsewhere, please activate it manually before running the app."
}

# Basic check for GEMINI_API_KEY (app.py has more robust checks)
if ([string]::IsNullOrEmpty($env:GEMINI_API_KEY)) {
    Write-Warning "WARNING: GEMINI_API_KEY environment variable is not detected in this session."
    Write-Warning "The application's AI features might not work. You can set it using 'setup_env.ps1' or manually."
} else {
    Write-Host "GEMINI_API_KEY detected in current session." -ForegroundColor Green
}

# Locate and run the Flask application
$appPyPath = Join-Path $PSScriptRoot "app.py"
if (-not (Test-Path $appPyPath)) {
    Write-Error "Application file 'app.py' not found in '$PSScriptRoot'. Cannot start."
    exit 1
}

Write-Host "`nStarting Flask application (python app.py)..." -ForegroundColor Cyan
Write-Host "Access the application at http://127.0.0.1:5001 (or the port configured in app.py)"
Write-Host "Press CTRL+C in the terminal where app.py is running to stop the server."

# Execute python app.py. Output will appear in the current PowerShell window.
python $appPyPath

Write-Host "Flask application (python app.py) has been terminated or finished." -ForegroundColor Yellow
