# PhantomMirror

High-performance Android screen mirroring and interactive control for **Windows** & **Linux**.

PhantomMirror provides ultra-low latency mirroring, high refresh rates (up to 120 FPS), automatic display curvature matching your phone's physical screen, click-through camera cutouts, and zero-configuration wireless discovery.

---

## Prerequisites

### 1. Computer
* **Windows**: Windows 10 or Windows 11 (64-bit)
* **Linux**: Ubuntu, Debian, Fedora, Arch Linux, Linux Mint, etc. (X11 or Wayland)

### 2. Android Phone (One-Time Setup)
1. **Enable Developer Options**: Go to **Settings** > **About Phone** and tap **Build Number** 7 times.
2. **Enable USB Debugging**: Go to **Settings** > **Developer Options** and turn on **USB Debugging**.
   *(On Xiaomi, Oppo, or Realme devices, also turn on "USB debugging (Security settings)" for keyboard and mouse input).*
3. **Authorize Your Computer**: When connecting for the first time, check *"Always allow from this computer"* on the phone's prompt and tap **Allow**.

---

## Installation

### Windows Installation

You can install PhantomMirror with a single PowerShell command or run the bootstrapper:

#### Option A: Automated PowerShell Installer (Recommended)
Open PowerShell and run:
```powershell
git clone https://github.com/liyemenOX/PhantomMirror.git
cd PhantomMirror
.\install.ps1
```
*(Or double-click `install.bat` from File Explorer).*

The Windows installer automatically handles:
* Detecting and installing `Python 3`, `adb` (Android Platform-Tools), and `scrcpy` (via `winget` or direct official release bundles).
* Deploying PhantomMirror to `%LOCALAPPDATA%\PhantomMirror`.
* Adding `phantom` to your User `PATH` so you can launch it from Command Prompt, PowerShell, or Windows Terminal.
* Creating Windows **Desktop** and **Start Menu** shortcuts with high-resolution app icons.

#### Windows Uninstall
To remove PhantomMirror, shortcuts, and PATH entries:
```powershell
.\uninstall.ps1
```
*(Or run `uninstall.bat`).*

---

### Linux Installation

Run the automated installer:
```bash
git clone https://github.com/liyemenOX/PhantomMirror.git
cd PhantomMirror
sudo ./install.sh
```

The Linux installer handles:
* Auto-installing required packages (`adb`, `scrcpy`, `python3-xlib`, `python3-cairo`, `gir1.2-gtk-3.0`) via `apt`, `dnf`, or `pacman`.
* Installing the `phantom` command to `/usr/local/bin`.
* Adding PhantomMirror to your desktop application menu and dock with system icons.

#### Linux Uninstall
To remove PhantomMirror and its desktop entries:
```bash
sudo ./uninstall.sh
```

---

## Quick Start

### 1. Verify System Setup
Run the diagnostics tool to check ADB, GPU hardware acceleration (D3D11VA / NVDEC / VA-API), and connected devices:
```bash
# Windows (PowerShell or CMD) or Linux
phantom doctor
```

### 2. Start Mirroring
* **From Desktop / Start Menu**: Click on the **PhantomMirror** app icon.
* **From Terminal**:
  ```bash
  # Wireless mirroring (auto-discovers your device over Wi-Fi)
  phantom --profile pro --wireless

  # USB mirroring (plug-and-play)
  phantom --profile pro
  ```

### 3. Virtual Session Mode (Phone Screen Stays Off)
Work in an independent display session while keeping the phone's physical screen locked and dark:
```bash
phantom --virtual-session
```
Launch a specific app directly:
```bash
phantom --virtual-session --app whatsapp
```

---

## Command Reference

| Command | Description |
| :--- | :--- |
| `phantom --profile pro` | High performance (120 FPS, H.265, 24 Mbps, hardware accelerated) |
| `phantom --profile pro --wireless` | Auto-discovers and connects to your phone over Wi-Fi |
| `phantom --virtual-session` | Independent virtual session with physical screen turned off |
| `phantom --virtual-session --app <name>` | Launch directly into a specific app (e.g. `whatsapp`, `spotify`) |
| `phantom --gui` | Open graphical desktop control panel (Tkinter / GTK) |
| `phantom --pure-shape` | Apply display curvature directly to the window without outer bezel |
| `phantom --profile balanced` | 60 FPS, H.265, 12 Mbps (optimized for Intel and AMD integrated GPUs) |
| `phantom --profile battery` | 60 FPS, H.264, 6 Mbps, 720p (for older hardware or battery saving) |
| `phantom --scale <height>` | Set custom window height in pixels (e.g. `phantom --scale 850`) |
| `phantom doctor` | Check dependencies, hardware decoding, and device connection status |
| `phantom -v` | Print installed version |

---

## Features

* **Cross-Platform Parity**: Fully native experience on both **Windows 10/11** and **Linux**.
* **Ultra-Low Latency & High Refresh**: Up to 120 FPS with hardware decoding via NVIDIA NVDEC, Intel D3D11VA / VA-API, or AMD Radeon AMF.
* **Native Display Silhouette**: Queries physical corner radius and punch-hole cutouts from your device:
  * **Windows**: Dynamically masks the viewport using native Win32 DWM and `SetWindowRgn`.
  * **Linux**: Masks the viewport using X11 XShape.
* **Click-Through Cutouts**: Camera punch-holes and Dynamic Islands pass click and swipe events directly to Android, allowing natural notification shade pulldowns.
* **Zero-Config Wireless Pairing**: Automatically finds paired devices using local ARP cache, mDNS, and parallel subnet discovery.
* **Screen-Off & Virtual Sessions**: Control apps without waking the physical screen or draining battery.
* **Bidirectional Clipboard & Shortcuts**:
  * Left Click: Tap
  * Right Click: Back
  * Middle Click: Home
  * Scroll Wheel: Kinetic swipe and scroll
  * Ctrl + C / Ctrl + V: Synchronized clipboard

---

## Troubleshooting

### Windows
* **`phantom` command not recognized**: Open a new terminal window after installation so the updated `PATH` takes effect.
* **Firewall prompt**: Allow `adb.exe` and `scrcpy.exe` on private networks if Windows Defender Firewall prompts you.
* **Device not detected in USB**: Verify that OEM USB drivers (Samsung, Google, Xiaomi, etc.) are installed on Windows. Run `phantom doctor` to verify.

### Linux
* **Device is "unauthorized"**: Unlock your phone and accept the RSA prompt (*"Always allow from this computer"*).
* **Wireless device not found**: Connect the phone via USB once and run `phantom --wireless`. PhantomMirror will configure wireless mode and remember the device for future wireless runs.
* **Wayland display**: If your desktop uses Wayland, scrcpy runs via XWayland. Native window corner curvature falls back gracefully to a borderless viewport if the XShape extension is not exposed by the compositor.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
