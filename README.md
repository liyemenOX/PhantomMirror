# PhantomMirror

High-performance Android screen mirroring and interactive control for Linux.

PhantomMirror provides low-latency mirroring, high refresh rates (up to 120 FPS), automatic display curvature matching your phone's physical screen, and zero-configuration wireless discovery.

---

## Prerequisites

### 1. Computer
* Linux (Ubuntu, Debian, Fedora, Arch Linux, Linux Mint, etc.)
* X11 or Wayland display server

### 2. Android Phone (One-Time Setup)
1. **Enable Developer Options**: Go to **Settings** > **About Phone** and tap **Build Number** 7 times.
2. **Enable USB Debugging**: Go to **Settings** > **Developer Options** and turn on **USB Debugging**.
   *(On Xiaomi, Oppo, or Realme devices, also turn on "USB debugging (Security settings)" for keyboard and mouse input).*
3. **Authorize Your Computer**: When connecting for the first time, check *"Always allow from this computer"* on the phone's prompt and tap **Allow**.

---

## Installation

Run the automated installer:

```bash
git clone https://github.com/liyemenOX/PhantomMirror.git
cd PhantomMirror
sudo ./install.sh
```

The installer handles:
* Auto-installing required packages (`adb`, `scrcpy`, `python3-xlib`, `python3-cairo`, `gir1.2-gtk-3.0`) via `apt`, `dnf`, or `pacman`.
* Installing the `phantom` command to `/usr/local/bin`.
* Adding PhantomMirror to your desktop application menu and dock with system icons.

### Uninstall
To remove PhantomMirror and its desktop entries:
```bash
sudo ./uninstall.sh
```

---

## Quick Start

### 1. Verify System Setup
Run the diagnostics tool to check ADB, GPU hardware acceleration, and connected devices:
```bash
phantom doctor
```

### 2. Start Mirroring
* **From Application Menu**: Search for **PhantomMirror** in your desktop launcher or dock.
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
| `phantom --gui` | Open the graphical desktop control panel |
| `phantom --pure-shape` | Apply display curvature directly to the window without outer bezel |
| `phantom --profile balanced` | 60 FPS, H.265, 12 Mbps (optimized for Intel and AMD integrated GPUs) |
| `phantom --profile battery` | 60 FPS, H.264, 6 Mbps, 720p (for older hardware or battery saving) |
| `phantom --scale <height>` | Set custom window height in pixels (e.g. `phantom --scale 850`) |
| `phantom doctor` | Check dependencies, hardware decoding, and device connection status |
| `phantom -v` | Print installed version |

---

## Features

* **Ultra-Low Latency & High Refresh**: Up to 120 FPS with hardware decoding via NVIDIA NVDEC, Intel VA-API, or AMD.
* **Native Display Silhouette**: Queries physical corner radius and punch-hole cutouts from your device, masking the viewport natively via X11 XShape without video pipeline overhead.
* **Click-Through Cutouts**: Camera punch-holes pass click and swipe events directly to Android, allowing natural notification shade pulldowns.
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

* **Device is "unauthorized"**: Unlock your phone and accept the RSA prompt (*"Always allow from this computer"*).
* **Wireless device not found**: Connect the phone via USB once and run `phantom --wireless`. PhantomMirror will configure wireless mode and remember the device for future wireless runs.
* **Wayland display**: If your desktop uses Wayland, scrcpy runs via XWayland. Native window corner curvature falls back gracefully to a borderless viewport if the XShape extension is not exposed by the compositor.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
