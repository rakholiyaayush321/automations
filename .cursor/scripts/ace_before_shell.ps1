# ACE Before Shell Hook - Gates shell command execution
# Input: command

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$command = if ($input.command) { $input.command } else { "" }

$entry = @{event="before_shell"; command=$command; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\shell_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{"decision": "allow"}'
