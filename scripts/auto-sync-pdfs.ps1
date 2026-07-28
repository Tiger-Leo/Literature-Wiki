# Auto-detect new PDFs in source library
# Called by Claude Code SessionStart hook.
# Checks: is it Monday ≥ 22:00 Beijing time, and hasn't been done this ISO week?
# If yes, scans source directory, compares with pdf_sources.json, updates manifest
# with new entries, and logs the results.
#
# Stamped weekly — even if you open this project multiple times on Monday night,
# the detection only runs once per ISO week.

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CacheDir = Join-Path $ProjectRoot ".cache"
$StampFile = Join-Path $CacheDir "pdf-sync-week.txt"

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
if ($beijingNow.Month -eq 1 -and $isoWeek -gt 50) {
    $isoYear = $isoYear - 1
}
if ($beijingNow.Month -eq 12 -and $isoWeek -eq 1) {
    $isoYear = $isoYear + 1
}

$weekKey = "$isoYear-W$($isoWeek.ToString('00'))"

# ── 3. Condition check ────────────────────────────────────────────
if ($dayOfWeek -ne [System.DayOfWeek]::Monday) {
    exit 0
}

if ($hour -lt 22) {
    exit 0
}

# ── 4. Check stamp file ───────────────────────────────────────────
if (Test-Path $StampFile) {
    $lastWeek = (Get-Content $StampFile -Raw).Trim()
    if ($lastWeek -eq $weekKey) {
        exit 0
    }
}

# ── 5. Run detection ──────────────────────────────────────────────
# Write the stamp BEFORE running so concurrent opens don't double-fire
$weekKey | Out-File -FilePath $StampFile -Encoding utf8 -NoNewline

$pythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonExe) {
    Write-Warning "python not found — skipping PDF detection"
    Remove-Item $StampFile -Force -ErrorAction SilentlyContinue
    exit 1
}

$detectScript = Join-Path $ProjectRoot "scripts" "detect_new_pdfs.py"
$logFile = Join-Path $CacheDir "pdf-sync.log"
$timestamp = $beijingNow.ToString("yyyy-MM-dd HH:mm:ss")

try {
    # Run detection (--update adds new PDFs to manifest)
    $output = & $pythonExe -X utf8 $detectScript --update 2>&1 | Out-String

    # Write full output to log
    "[$timestamp] PDF sync — week $weekKey" | Out-File -FilePath $logFile -Encoding utf8
    $output | Out-File -FilePath $logFile -Encoding utf8 -Append

    # Parse new count from output
    $newCount = 0
    if ($output -match "--- NEW \((\d+)\)") {
        $newCount = [int]$Matches[1]
    }

    # ── 6. Show reminders ──────────────────────────────────────────
    if ($newCount -gt 0) {
        Write-Output ""
        Write-Output "📄 检测到 $newCount 篇新增 PDF，已更新 pdf_sources.json"
        Write-Output "   本周: $weekKey  |  时间: $timestamp"
        Write-Output "   转换新论文: python scripts/link_pdfs.py `<文献库>` --convert --new-only"
        Write-Output "   查看日志: cat .cache/pdf-sync.log"
        Write-Output ""
    } else {
        # Quiet — no new papers, just log it
        Write-Output ""
        Write-Output "📄 PDF 文献库巡检完成 — 无新增论文  (week $weekKey)"
        Write-Output ""
    }
} catch {
    Remove-Item $StampFile -Force -ErrorAction SilentlyContinue
    Write-Warning "PDF detection failed: $_"
    exit 1
}

exit 0
