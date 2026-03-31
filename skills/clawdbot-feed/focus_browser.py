import subprocess, time
from PIL import ImageGrab

# Bring Chromium window to front using PowerShell
subprocess.run([
    'powershell', '-Command',
    '''
    $proc = Get-Process | Where-Object { $_.MainWindowTitle -like "*LinkedIn*" -or $_.Name -like "*chrome*" } | Where-Object { $_.MainWindowHandle -ne 0 } | Select-Object -First 1
    if ($proc) {
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {
            [DllImport("user32.dll")]
            public static extern bool SetForegroundWindow(IntPtr hWnd);
            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        }
"@
        [Win32]::ShowWindow($proc.MainWindowHandle, 9)
        [Win32]::SetForegroundWindow($proc.MainWindowHandle)
        Write-Host "Brought to front: $($proc.MainWindowTitle)"
    } else {
        Write-Host "No matching window found"
    }
    '''
], capture_output=True, text=True)

time.sleep(1.5)
img = ImageGrab.grab()
img.save(r"C:\Users\richm\.claude\skills\clawdbot-feed\screen.png")
print("Done")
