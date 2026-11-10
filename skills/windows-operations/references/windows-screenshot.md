## Full-Resolution Multi-Monitor Screenshot from WSL

### One-liner PowerShell (single display, full physical resolution)

This was the exact command that worked on the user's 3000x2000 (200% DPI scaling) display:

```powershell
Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; Add-Type @' using System; using System.Runtime.InteropServices; public class N { [DllImport(\"user32.dll\")] public static extern IntPtr GetDC(IntPtr hWnd); [DllImport(\"gdi32.dll\")] public static extern int GetDeviceCaps(IntPtr hdc, int nIndex); public const int D=117; } '@; $h=[N]::GetDC([IntPtr]::Zero); $rw=[N]::GetDeviceCaps($h,[N]::D); $rh=[N]::GetDeviceCaps($h,118); $f=New-Object Windows.Forms.Form; $f.WindowState='Minimized'; $f.Show(); [Windows.Forms.Application]::DoEvents(); Start-Sleep 300; $b=New-Object Drawing.Bitmap $rw,$rh; $g=[Drawing.Graphics]::FromImage($b); $g.CopyFromScreen(0,0,0,0,[Drawing.Size]::new($rw,$rh)); $p=[IO.Path]::GetTempPath()+'ss_final.png'; $b.Save($p); $g.Dispose(); $b.Dispose(); $f.Close(); Write-Host $p
```

### Multi-monitor capture (all displays)

```powershell
$all = [Windows.Forms.Screen]::AllScreens
$l=[int]::MaxValue; $t=[int]::MaxValue; $r=[int]::MinValue; $b=[int]::MinValue
foreach($s in $all) { if($s.Bounds.Left -lt $l){$l=$s.Bounds.Left}; if($s.Bounds.Top -lt $t){$t=$s.Bounds.Top}; if($s.Bounds.Right -gt $r){$r=$s.Bounds.Right}; if($s.Bounds.Bottom -gt $b){$b=$s.Bounds.Bottom} }
$w=$r-$l; $h=$b-$t
# ... then same pattern: new Form, CopyFromScreen($l,$t,0,0,($w,$h)), save
```

### Copy to WSL and send

```bash
cp <C盘>/Users/$USER/AppData/Local/Temp/ss_final.png /tmp/
# Then in response: MEDIA:/tmp/ss_final.png
```

### Key insight
- `[System.Windows.Forms.Screen]::PrimaryScreen.Bounds` → **scaled** (1500x1000)
- `GetDeviceCaps(hdc, DESKTOPHORZRES=118)` → **physical** (3000x2000)
- Always use the physical resolution for the bitmap and CopyFromScreen
- Create a hidden `Form` first (even if minimized) to establish the Windows message pump
