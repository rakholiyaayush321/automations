# ACE Session End Hook - Logs session analytics
# Input: session_id, reason, duration_ms, is_background_agent
# Output: none (fire-and-forget)

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$mcpCount = 0; $shellCount = 0; $editCount = 0; $responseCount = 0
if (Test-Path "$aceDir\mcp_trajectory.jsonl") { $mcpCount = (Get-Content "$aceDir\mcp_trajectory.jsonl" | Measure-Object -Line).Lines }
if (Test-Path "$aceDir\shell_trajectory.jsonl") { $shellCount = (Get-Content "$aceDir\shell_trajectory.jsonl" | Measure-Object -Line).Lines }
if (Test-Path "$aceDir\edit_trajectory.jsonl") { $editCount = (Get-Content "$aceDir\edit_trajectory.jsonl" | Measure-Object -Line).Lines }
if (Test-Path "$aceDir\response_trajectory.jsonl") { $responseCount = (Get-Content "$aceDir\response_trajectory.jsonl" | Measure-Object -Line).Lines }

$sessionId = $data.session_id
$reason = if ($data.reason) { $data.reason } else { "unknown" }
$durationMs = if ($data.duration_ms) { $data.duration_ms } else { 0 }

$logEntry = @{
    session_id=$sessionId; reason=$reason; duration_ms=$durationMs
    trajectory=@{mcp=$mcpCount; shell=$shellCount; edits=$editCount; responses=$responseCount}
    ended_at=(Get-Date -Format "o")
} | ConvertTo-Json -Compress

$logEntry | Out-File -Append -FilePath "$aceDir\session_log.jsonl" -Encoding utf8
