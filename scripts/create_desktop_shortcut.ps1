param(
    [string]$ProjectRoot = $(Split-Path -Parent $PSScriptRoot),
    [string]$ShortcutName = ""
)

if ([string]::IsNullOrWhiteSpace($ShortcutName)) {
    $ShortcutName = [string]::Concat(
        [char]22823, [char]35805, [char]35199, [char]28216, [char]50,
        [char]33258, [char]21160, [char]21270,
        [char]36816, [char]34892,
        [char]24179, [char]21488
    )
}

$desktop = [Environment]::GetFolderPath("Desktop")
$target = Join-Path $ProjectRoot ".venv\Scripts\pythonw.exe"
$launcher = Join-Path $ProjectRoot "scripts\launch_dhxy2_platform.py"
$iconPath = Join-Path $ProjectRoot "resources\app\dhxy2-platform.ico"
$shortcutPath = Join-Path $desktop ($ShortcutName + ".lnk")

if (-not (Test-Path $target)) {
    throw "missing target: $target"
}
if (-not (Test-Path $launcher)) {
    throw "missing launcher: $launcher"
}
if (-not (Test-Path $iconPath)) {
    throw "missing icon: $iconPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $target
$shortcut.Arguments = "`"$launcher`""
$shortcut.WorkingDirectory = $ProjectRoot
$shortcut.Description = $ShortcutName
$shortcut.IconLocation = "$iconPath,0"
$shortcut.WindowStyle = 1
$shortcut.Save()

[byte[]]$bytes = [System.IO.File]::ReadAllBytes($shortcutPath)
$bytes[0x15] = $bytes[0x15] -bor 0x20
[System.IO.File]::WriteAllBytes($shortcutPath, $bytes)

Write-Output $shortcutPath
