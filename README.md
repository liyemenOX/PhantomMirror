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
│       └── App.tsx
│
└── protocol/               # Binary protocol specification
    └── SPECIFICATION.md    # Frame headers, input packets, PLI requests
```

---

## 🚀 Quickstart

### 1. Build the Android Server
```bash
cd phantom-server
./gradlew build
```

### 2. Push & Launch Server Daemon on Android
```bash
adb push build/libs/phantom-server.jar /data/local/tmp/
adb shell CLASSPATH=/data/local/tmp/phantom-server.jar app_process / com.phantom.mirror.PhantomServer
```

### 3. Launch the Desktop Client (Linux / Windows)
```bash
cd phantom-desktop
npm install
npm run tauri dev
```

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](file:///home/useer456/PhantomMirror/LICENSE) for more information.
