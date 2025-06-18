# engineering-partner-flask/setup_env.ps1
<#
.SYNOPSIS
    Sets required environment variables for the Engineering Partner Flask application
    for the current PowerShell session.
.DESCRIPTION
    This script prompts the user for their Google Gemini API Key and an optional
    Flask Secret Key. It then sets these as environment variables for the
    duration of the current PowerShell session.
.NOTES
    Author: AI Assistant (Generated)
    Version: 1.0
#>

Write-Host "--- Engineering Partner Environment Setup (Current Session) ---" -ForegroundColor Yellow

# Prompt for Gemini API Key
$geminiApiKey = Read-Host -Prompt "Please enter your Google Gemini API Key"
if ([string]::IsNullOrWhiteSpace($geminiApiKey)) {
    Write-Error "Gemini API Key cannot be empty. Setup aborted."
    exit 1
}
$env:GEMINI_API_KEY = $geminiApiKey
Write-Host "GEMINI_API_KEY has been set for this session." -ForegroundColor Green

# Prompt for Flask Secret Key
$flaskSecretKey = Read-Host -Prompt "Enter a Flask Secret Key (optional, press Enter for a dev default from app.py)"
if (-not [string]::IsNullOrWhiteSpace($flaskSecretKey)) {
    $env:FLASK_SECRET_KEY = $flaskSecretKey
    Write-Host "FLASK_SECRET_KEY has been set for this session." -ForegroundColor Green
} else {
    Write-Host "FLASK_SECRET_KEY not set by this script. The application will use its internal default or expect it to be set elsewhere." -ForegroundColor Cyan
}

Write-Host "`nEnvironment variables configured for the current PowerShell session only." -ForegroundColor Yellow
Write-Host "To make them permanent across sessions, consider adding them to your PowerShell profile or system environment variables."
Write-Host "GEMINI_API_KEY: $($env:GEMINI_API_KEY.Substring(0, [System.Math]::Min($env:GEMINI_API_KEY.Length, 10)))... (masked for display)"
if ($env:FLASK_SECRET_KEY) {
    Write-Host "FLASK_SECRET_KEY: $($env:FLASK_SECRET_KEY.Substring(0, [System.Math]::Min($env:FLASK_SECRET_KEY.Length, 10)))... (masked for display)"
}
