# ACE MCP Tracking Hook - Captures tool executions for AI-Trail
# Also detects ace_learn calls and extracts task helpfulness (TIME_SAVED)
# Input: tool_name, tool_input, result_json, duration

$inputJson = [Console]::In.ReadToEnd()

$aceDir = ".cursor\ace"
if (-not (Test-Path $aceDir)) {
    New-Item -ItemType Directory -Path $aceDir -Force | Out-Null
}

# Always log to trajectory
$inputJson | Out-File -Append -FilePath "$aceDir\mcp_trajectory.jsonl" -Encoding utf8

# Detect ace_learn call — extract helpfulness from tool_input.output
try {
    $data = $inputJson | ConvertFrom-Json -ErrorAction SilentlyContinue
    $toolName = if ($data.tool_name) { $data.tool_name } else { "" }
} catch {
    $toolName = ""
}

if ($toolName -match "ace_learn") {
    try {
        # tool_input may be string or object
        $toolInput = $data.tool_input
        if ($toolInput -is [string]) {
            $toolInput = $toolInput | ConvertFrom-Json -ErrorAction SilentlyContinue
        }
        $outputField = if ($toolInput.output) { $toolInput.output } else { "" }
    } catch {
        $outputField = ""
    }

    # Look for TIME_SAVED: Xm | reason on the first line
    $firstLine = ($outputField -split "\n")[0]
    if ($firstLine -match "^TIME_SAVED:\s*([^|]+?)\s*(?:\|\s*(.+))?$") {
        $timeSaved = $Matches[1].Trim()
        $reason = if ($Matches[2]) { $Matches[2].Trim().Substring(0, [Math]::Min(200, $Matches[2].Trim().Length)) } else { "" }

        # Extract numeric minutes for helpful_pct
        if ($timeSaved -match "(\d+)") {
            $minutes = [int]$Matches[1]
        } else {
            $minutes = 0
        }
        # Map time to helpful %: 0m=0%, 1-4m=15%, 5-14m=30%, 15-29m=60%, 30m+=80%
        if ($minutes -ge 30) { $helpfulPct = 80 }
        elseif ($minutes -ge 15) { $helpfulPct = 60 }
        elseif ($minutes -ge 5) { $helpfulPct = 30 }
        elseif ($minutes -gt 0) { $helpfulPct = 15 }
        else { $helpfulPct = 0 }

        # Write review result (overwrites previous)
        $reviewResult = @{
            helpful_pct = $helpfulPct
            time_saved = $timeSaved
            reason = $reason
            timestamp = (Get-Date -Format "o")
        } | ConvertTo-Json -Compress
        $reviewResult | Out-File -FilePath "$aceDir\ace-review-result.json" -Encoding utf8
    }
}
