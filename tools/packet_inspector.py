#!/usr/bin/env python3
"""
PhantomMirror - Protocol Packet Inspector & Telemetry Analyzer
Sniffs and decodes live UDP packets on port 49152 to verify latency,
packet fragmentation, and input event timing.
"""

import socket
import struct
import time
import sys

PORT = 49152
MAGIC = 0x504D

def main():
    print("==================================================")
    print("🔍 PhantomMirror - Wire Packet Inspector")
    print(f"[*] Sniffing UDP traffic on port {PORT}...")
    print("==================================================")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("0.0.0.0", PORT))
    except Exception as e:
        print(f"[-] Could not bind port {PORT}: {e}")
        sys.exit(1)

    packet_count = 0
    start_time = time.time()
    total_bytes = 0

    try:
        while True:
            data, addr = sock.recvfrom(2048)
            total_bytes += len(data)
            packet_count += 1

            if len(data) >= 8:
                magic, ver, ptype, seq = struct.unpack(">HBB I", data[:8])
                if magic == MAGIC:
                    type_str = {
                        0x01: "VIDEO_CHUNK",
                        0x02: "VIDEO_CONFIG",
                        0x03: "PLI_REQUEST",
                        0x10: "TOUCH_INPUT",
                        0x11: "KEY_INPUT",
                        0x20: "PING",
                        0x21: "PONG"
                    }.get(ptype, f"UNKNOWN(0x{ptype:02X})")

                    if ptype == 0x01 and len(data) >= 24:
                        frame_id, chunk_idx, total_chunks, ts = struct.unpack(">I HH Q", data[8:24])
                        print(f"[{time.strftime('%H:%M:%S')}] {addr[0]} -> {type_str:12} | Seq: {seq:5} | Frame: {frame_id:4} | Chunk: {chunk_idx+1}/{total_chunks} | Bytes: {len(data)}")
                    else:
                        print(f"[{time.strftime('%H:%M:%S')}] {addr[0]} -> {type_str:12} | Seq: {seq:5} | Bytes: {len(data)}")

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        mbps = (total_bytes * 8) / (elapsed * 1_000_000) if elapsed > 0 else 0
        print(f"\n[✓] Sniffed {packet_count} packets ({total_bytes / 1024:.1f} KB) in {elapsed:.2f}s (~{mbps:.2f} Mbps)")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
