# ACE After Agent Thought Hook - Captures agent thinking
# Input: text, duration_ms

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$text = if ($input.text) { $input.text.Substring(0, [Math]::Min(300, $input.text.Length)) } else { "" }
$durationMs = if ($input.duration_ms) { $input.duration_ms } else { 0 }

$entry = @{event="agent_thought"; text=$text; duration_ms=$durationMs; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\response_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{}'
