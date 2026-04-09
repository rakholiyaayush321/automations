# ACE Post-Tool Use Failure Hook - Tracks tool failures
# Input: tool_type, tool_name, error_type, error_message

$inputJson = [Console]::In.ReadToEnd()
$input = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$toolType = if ($input.tool_type) { $input.tool_type } else { "unknown" }
$toolName = if ($input.tool_name) { $input.tool_name } else { "unknown" }
$errorType = if ($input.error_type) { $input.error_type } else { "unknown" }
$errorMessage = if ($input.error_message) { $input.error_message.Substring(0, [Math]::Min(500, $input.error_message.Length)) } else { "" }

$entry = @{event="tool_failure"; tool_type=$toolType; tool_name=$toolName; error_type=$errorType; error_message=$errorMessage; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8 -Append

Write-Output '{}'
