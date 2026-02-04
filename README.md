# UnlockEND
# 🔐 UnlockEND v1.0
**A lightweight, military-grade encryption safe for your files and folders.**

UnlockEND is a Python-based security tool designed for Linux users (optimized for CachyOS/Arch). It combines strong cryptography with a minimalist UI, allowing you to secure sensitive data in seconds without the overhead of complex volume management.



## 🚀 Key Features
- **Dual-Mode Locking**: Encrypt individual files or entire directories (automatic TAR compression).
- **Military-Grade Security**: Core engine powered by AES-GCM (Authenticated Encryption) with dynamic key rotation.
- **Stealth Mode**: Runs in the System Tray – the app stays out of your way but remains ready at any moment.
- **Hacker's Terminal**: Built-in debug console (accessible via `F12`) for advanced session control and logging.
- **Secure Shredding**: Automatically overwrites original data with random bytes before deletion to prevent recovery.
- **Modern UI**: Clean PyQt6 interface with token masking and one-click clipboard copying.



## 🛠 Technology Stack
- **Language**: Python 3.10+
- **GUI Framework**: PyQt6
- **Cryptography**: PyCA/Cryptography (AES-GCM)
- **Linux Integration**: Native support for `xdg-open`, `tar`, and `shred`.

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/UnlockEND.git](https://github.com/YOUR_USERNAME/UnlockEND.git)
   cd UnlockEND
