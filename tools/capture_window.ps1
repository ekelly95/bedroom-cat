# Capture the real Bedroom window's own pixels.
#
# Not a screen grab of that region: PrintWindow asks the window to render
# itself, so an overlapping window cannot contaminate the result. This exists
# because rendering the room through a copy of the app's pipeline is not proof
# of what the app actually draws — the two diverged once already.

param(
    [string]$Out = "docs\proof\window-capture.png"
)

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinCap {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr c);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
}
"@

# Without this, GetWindowRect hands back DPI-virtualised coordinates on a scaled
# display while PrintWindow renders at true physical resolution — so the bitmap
# is too small and captures only the top-left corner of the window. That looked
# exactly like the app clipping its own room.
[void][WinCap]::SetProcessDpiAwarenessContext([IntPtr](-4))  # PER_MONITOR_AWARE_V2

# Selected by command line, not window title: the title carries the track name
# and play/pause glyphs, which do not survive this file's encoding reliably.
$owners = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match '-m bedroom' } |
    ForEach-Object { $_.ProcessId }

$proc = Get-Process -Id $owners -ErrorAction SilentlyContinue |
    Where-Object { $_.MainWindowHandle -ne 0 } |
    Select-Object -First 1

if (-not $proc) { Write-Output "NO_WINDOW"; exit 1 }

$handle = $proc.MainWindowHandle
$rect = New-Object WinCap+RECT
[void][WinCap]::GetWindowRect($handle, [ref]$rect)
$width = $rect.R - $rect.L
$height = $rect.B - $rect.T

$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$dc = $graphics.GetHdc()
# 0x2 = PW_RENDERFULLCONTENT, needed for hardware-composited surfaces.
[void][WinCap]::PrintWindow($handle, $dc, 2)
$graphics.ReleaseHdc($dc)

$full = Join-Path (Get-Location) $Out
New-Item -ItemType Directory -Force (Split-Path $full) | Out-Null
$bitmap.Save($full, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Output "title: $($proc.MainWindowTitle)"
Write-Output "size:  ${width}x${height}"
Write-Output "saved: $full"
