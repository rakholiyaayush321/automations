# ACE Before MCP Hook - Gates MCP tool execution
# Input: tool_name, tool_input

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$toolName = if ($input.tool_name) { $input.tool_name } else { "unknown" }
$toolInput = if ($input.tool_input) { ($input.tool_input | ConvertTo-Json -Compress).Substring(0, [Math]::Min(500, ($input.tool_input | ConvertTo-Json -Compress).Length)) } else { "{}" }

$entry = @{event="before_mcp"; tool_name=$toolName; tool_input=$toolInput; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{"decision": "allow"}'
