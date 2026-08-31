# Auto-update Zotero Semantic Search DB
# Called by Claude Code SessionStart hook.
# Checks: is it Monday ≥ 7:00 Beijing time, and hasn't been done this ISO week?
# If yes, spawns `zotero-mcp update-db --fulltext` in background and writes stamp file.
#
# Stamped weekly — even if you open this project multiple times on Monday night,
# the update only runs once per ISO week.
#
# -Force: bypass the Monday ≥ 7:00 guard and run immediately (for manual/on-demand use).

param([switch]$Force)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CacheDir = Join-Path $ProjectRoot ".cache"
$StampFile = Join-Path $CacheDir "zotero-db-update-week.txt"

# Ensure cache directory exists
if (-not (Test-Path $CacheDir)) {
    New-Item -ItemType Directory -Path $CacheDir -Force | Out-Null
}

# ── 1. Get current Beijing time (UTC+8) ──────────────────────────
$beijingNow = [DateTime]::UtcNow.AddHours(8)
$dayOfWeek = $beijingNow.DayOfWeek
$hour = $beijingNow.Hour

# ── 2. Get ISO week number ────────────────────────────────────────
$calendar = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$isoWeek = $calendar.GetWeekOfYear(
    $beijingNow,
    [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
    [System.DayOfWeek]::Monday
)
$isoYear = $beijingNow.Year
# Edge case: if we are in January with a week number > 50, the week belongs to previous year
if ($beijingNow.Month -eq 1 -and $isoWeek -gt 50) {
    $isoYear = $isoYear - 1
}
# Edge case: if we are in December with week number 1, the week belongs to next year
if ($beijingNow.Month -eq 12 -and $isoWeek -eq 1) {
    $isoYear = $isoYear + 1
}

$weekKey = "$isoYear-W$($isoWeek.ToString('00'))"

# ── 3. Condition check (skippable via -Force) ─────────────────────
if (-not $Force) {
    if ($dayOfWeek -ne [System.DayOfWeek]::Monday) {
        # Not Monday — nothing to do
        exit 0
    }

    if ($hour -lt 7) {
        # Monday but not yet 7:00 — nothing to do
        exit 0
    }
}

# ── 4. Check stamp file ───────────────────────────────────────────
if (Test-Path $StampFile) {
    $lastWeek = (Get-Content $StampFile -Raw).Trim()
    if ($lastWeek -eq $weekKey) {
        # Already done this week — skip
        exit 0
    }
}

# ── 5. Resolve zotero-mcp and run in background ─────────────────────
# Launch zotero-mcp in background (non-blocking)
$zoteroExe = "C:\Users\pc\miniconda3\Scripts\zotero-mcp.exe"
if (-not (Test-Path $zoteroExe)) {
    # Fallback: try finding it via PATH
    $zoteroExe = (Get-Command "zotero-mcp" -ErrorAction SilentlyContinue).Source
    if (-not $zoteroExe) {
        Write-Warning "zotero-mcp not found — skipping DB update"
        exit 1
    }
}

$logFile = Join-Path $CacheDir "zotero-db-update.log"

try {
    $proc = Start-Process `
        -FilePath $zoteroExe `
        -ArgumentList "update-db --fulltext" `
        -NoNewWindow `
        -RedirectStandardOutput $logFile `
        -RedirectStandardError (Join-Path $CacheDir "zotero-db-update-error.log") `
        -PassThru

    # Write stamp ONLY after successful launch (prevents broken stamp on failure)
    $weekKey | Out-File -FilePath $StampFile -Encoding utf8 -NoNewline

    $timestamp = $beijingNow.ToString("yyyy-MM-dd HH:mm:ss")

    # ── Show a reminder in the Claude Code session ──────────────────
    Write-Output 'Zotero semantic search DB is updating in background (zotero-mcp update-db --fulltext)'
    Write-Output "   Week: $weekKey  |  Time: $timestamp  |  PID: $($proc.Id)"
    Write-Output '   Check progress: Get-Content .cache/zotero-db-update.log -Tail 20'
} catch {
    # If the background launch fails, remove the stamp so we retry next time
    Remove-Item $StampFile -Force -ErrorAction SilentlyContinue
    $errMsg = 'Failed to launch zotero-mcp update-db: ' + $_
    Write-Warning $errMsg
    exit 1
}

exit 0
