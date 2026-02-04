# 🔒 UnlockEND - One-Step Installation

Copy and paste this entire block into your terminal. This installs the modules and creates the app shortcut immediately.

```bash
# 1. Install all dependencies (System + Python)
sudo pacman -S --needed --noconfirm python python-pip python-pyqt6 cryptography
pip install pyqt6 cryptography --break-system-packages

# 2. Get current directory path
APP_DIR=$(pwd)

# 3. Create the .desktop file directly in your system applications folder
cat <<EOF > ~/.local/share/applications/unlockend.desktop
[Desktop Entry]
Name=UnlockEND
Comment=Masterpiece Encryption Tool
Exec=python $APP_DIR/main.py
Path=$APP_DIR
Icon=$APP_DIR/assets/icon.png
Terminal=false
Type=Application
Categories=Security;Utility;
StartupNotify=true
EOF

# 4. Make the shortcut executable
chmod +x ~/.local/share/applications/unlockend.desktop
or (if this didn't work)
You can open application from .desktop file from folder UnlockEnd

echo "✅ DONE! Look for UnlockEND in your application menu."
