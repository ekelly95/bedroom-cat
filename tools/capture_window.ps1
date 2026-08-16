# Capture the real Bedroom window's own pixels.
#
# Not a screen grab of that region: PrintWindow asks the window to render
# itself, so an overlapping window cannot contaminate the result. This exists
# because rendering the room through a copy of the app's pipeline is not proof
# of what the app actually draws — the two diverged once already.
#
#   .\tools\capture_window.ps1                # one still
#   .\tools\capture_window.ps1 -Seconds 15    # a GIF of the room actually running
#
# The moving version is the honest way to show this app: everything it does is
# motion, and a still cannot show a record turning or a cat reacting. It records
# whatever is really playing, so start the music first.

param(
    [string]$Out = "",
    [double]$Seconds = 0,
    # The app's own frame interval. Capturing faster only duplicates frames, and
    # capturing slower drops some of the cat. Keep in step with __main__.TICK_MS.
    [int]$IntervalMs = 120,
    # Crop the title bar and borders away, leaving the room alone. For pictures
    # that sit in a table in the README, where six sets of window chrome is just
    # noise; the moving one keeps its frame, because it is showing a real app.
    [switch]$Room
)

if (-not $Out) {
    $Out = if ($Seconds -gt 0) { "docs\proof\window-loop.gif" } else { "docs\proof\window-capture.png" }
}

Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinCap {
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool ClientToScreen(IntPtr h, ref POINT p);
    [DllImport("user32.dll")] public static extern bool SetProcessDpiAwarenessContext(IntPtr c);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
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

# PrintWindow always renders the whole window, chrome included, so -Room is a
# crop rather than a different capture. The client area is located by asking
# Windows where it starts on screen and subtracting the window's own origin.
$crop = $null
if ($Room) {
    $client = New-Object WinCap+RECT
    [void][WinCap]::GetClientRect($handle, [ref]$client)
    $origin = New-Object WinCap+POINT
    [void][WinCap]::ClientToScreen($handle, [ref]$origin)
    $crop = [System.Drawing.Rectangle]::new(
        $origin.X - $rect.L, $origin.Y - $rect.T,
        $client.R - $client.L, $client.B - $client.T
    )
}

function Save-Frame([string]$Path) {
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $dc = $graphics.GetHdc()
    # 0x2 = PW_RENDERFULLCONTENT, needed for hardware-composited surfaces.
    [void][WinCap]::PrintWindow($handle, $dc, 2)
    $graphics.ReleaseHdc($dc)
    if ($crop) {
        $room = $bitmap.Clone($crop, $bitmap.PixelFormat)
        $room.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
        $room.Dispose()
    } else {
        $bitmap.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    $graphics.Dispose()
    $bitmap.Dispose()
}

# Relative to where it was run from, but an absolute -Out is taken as given:
# joining one onto the working directory produced C:\repo\C:\Users\... and a
# save that reported success into a path that does not exist.
$full = if ([System.IO.Path]::IsPathRooted($Out)) { $Out } else { Join-Path (Get-Location) $Out }
New-Item -ItemType Directory -Force (Split-Path $full) | Out-Null

Write-Output "title: $($proc.MainWindowTitle)"
Write-Output "size:  ${width}x${height}"

if ($Seconds -le 0) {
    Save-Frame $full
    Write-Output "saved: $full"
    exit 0
}

$frames = [int]([math]::Round($Seconds * 1000 / $IntervalMs))
$scratch = Join-Path $env:TEMP "bedroom-record"
Remove-Item -Recurse -Force $scratch -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $scratch | Out-Null

# Timed against a stopwatch rather than sleeping a flat interval: PrintWindow
# itself takes a few milliseconds, and sleeping the full interval on top of that
# drifts slower than the app and quietly drops frames of the cat.
$clock = [System.Diagnostics.Stopwatch]::StartNew()
Write-Output "recording $Seconds s ($frames frames)..."
for ($i = 0; $i -lt $frames; $i++) {
    Save-Frame (Join-Path $scratch ("frame-{0:d4}.png" -f $i))
    $due = ($i + 1) * $IntervalMs
    $wait = $due - $clock.ElapsedMilliseconds
    if ($wait -gt 0) { Start-Sleep -Milliseconds $wait }
}
$clock.Stop()

& uv run python (Join-Path $PSScriptRoot "frames_to_gif.py") $scratch $full $IntervalMs
Remove-Item -Recurse -Force $scratch -ErrorAction SilentlyContinue
