# ⚡ PhantomMirror

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=cylinder&color=0:0a0e14,100:032e18&height=180&section=header&text=PhantomMirror&fontSize=65&fontColor=00FF66&fontAlignY=42&desc=%E2%9A%A1%20ULTRA%20LOW-LATENCY%20WIRELESS%20DEVICE%20STREAMING%20%26%20CONTROL%20%E2%9A%A1&descAlignY=68&descAlign=50&descColor=A8FFB2" width="100%" alt="PhantomMirror Banner" />

  <p align="center">
    <b>Apple-grade fluid mobile mirroring & interactive control for Linux and Windows over Wi-Fi.</b>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-000000?style=for-the-badge&logo=linux&logoColor=white" alt="Platform" />
    <img src="https://img.shields.io/badge/Transport-UDP%20%2F%20QUIC-000000?style=for-the-badge&logo=fastapi&logoColor=00FF66" alt="Transport" />
    <img src="https://img.shields.io/badge/Video_Codec-H.265%20%2F%20HEVC-000000?style=for-the-badge&logo=youtube&logoColor=00FF66" alt="Codec" />
    <img src="https://img.shields.io/badge/Client-Rust%20%2B%20Tauri%20v2-000000?style=for-the-badge&logo=rust&logoColor=white" alt="Client" />
    <img src="https://img.shields.io/badge/License-MIT-000000?style=for-the-badge&logo=open-source-initiative&logoColor=00FF66" alt="License" />
  </p>
</div>

---

## 🎯 Why PhantomMirror?

Traditional tools like `scrcpy` over Wi-Fi suffer from noticeable latency, stuttering, and fuzzy resolution because they stream raw video frames over a **TCP** connection. Over wireless networks, any transient packet drop causes TCP **Head-of-Line Blocking**—freezing the video pipeline until retransmitted.

**PhantomMirror** solves this with a purpose-built streaming architecture:

1. **UDP / QUIC Datagram Transport**: Dropped video packets are dropped immediately in real-time rather than stalling the pipeline. Real-time frames arrive with $<15\text{ms}$ network jitter.
2. **Hardware H.265 (HEVC) / AV1 Encoding**: 50% better compression than standard H.264, delivering razor-sharp text and interface details even at high resolutions (1080p / 1440p) over Wi-Fi.
3. **Zero-Config mDNS Discovery**: No manual `adb tcpip 5555` or typing local IP addresses. Start PhantomMirror and your phone is discovered instantly.
4. **Kernel-Direct Input Injection**: Bypasses sluggish Android accessibility APIs by leveraging `InputManager.injectInputEvent` at the system level for instant mouse clicks, scroll wheel, and touch gestures.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────┐         Ultra-Low Latency UDP Datagrams        ┌────────────────────────────────────────┐
│             Android Device             │───────────────────────────────────────────────>│       Phantom Desktop (Linux/Win)      │
│                                        │  - H.265 NAL Units (KEY_LATENCY=0, CBR)        │                                        │
│  - VirtualDisplay Frame Capture        │  - Sequence Header & Frame Index               │  - Hardware Decoder (VA-API / NVDEC /  │
│  - MediaCodec Hardware Encoder         │                                                │    D3D11VA via FFmpeg)                 │
│  - mDNS Beacon (Zero-Config Announcer) │<───────────────────────────────────────────────│  - Native Zero-Copy Presentation Canvas│
│  - Kernel Input Injector (InputManager)│         Non-blocking UDP Input Packets         │  - Auto-Discovery mDNS Service Listener│
└────────────────────────────────────────┘                                                └────────────────────────────────────────┘
```

---

## ✨ Features

- ⚡ **Sub-15ms Latency**: Real-time response designed for fluid typing, scrolling, and gaming.
- 📺 **60–120 FPS High Refresh Support**: Synchronizes with modern high-refresh mobile screens.
- 🖱️ **Full Fluid Mouse & Gesture Mapping**:
  - Left click $\rightarrow$ Tap / Click
  - Right click $\rightarrow$ Back button
  - Middle click $\rightarrow$ Home screen
  - Scroll wheel $\rightarrow$ Smooth kinetic swipe & scroll
- 📋 **Bidirectional Clipboard**: Copy on your desktop, paste on your phone in real time.
- 🔒 **Screen-Off Operation**: Control your device with the physical screen completely off to preserve battery and maintain privacy.
- 🌐 **Cross-Platform**: Native builds for Linux (Wayland & X11) and Windows (10/11).

---

## 📁 Repository Structure

```
PhantomMirror/
├── phantom-server/         # Android daemon (Java/Kotlin)
│   ├── src/main/java/com/phantom/mirror/
│   │   ├── capture/        # VirtualDisplay + MediaCodec H.265 encoder
│   │   ├── input/          # Direct InputManager injection
│   │   ├── net/            # UDP non-blocking stream server
│   │   └── discovery/      # mDNS ZeroConf service beacon
│   └── build.gradle
│
├── phantom-desktop/        # Desktop Client (Rust + Tauri v2)
│   ├── src-tauri/          # High-performance Rust backend
│   │   ├── src/            # Hardware decoding & networking
│   │   └── Cargo.toml
│   └── src/                # Apple-style Glassmorphic Frontend
│       ├── components/     # Interactive StreamCanvas & Controls HUD
│       └── App.tsx
│
├── tools/                  # Diagnostics & Development Suite
│   ├── mock_phone_streamer.py # Simulated phone daemon for local client testing
│   └── packet_inspector.py    # Live UDP protocol packet sniffer
│
└── protocol/               # Binary protocol specification
    └── SPECIFICATION.md    # Frame headers, input packets, PLI requests
```

---

```

---

## 📦 Production Installation (1-Step Setup)

Install PhantomMirror globally with full desktop integration, application menu launcher, and system icons:

```bash
# Clone the repository
git clone https://github.com/liyemenOX/PhantomMirror.git
cd PhantomMirror

# Run the production installer (auto-resolves dependencies & sets up desktop launcher)
./install.sh
```

Once installed, **PhantomMirror** is accessible globally:
* **Desktop App Menu / Dock**: Search for **PhantomMirror** in your application launcher and click to open!
* **Global CLI**: Run `phantom` anywhere from your terminal.

To uninstall cleanly at any time:
```bash
./uninstall.sh
```

---

## 🚀 Usage & Commands

### 🩺 System & Hardware Health Check
Verify your ADB connectivity, GPU hardware decoding (VA-API / NVDEC), and network status:
```bash
phantom doctor
```

### ⚡ Mirroring Commands
```bash
# 1. Pro Mode with Apple Device Silhouette (Auto-adapts to your device's exact display shape & cutouts)
phantom --profile pro

# 2. Wireless / Mobile Hotspot Mode (Connects over Wi-Fi with Zero-Config Discovery)
phantom --profile pro --wireless

# 3. Virtual Session Mode (Apple iPhone Mirroring style: stays alive even if physical phone is closed/locked)
phantom --virtual-session

# 4. Launch specific app directly in Virtual Session (e.g. WhatsApp, Spotify, Settings)
phantom --virtual-session --app whatsapp

# 5. Open Desktop Control Hub (GUI Launcher)
phantom --gui

# 6. Pure Display Shape (Direct screen curvature matching device corners without outer bezel)
phantom --profile pro --pure-shape

# 7. Balanced Mode: 60 FPS, H.265, 12 Mbps (Optimized for Intel Iris Xe / AMD Radeon iGPUs)
phantom --profile balanced

# 8. Battery Saver Mode: 60 FPS, H.264, 6 Mbps, 720p (For older laptops / ultra-low power)
phantom --profile battery

# 9. Custom Viewport Scale (Specify custom window height in pixels, e.g. 850px)
phantom --profile pro --scale 850
```

---

### 🛠️ Manual Server Daemon Build & Deployment (Zero-Dependency)
```bash
# Compile and dex the server daemon (Google D8)
./phantom-server/build.sh

# Deploy directly to connected Android device via ADB
./deploy.sh
```

---

## 🧪 Local Testing Without a Physical Phone

You can test the entire desktop streaming pipeline and interactive mouse/touch controls right on your machine:

1. **Start the Mock Android Daemon**:
   ```bash
   python3 tools/mock_phone_streamer.py
   ```
2. **Start the Desktop Client**:
   ```bash
   cd phantom-desktop && npm run dev
   ```
3. Open `http://localhost:1420` in your browser. Click on the discovered device to immediately test 60 FPS streaming, mouse gestures, and real-time sub-15ms latency telemetry!

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](file:///home/useer456/PhantomMirror/LICENSE) for more information.
