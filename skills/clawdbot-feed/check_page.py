from playwright.sync_api import sync_playwright
import os, time

user_data_dir = os.path.join(os.path.dirname(__file__), 'chrome_profile')

# We can't attach to an existing context, but we can read a screenshot
# The bot process is holding the context, so let's just screenshot its window via PIL
from PIL import ImageGrab
import subprocess

# Try to find and screenshot the chromium window
r = subprocess.run([
    'powershell', '-Command',
    '''
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")]
    public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, ref RECT lpRect);
}
public struct RECT { public int Left, Top, Right, Bottom; }
"@

$procs = Get-Process | Where-Object { $_.Name -eq "chrome" -and $_.MainWindowHandle -ne 0 }
foreach ($p in $procs) {
    [Win32]::ShowWindow($p.MainWindowHandle, 9)
    [Win32]::SetForegroundWindow($p.MainWindowHandle)
    Write-Host "Brought to front: $($p.MainWindowTitle)"
    Start-Sleep -Milliseconds 500
}
    '''
], capture_output=True, text=True)
print(r.stdout.strip())

time.sleep(1.5)
img = ImageGrab.grab()
img.save(r"C:\Users\richm\.claude\skills\clawdbot-feed\screen.png")
print("Screenshot saved")
