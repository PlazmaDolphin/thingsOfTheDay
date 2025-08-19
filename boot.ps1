# --- Make script relative to its folder ---
Set-Location $PSScriptRoot

# --- Launch processes ---
Start-Process "C:\Program Files\Python311\python.exe" -ArgumentList "$PSScriptRoot\main.py" -PassThru
Start-Process "C:\ProgramData\chocolatey\bin\caddy.exe" -ArgumentList "run --config $PSScriptRoot\caddyfile" -PassThru

Write-Host "Running Flask + Caddy. Press Enter to stop all..."
Read-Host

# --- Cleanup ---
Write-Host "Stopping all processes..."
taskkill /IM python.exe /F /T
taskkill /IM caddy.exe /F /T

Write-Host "All processes stopped."