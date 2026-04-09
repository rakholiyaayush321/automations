# ACE Post-Tool Use Hook - Generic post-tool tracking
# Input: tool_type, tool_name, tool_input, tool_output, duration

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$toolType = if ($input.tool_type) { $input.tool_type } else { "unknown" }
$toolName = if ($input.tool_name) { $input.tool_name } else { "unknown" }
$toolOutput = if ($input.tool_output) { $input.tool_output.Substring(0, [Math]::Min(500, $input.tool_output.Length)) } else { "" }
$duration = if ($input.duration) { $input.duration } else { 0 }

$entry = @{event="post_tool_use"; tool_type=$toolType; tool_name=$toolName; tool_output=$toolOutput; duration=$duration; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{}'
