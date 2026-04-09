# ACE Subagent Start Hook - Tracks subagent spawning for AI-Trail
# Input: subagent_type, prompt, model

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue

$subagentType = if ($data.subagent_type) { $data.subagent_type } else { "unknown" }
$model = if ($data.model) { $data.model } else { "unknown" }
$promptPreview = if ($data.prompt) { $data.prompt.Substring(0, [Math]::Min(200, $data.prompt.Length)) } else { "" }

$entry = @{event="subagent_start"; type=$subagentType; model=$model; prompt_preview=$promptPreview; timestamp=(Get-Date -Format "o")} | ConvertTo-Json -Compress
$entry | Out-File -Append -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8

Write-Output "{`"decision`": `"allow`"}"
