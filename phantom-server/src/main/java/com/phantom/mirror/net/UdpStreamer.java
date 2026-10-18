package com.phantom.mirror.net;

import com.phantom.mirror.capture.ScreenEncoder;
import com.phantom.mirror.input.InputInjector;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

/**
 * UdpStreamer handles high-throughput video datagram fragmentation and
 * low-latency packet reception for input control signals, PLI, and RTT pings.
 */
public class UdpStreamer {

    public static final int MAGIC_HEADER = 0x504D; // "PM"
    public static final int MAX_PACKET_SIZE = 1400; // MTU safe

    // Protocol Packet Types
    public static final int TYPE_VIDEO_CHUNK = 0x01;
    public static final int TYPE_VIDEO_CONFIG = 0x02;
    public static final int TYPE_PLI_REQUEST = 0x03;
    public static final int TYPE_INPUT_TOUCH = 0x10;
    public static final int TYPE_INPUT_KEY = 0x11;
    public static final int TYPE_CLIPBOARD = 0x12;
    public static final int TYPE_HEARTBEAT_PING = 0x20;
    public static final int TYPE_HEARTBEAT_PONG = 0x21;

    private final DatagramSocket socket;
    private final byte[] receiveBuffer = new byte[MAX_PACKET_SIZE];
    private SocketAddress connectedClient = null;
    private long sequenceNumber = 0;
    private ScreenEncoder screenEncoder = null;

    public UdpStreamer(int port) throws IOException {
        this.socket = new DatagramSocket(port);
        this.socket.setReceiveBufferSize(4 * 1024 * 1024); // 4MB rx buffer
        this.socket.setSendBufferSize(4 * 1024 * 1024);    // 4MB tx buffer
    }

    public void setScreenEncoder(ScreenEncoder encoder) {
        this.screenEncoder = encoder;
    }

    public synchronized void sendVideoChunk(long frameId, int chunkIndex, int totalChunks, byte[] chunkData) throws IOException {
        if (connectedClient == null) {
            return;
        }

        ByteBuffer buffer = ByteBuffer.allocate(MAX_PACKET_SIZE);
        // Header (8 bytes)
        buffer.putShort((short) MAGIC_HEADER);
        buffer.put((byte) 1);     // Version 1
        buffer.put((byte) TYPE_VIDEO_CHUNK);
        buffer.putInt((int) sequenceNumber++);

        // Payload Header
        buffer.putInt((int) frameId);
        buffer.putShort((short) chunkIndex);
        buffer.putShort((short) totalChunks);
        buffer.putLong(System.nanoTime()); // Presentation timestamp

        // NAL slice payload
        buffer.put(chunkData);

        DatagramPacket packet = new DatagramPacket(buffer.array(), buffer.position(), connectedClient);
        socket.send(packet);
    }

    public void processIncomingInput(InputInjector injector) throws IOException {
        DatagramPacket packet = new DatagramPacket(receiveBuffer, receiveBuffer.length);
        socket.receive(packet);

        // Track connected client endpoint
        this.connectedClient = packet.getSocketAddress();

        ByteBuffer buffer = ByteBuffer.wrap(packet.getData(), 0, packet.getLength());
        if (buffer.remaining() < 8) return;

        int magic = buffer.getShort() & 0xFFFF;
        if (magic != MAGIC_HEADER) return;

        int version = buffer.get() & 0xFF;
        int packetType = buffer.get() & 0xFF;
        int seq = buffer.getInt();

        switch (packetType) {
            case TYPE_INPUT_TOUCH:
                if (buffer.remaining() >= 12) {
                    int action = buffer.get() & 0xFF;
                    int pointerId = buffer.get() & 0xFF;
                    buffer.getShort(); // Reserved
                    int normX = buffer.getShort() & 0xFFFF;
                    int normY = buffer.getShort() & 0xFFFF;
                    float pressure = buffer.getFloat();
                    injector.injectTouchEvent(action, pointerId, normX, normY, pressure);
                }
                break;

            case TYPE_INPUT_KEY:
                if (buffer.remaining() >= 8) {
                    int keyAction = buffer.get() & 0xFF;
                    buffer.get(); // Reserved
                    int keyCode = buffer.getShort() & 0xFFFF;
                    int metaState = buffer.getInt();
                    injector.injectKeyEvent(keyAction, keyCode, metaState);
                }
                break;

            case TYPE_PLI_REQUEST:
                // Client requests immediate I-frame
                if (screenEncoder != null) {
                    screenEncoder.requestSyncFrame();
                }
                break;

            case TYPE_HEARTBEAT_PING:
                // Immediate Pong reply for precise RTT telemetry
                sendPong(seq);
                break;

            default:
                break;
        }
    }

    private void sendPong(int pingSeq) {
        try {
            if (connectedClient == null) return;
            ByteBuffer pong = ByteBuffer.allocate(16);
            pong.putShort((short) MAGIC_HEADER);
            pong.put((byte) 1);
            pong.put((byte) TYPE_HEARTBEAT_PONG);
            pong.putInt(pingSeq);
            pong.putLong(System.nanoTime());

            DatagramPacket packet = new DatagramPacket(pong.array(), pong.position(), connectedClient);
            socket.send(packet);
        } catch (IOException ignored) {}
    }

    public void close() {
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
    }
}
