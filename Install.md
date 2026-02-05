🔒 UnlockEND - Master Installation Guide
This guide covers the full setup for Linux (Arch, CachyOS, Ubuntu, Debian, Fedora) and Windows. By following these steps, you will install all necessary dependencies and create a system shortcut to launch the app.

1. Preparation
Ensure you are inside the project root folder (UnlockEND/) before running any commands. This ensures the shortcuts point to the correct file paths.

2. Linux Setup
If you are on Arch or CachyOS, use pacman. For Ubuntu, Debian, or Mint, use apt. For Fedora, use dnf. Copy the entire block for your distribution into your terminal:

Arch / CachyOS:

sudo pacman -S --needed --noconfirm python python-pyqt6 python-cryptography
APP_DIR=$(pwd)
cat <<EOF > ~/.local/share/applications/unlockend.desktop
[Desktop Entry]
Name=UnlockEND
Exec=python3 $APP_DIR/main.py
Path=$APP_DIR
Icon=$APP_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Security;
EOF
chmod +x ~/.local/share/applications/unlockend.desktop
echo "Installation successful."

Ubuntu / Debian / Mint:


sudo apt update && sudo apt install -y python3-pyqt6 python3-cryptography
APP_DIR=$(pwd)
cat <<EOF > ~/.local/share/applications/unlockend.desktop
[Desktop Entry]
Name=UnlockEND
Exec=python3 $APP_DIR/main.py
Path=$APP_DIR
Icon=$APP_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Security;
EOF
chmod +x ~/.local/share/applications/unlockend.desktop
echo "Installation successful."

Fedora:

sudo dnf install -y python3-pyqt6 python3-cryptography
APP_DIR=$(pwd)
cat <<EOF > ~/.local/share/applications/unlockend.desktop
[Desktop Entry]
Name=UnlockEND
Exec=python3 $APP_DIR/main.py
Path=$APP_DIR
Icon=$APP_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Security;
EOF
chmod +x ~/.local/share/applications/unlockend.desktop
echo "Installation successful."

3. Windows Setup
For Windows, open PowerShell as an Administrator inside the project folder and run this combined block:

PowerShell

pip install pyqt6 cryptography
$AppDir = Get-Location
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\UnlockEND.lnk")
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = """$AppDir\main.py"""
$Shortcut.WorkingDirectory = "$AppDir"
$Shortcut.IconLocation = "$AppDir\assets\icon.ico"
$Shortcut.Save()
Write-Host "Installation successful. Shortcut created on Desktop."

4. Finalizing
Once the commands are finished, Linux users will find UnlockEND in their application menu (Start Menu). Windows users will see a new shortcut on their desktop. You can now launch the app, and it will run without a background console window.
