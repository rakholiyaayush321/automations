# ACE Pre-Tool Use Hook - Gates tool execution
# Input: tool_type, tool_name, tool_input

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$toolType = if ($input.tool_type) { $input.tool_type } else { "unknown" }
$toolName = if ($input.tool_name) { $input.tool_name } else { "unknown" }
$toolInput = if ($input.tool_input) { ($input.tool_input | ConvertTo-Json -Compress).Substring(0, [Math]::Min(500, ($input.tool_input | ConvertTo-Json -Compress).Length)) } else { "{}" }

$entry = @{event="pre_tool_use"; tool_type=$toolType; tool_name=$toolName; tool_input=$toolInput; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{"decision": "allow"}'
