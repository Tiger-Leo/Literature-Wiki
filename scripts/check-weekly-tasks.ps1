# Check weekly scheduled tasks - 判断本周定时任务是否已完成
# 对应两个 SessionStart 定时任务（均为「周一 >=22:00 北京时间」触发、每周一次）：
#   1) auto-sync-pdfs.ps1  -> 扫描新 PDF 并更新清单 -> stamp: .cache/pdf-sync-week.txt
#   2) auto-update-db.ps1  -> 更新 Zotero 语义搜索库  -> stamp: .cache/zotero-db-update-week.txt
#
# 用法（可在 Claude Code 中或终端直接运行）：
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-weekly-tasks.ps1
#
# 若本周某任务未完成，脚本会打印提示文字并给出可手动执行的命令。

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$CacheDir = Join-Path $ProjectRoot ".cache"

# ── 1. 当前北京时间 + ISO 周号（与 auto-*.ps1 完全一致）────────────────
$beijingNow = [DateTime]::UtcNow.AddHours(8)
$calendar = [System.Globalization.CultureInfo]::InvariantCulture.Calendar
$isoWeek = $calendar.GetWeekOfYear(
    $beijingNow,
    [System.Globalization.CalendarWeekRule]::FirstFourDayWeek,
    [System.DayOfWeek]::Monday
)
$isoYear = $beijingNow.Year
if ($beijingNow.Month -eq 1 -and $isoWeek -gt 50) { $isoYear = $isoYear - 1 }
if ($beijingNow.Month -eq 12 -and $isoWeek -eq 1) { $isoYear = $isoYear + 1 }
$weekKey = "$isoYear-W$($isoWeek.ToString('00'))"

# ── 2. 预计算路径（避免在哈希表内联命令的解析问题）──────────────────
$pdfStampFile    = Join-Path $CacheDir "pdf-sync-week.txt"
$zoteroStampFile = Join-Path $CacheDir "zotero-db-update-week.txt"
$pdfRunScript    = Join-Path $ScriptDir "auto-sync-pdfs.ps1"
$zoteroRunScript = Join-Path $ScriptDir "auto-update-db.ps1"

$tasks = @(
    @{ Name = "PDF 同步扫描（新文献入库）"; StampFile = $pdfStampFile;    RunScript = $pdfRunScript },
    @{ Name = "Zotero 语义搜索库更新";    StampFile = $zoteroStampFile; RunScript = $zoteroRunScript }
)

# ── 3. 读取 stamp（去掉 UTF-8 BOM，避免 -eq 比较失败）────────────────
function Get-WeekStamp {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $raw = Get-Content -Path $Path -Raw
    if ($null -eq $raw) { return $null }
    $raw = $raw.Trim()
    if ($raw.Length -gt 0 -and [int]$raw[0] -eq 0xFEFF) {
        $raw = $raw.Substring(1)
    }
    return $raw.Trim()
}

# ── 4. 判断「周一 >=22:00」触发窗口是否已开启（用于提示措辞）─────────
$triggerWindowOpen = $true
if ($beijingNow.DayOfWeek -eq [System.DayOfWeek]::Monday -and $beijingNow.Hour -lt 22) {
    $triggerWindowOpen = $false
}

# ── 5. 逐任务检查并输出 ─────────────────────────────────────────────
$incomplete = @()

Write-Output ""
Write-Output "══════════════════════════════════════════════════════"
Write-Output "  每周定时任务完成检查"
Write-Output "  当前时间 : $($beijingNow.ToString('yyyy-MM-dd HH:mm'))（北京时间）"
Write-Output "  当前周   : $weekKey"
Write-Output "══════════════════════════════════════════════════════"

foreach ($t in $tasks) {
    $stamp = Get-WeekStamp -Path $t.StampFile
    if ($stamp -eq $weekKey) {
        Write-Output ""
        Write-Output "  [OK] 已完成  $($t.Name)"
        Write-Output "       （本周 $weekKey 已执行，无需操作）"
    } else {
        $incomplete += $t
        Write-Output ""
        Write-Output "  [!!] 未完成  $($t.Name)"
        if ($null -eq $stamp -or $stamp -eq "") {
            Write-Output "       （尚无执行记录）"
        } else {
            Write-Output "       （上次执行：$stamp，本周 $weekKey 尚未执行）"
        }
        if (-not $triggerWindowOpen) {
            Write-Output "       提示：本周定时窗口（周一 22:00）尚未到，可稍后自动触发；也可手动运行："
        } else {
            Write-Output "       请尽快执行以下命令完成本周任务："
        }
        Write-Output "         powershell -NoProfile -ExecutionPolicy Bypass -File `"$($t.RunScript)`" -Force"
    }
}

Write-Output ""

if ($incomplete.Count -eq 0) {
    Write-Output "  结果：本周 $weekKey 两个定时任务均已完成。"
} else {
    Write-Output "  结果：本周 $weekKey 仍有 $($incomplete.Count) 个定时任务未完成，请按上述命令处理。"
}
Write-Output ""
exit 0
