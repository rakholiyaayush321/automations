# Kill processes holding applications.csv
$csvPath = "C:\Users\rakho\.openclaw\workspace\job_apply\applications.csv"
$locked = $true
try {
    $fh = [System.IO.File]::Open($csvPath, "Open", "ReadWrite", "None")
    $fh.Close()
    $locked = $false
    Write-Host "File is NOT locked"
} catch {
    Write-Host "File is LOCKED by: $($_.Exception.Message)"
    # Find and kill processes that might be holding it
    Get-Process | Where-Object { $_.MainWindowTitle -like "*job_apply*" -or $_.MainWindowTitle -like "*excel*" -or $_.MainWindowTitle -like "*csv*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "Attempted to release lock"
}
