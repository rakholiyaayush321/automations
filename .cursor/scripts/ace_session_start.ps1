# ACE Session Start Hook - Injects pattern context into new conversations
# Input: session_id, is_background_agent, composer_mode
# Output: additional_context, env

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

$inputJson = [Console]::In.ReadToEnd()
$data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue
$sessionId = if ($data.session_id) { $data.session_id } else { "" }
$isBg = if ($data.is_background_agent) { "true" } else { "false" }

# Clear trajectory files from previous session
@("mcp_trajectory.jsonl", "shell_trajectory.jsonl", "edit_trajectory.jsonl", "response_trajectory.jsonl", "ace-relevance.jsonl") | ForEach-Object {
    $trajFile = "$aceDir\$_"
    if (Test-Path $trajFile) { Clear-Content $trajFile }
}
if (Test-Path "$aceDir\ace-review-result.json") { Remove-Item "$aceDir\ace-review-result.json" -Force }

# Save session info
@{session_id=$sessionId; started_at=(Get-Date -Format "o"); is_background=$isBg} | ConvertTo-Json -Compress | Out-File -FilePath "$aceDir\current_session.json" -Encoding utf8

# Read cached pattern info
$patternCount = 0
$domains = ""
$cacheFile = "$aceDir\pattern_cache.json"
if (Test-Path $cacheFile) {
    try {
        $cache = Get-Content $cacheFile | ConvertFrom-Json
        $patternCount = $cache.patternCount
        $domains = ($cache.domains -join ", ")
    } catch {}
}

# Build context
if ($patternCount -gt 0) {
    $context = "[ACE Pattern Learning] This project has $patternCount patterns across domains: $domains. Use ace_search MCP tool to retrieve relevant patterns before starting work."
} else {
    $context = "[ACE Pattern Learning] ACE is configured. Use ace_search MCP tool to find patterns relevant to your task."
}

# Return env + additional_context
Write-Output "{`"env`": {`"ACE_SESSION_ID`": `"$sessionId`"}, `"additional_context`": `"$context`"}"
