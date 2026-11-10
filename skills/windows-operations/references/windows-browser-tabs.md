# Browser Tab Detection from WSL — Session-Proven Scripts

## 1. Detect Browser Process

```bash
<C盘>/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -Command "Get-Process | Where-Object { \$_.ProcessName -match 'chrome|msedge|firefox|opera|brave|sogou|360|qqbrowser' } | Select-Object ProcessName, Id, StartTime"
```

## 2. Get Edge Process PID and Command Line

Use this to identify the **main Edge process** (not child utility processes):

```powershell
Get-CimInstance Win32_Process -Filter "Name = 'msedge.exe'" | Select-Object ProcessId, CommandLine
```

The main process has **no** `--type=` flag. Children have `--type=renderer`, `--type=gpu-process`, etc. The main PID is what you need for UI Automation.

## 3. Full UI Automation Script (Session Verified, May 2026)

This worked on the user's system to detect an Edge tab open at `127.0.0.1:18789/chat?session=main`:

```powershell
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$targetPid = 11184  # ← REPLACE with actual main Edge PID
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ProcessIdProperty, $targetPid)
$edgeEl = $root.FindFirst([System.Windows.Automation.TreeScope]::Subtree, $cond)

if ($edgeEl) {
    $editCond = New-Object System.Windows.Automation.PropertyCondition([System.Windows.Automation.AutomationElement]::ControlTypeProperty, [System.Windows.Automation.ControlType]::Edit)
    $edits = $edgeEl.FindAll([System.Windows.Automation.TreeScope]::Subtree, $editCond)
    for ($i = 0; $i -lt $edits.Count; $i++) {
        $e = $edits[$i]
        try {
            $n = $e.Current.Name
            try {
                $vp = $e.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
                $v = $vp.Current.Value
            } catch { $v = '' }
            if ($v -match '^https?://' -or $v -match '^\d+\.\d+\.\d+\.\d+:\d+') {
                Write-Host ("URL: $v")
            }
        } catch {}
    }
}
```

## 4. Get Visible Window Titles

Quick way to find Edge browser window title:

```powershell
Add-Type @'
using System; using System.Runtime.InteropServices; using System.Text;
public class W {
    public delegate bool EWP(IntPtr h, int l);
    [DllImport("user32.dll")] public static extern int EnumWindows(EWP e, int l);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
    [DllImport("user32.dll")] public static extern int IsWindowVisible(IntPtr h);
}
'@
$results = [System.Collections.ArrayList]@()
$cb = {
    $h = $args[0]
    if ([W]::IsWindowVisible($h)) {
        $len = [W]::GetWindowTextLength($h)
        if ($len -gt 0) {
            $s = New-Object System.Text.StringBuilder 512
            [W]::GetWindowText($h, $s, 512)
            $t = $s.ToString().Trim()
            if ($t.Length -gt 0) { [void]$results.Add($t) }
        }
    }
    return $true
}
[W]::EnumWindows($cb, 0)
$results | Sort-Object -Unique | Where-Object { $_ -match 'edge|chrome|firefox|browser' }
```

## 5. Known Limitations

| Issue | Details |
|-------|---------|
| **UI Automation blocks** | `FindFirst` with `Subtree` scope can be slow on complex UIs |
| **PowerShell `$pid` reserved** | Cannot use `$pid` as a variable name — use `$targetPid` |
| **Edge --no-startup-window** | Edge may run in background with no visible window; check `Get-CimInstance` command line for `--no-startup-window` flag |
| **Shell.Application COM** | `New-Object -ComObject Shell.Application` returns 0 windows when running from WSL (no interactive session) |
| **Chrome vs Edge** | Chrome's address bar may use different UI Automation patterns; Edge is more accessible |
