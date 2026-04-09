# ACE Response Tracking Hook - Captures agent responses for AI-Trail
# Input: text (assistant final text)

$inputJson = [Console]::In.ReadToEnd()

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

# Log response to trajectory
$inputJson | Out-File -Append -FilePath "$aceDir\response_trajectory.jsonl" -Encoding utf8
