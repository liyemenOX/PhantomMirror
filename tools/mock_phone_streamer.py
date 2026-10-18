#!/usr/bin/env python3
"""
PhantomMirror - Mock Phone Daemon Simulator
Simulates an Android device running the Phantom Server daemon.
Enables full end-to-end testing of the desktop client without a physical Android phone.
"""

import socket
import struct
import time
import sys

PORT = 49152
MAGIC = 0x504D
TYPE_VIDEO_CHUNK = 0x01
TYPE_INPUT_TOUCH = 0x10
TYPE_INPUT_KEY = 0x11
TYPE_HEARTBEAT_PING = 0x20
TYPE_HEARTBEAT_PONG = 0x21

def main():
    print("==================================================")
    print("⚡ PhantomMirror - Mock Android Daemon Simulator")
    print(f"[*] Binding UDP server on 0.0.0.0:{PORT}...")
    print("==================================================")

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", PORT))
    sock.setblocking(False)

    print(f"[+] Listening for desktop client connections on port {PORT}")
    print("[*] Press Ctrl+C to exit.\n")

    client_addr = None
    seq = 0
    frame_id = 0
    last_frame_time = time.time()

    try:
        while True:
            # 1. Process incoming client packets (Inputs / Pings)
            try:
                data, addr = sock.recvfrom(1400)
                client_addr = addr

                if len(data) >= 8:
                    magic, ver, ptype, client_seq = struct.unpack(">HBB I", data[:8])
                    if magic == MAGIC:
                        if ptype == TYPE_INPUT_TOUCH and len(data) >= 20:
                            action, ptr_id, _, nx, ny, pressure = struct.unpack(">BB H HH f", data[8:20])
                            action_name = {0: "DOWN", 1: "UP", 2: "MOVE", 8: "SCROLL"}.get(action, str(action))
                            print(f"[Touch] Client {addr[0]} -> Action: {action_name} | Pos: ({nx}, {ny}) | Pressure: {pressure:.2f}")

                        elif ptype == TYPE_INPUT_KEY and len(data) >= 16:
                            action, _, keycode, meta = struct.unpack(">BB H I", data[8:16])
                            print(f"[Key] Client {addr[0]} -> Action: {action} | Keycode: {keycode}")

                        elif ptype == TYPE_HEARTBEAT_PING:
                            # Send immediate Pong
                            pong = struct.pack(">HBB I Q", MAGIC, 1, TYPE_HEARTBEAT_PONG, client_seq, time.time_ns())
                            sock.sendto(pong, client_addr)

            except BlockingIOError:
                pass

            # 2. Transmit simulated 60 FPS video stream chunks to active client
            now = time.time()
            if client_addr and (now - last_frame_time) >= (1.0 / 60.0):
                last_frame_time = now
                frame_id += 1

                # Generate 2 simulated chunks per frame
                total_chunks = 2
                for chunk_idx in range(total_chunks):
                    # Header: Magic (2B) + Ver (1B) + Type (1B) + Seq (4B)
                    header = struct.pack(">HBB I", MAGIC, 1, TYPE_VIDEO_CHUNK, seq)
                    seq += 1

                    # Payload header: FrameID (4B) + ChunkIdx (2B) + TotalChunks (2B) + Timestamp (8B)
                    payload_meta = struct.pack(">I HH Q", frame_id, chunk_idx, total_chunks, time.time_ns())

                    # Synthetic H.265 test payload slice (700 bytes)
                    dummy_payload = b"\x00\x00\x00\x01\x26" + b"\x42" * 695

                    packet = header + payload_meta + dummy_payload
                    sock.sendto(packet, client_addr)

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n[*] Stopping Mock Phone Daemon.")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
