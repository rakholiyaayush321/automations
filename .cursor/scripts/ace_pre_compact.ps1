# ACE Pre-Compact Hook - Preserves trajectory before context compaction
# Input: trigger, context_usage_percent, context_tokens, message_count, messages_to_compact

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$trigger = if ($data.trigger) { $data.trigger } else { "auto" }
$usagePct = if ($data.context_usage_percent) { $data.context_usage_percent } else { 0 }
$tokens = if ($data.context_tokens) { $data.context_tokens } else { 0 }
$msgCount = if ($data.message_count) { $data.message_count } else { 0 }
$toCompact = if ($data.messages_to_compact) { $data.messages_to_compact } else { 0 }

$mcpCount = if (Test-Path "$aceDir\mcp_trajectory.jsonl") { (Get-Content "$aceDir\mcp_trajectory.jsonl" | Measure-Object -Line).Lines } else { 0 }
$shellCount = if (Test-Path "$aceDir\shell_trajectory.jsonl") { (Get-Content "$aceDir\shell_trajectory.jsonl" | Measure-Object -Line).Lines } else { 0 }
$editCount = if (Test-Path "$aceDir\edit_trajectory.jsonl") { (Get-Content "$aceDir\edit_trajectory.jsonl" | Measure-Object -Line).Lines } else { 0 }
$responseCount = if (Test-Path "$aceDir\response_trajectory.jsonl") { (Get-Content "$aceDir\response_trajectory.jsonl" | Measure-Object -Line).Lines } else { 0 }

$snapshot = @{
    trigger=$trigger; context_usage_percent=$usagePct; context_tokens=$tokens
    message_count=$msgCount; messages_to_compact=$toCompact
    trajectory=@{mcp=$mcpCount; shell=$shellCount; edits=$editCount; responses=$responseCount}
    timestamp=(Get-Date -Format "o")
} | ConvertTo-Json -Compress
$snapshot | Out-File -Append -FilePath "$aceDir\compaction_log.jsonl" -Encoding utf8

$msg = "Context compacting (${usagePct}% used). AI-Trail preserved: MCP:${mcpCount} Shell:${shellCount} Edits:${editCount} Responses:${responseCount}"
Write-Output "{`"user_message`": `"$msg`"}"
