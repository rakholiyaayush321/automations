# ACE Subagent Stop Hook - Tracks subagent completion for AI-Trail
# Input: subagent_type, status, result, duration, agent_transcript_path

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$subagentType = if ($data.subagent_type) { $data.subagent_type } else { "unknown" }
$status = if ($data.status) { $data.status } else { "unknown" }
$duration = if ($data.duration) { $data.duration } else { 0 }
$transcript = $data.agent_transcript_path
$hasTranscript = if ($transcript) { "true" } else { "false" }

$entry = @{event="subagent_stop"; type=$subagentType; status=$status; duration_ms=$duration; has_transcript=$hasTranscript; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -Append -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8

if ($transcript) {
    $transcriptEntry = @{subagent_type=$subagentType; transcript_path=$transcript; status=$status; duration_ms=$duration; saved_at=(Get-Date -Format "o")} | ConvertTo-Json -Compress
    $transcriptEntry | Out-File -Append -FilePath "$aceDir\subagent_transcripts.jsonl" -Encoding utf8
}

exit 0
