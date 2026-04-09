# ACE Stop Hook - Hybrid: trajectory summary + ace_learn fallback nudge
# Primary: afterMCPExecution detects ace_learn (via rules instruction)
# Fallback: if ace_learn wasn't called, nudge the AI via followup_message
# Input: status, loop_count, transcript_path, conversation_id

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue
$status = $data.status
$loopCount = if ($data.loop_count) { $data.loop_count } else { 0 }
$transcriptPath = $data.transcript_path

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) { New-Item -ItemType Directory -Path $aceDir -Force | Out-Null }

# Only process completed tasks
if ($status -ne "completed") {
    Write-Output '{}'
    exit 0
}

# Aggregate trajectory
$gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
if (-not $gitBranch) { $gitBranch = "unknown" }
$gitHash = git rev-parse --short HEAD 2>$null
if (-not $gitHash) { $gitHash = "unknown" }

$mcpCount = 0; $shellCount = 0; $editCount = 0; $responseCount = 0
if (Test-Path "$aceDir\mcp_trajectory.jsonl") {
    $mcpCount = (Get-Content "$aceDir\mcp_trajectory.jsonl" | Measure-Object -Line).Lines
}
if (Test-Path "$aceDir\shell_trajectory.jsonl") {
    $shellCount = (Get-Content "$aceDir\shell_trajectory.jsonl" | Measure-Object -Line).Lines
}
if (Test-Path "$aceDir\edit_trajectory.jsonl") {
    $editCount = (Get-Content "$aceDir\edit_trajectory.jsonl" | Measure-Object -Line).Lines
}
if (Test-Path "$aceDir\response_trajectory.jsonl") {
    $responseCount = (Get-Content "$aceDir\response_trajectory.jsonl" | Measure-Object -Line).Lines
}

if ($transcriptPath) {
    @{transcript_path=$transcriptPath; saved_at=(Get-Date -Format "o")} | ConvertTo-Json -Compress | Out-File -FilePath "$aceDir\last_transcript.json" -Encoding utf8
}

$summary = "MCP:$mcpCount Shell:$shellCount Edits:$editCount Responses:$responseCount"
$entry = @{event="stop"; summary=$summary; git_branch=$gitBranch; git_hash=$gitHash; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -Append -FilePath "$aceDir\ace-relevance.jsonl" -Encoding utf8

# Hybrid: check if ace_learn was already called (review file exists)
if ($loopCount -eq 0 -and -not (Test-Path "$aceDir\ace-review-result.json")) {
    # ace_learn was NOT called — nudge the AI
    $msg = "Now call ace_learn to capture what you learned. Start the output field with TIME_SAVED: Xm | reason (estimate minutes saved by ACE patterns, 0 if none helped)."
    Write-Output "{`"followup_message`": `"$msg`"}"
} else {
    Write-Output '{}'
}
