# 📡 PhantomMirror Binary Protocol Specification (v1.0)

This document specifies the wire protocol used for ultra-low latency video streaming, control signals, and input event injection between the **Phantom Android Daemon** and **Phantom Desktop Client**.

---

## 1. Network Transport Model

- **Data Transport**: UDP datagrams (or QUIC streams).
- **Default Port**: `49152/udp` (Dynamic / Configurable).
- **Service Discovery**: mDNS (Multicast DNS) advertising service `_phantom-mirror._udp.local`.
- **Packet MTU**: Maximum Payload Size = 1400 bytes to avoid IP-level fragmentation across Wi-Fi networks.

---

## 2. Packet Types

Every UDP packet begins with a standard 8-byte **Phantom Header**:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Magic (0x504D)       |  Version (1)  |  Packet Type  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Sequence Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Payload...                          |
```

### Packet Type Identifiers
- `0x01`: **Video Frame Chunk** (H.265 / AV1 NAL fragment)
- `0x02`: **Video Config / SPS / PPS** (Metadata for decoder initialization)
- `0x03`: **Picture Loss Indication (PLI)** (Client requesting immediate I-frame)
- `0x10`: **Touch / Mouse Event** (Tap, movement, scroll)
- `0x11`: **Keyboard Event** (Keycodes, unicode input)
- `0x12`: **Clipboard Sync** (UTF-8 text payload)
- `0x20`: **Heartbeat / Ping-Pong** (RTT calculation)

---

## 3. Video Frame Packet Format (`0x01`)

Since H.265 frames (especially I-frames) exceed standard 1400-byte MTUs, large frames are sliced into chunks:

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                        Frame ID Number                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Chunk Index (16b)      |       Total Chunks (16b)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Presentation Timestamp                  |
|                              (64-bit)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     H.265 NAL Fragment Data                   |
|                              ...                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Packet Loss Handling
If a client detects that a `Chunk Index` is missing for an I-frame or critical P-frame:
1. It discards partial frame chunks immediately without stalling the pipeline.
2. It sends a **PLI (`0x03`)** packet to the phone.
3. The phone's `MediaCodec` immediately generates a fresh sync keyframe on the next hardware encode cycle (`MediaCodec.PARAMETER_KEY_REQUEST_SYNC_FRAME`).

---

## 4. Input Injection Packet Format (`0x10`)

Client sends touch and mouse interactions over UDP:

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Action (1B)   | Pointer ID(1B)|           Reserved            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Normalized X (0 - 65535)  |     Normalized Y (0 - 65535)  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Pressure / Wheel Delta                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Action Codes:
- `0x00`: `ACTION_DOWN` (Mouse press / finger down)
- `0x01`: `ACTION_UP` (Mouse release / finger up)
- `0x02`: `ACTION_MOVE` (Pointer dragging / motion)
- `0x08`: `ACTION_SCROLL` (Scroll wheel with vertical/horizontal delta)
- `0x04`: `ACTION_BACK` (Right-click mapped to Android Back)
- `0x05`: `ACTION_HOME` (Middle-click mapped to Android Home)
