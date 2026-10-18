package com.phantom.mirror.net;

import com.phantom.mirror.input.InputInjector;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetSocketAddress;
import java.net.SocketAddress;
import java.nio.ByteBuffer;

/**
 * UdpStreamer handles high-throughput video datagram fragmentation and
 * low-latency packet reception for input control signals.
 */
public class UdpStreamer {

    private static final int MAGIC_HEADER = 0x504D; // "PM"
    private static final int MAX_PACKET_SIZE = 1400; // Safe MTU size

    private final DatagramSocket socket;
    private final byte[] receiveBuffer = new byte[MAX_PACKET_SIZE];
    private SocketAddress connectedClient = null;
    private long sequenceNumber = 0;

    public UdpStreamer(int port) throws IOException {
        this.socket = new DatagramSocket(port);
        this.socket.setReceiveBufferSize(2 * 1024 * 1024); // 2MB rx buffer
        this.socket.setSendBufferSize(2 * 1024 * 1024);    // 2MB tx buffer
    }

    public synchronized void sendVideoChunk(long frameId, int chunkIndex, int totalChunks, byte[] chunkData) throws IOException {
        if (connectedClient == null) {
            return;
        }

        ByteBuffer buffer = ByteBuffer.allocate(MAX_PACKET_SIZE);
        // Header (8 bytes)
        buffer.putShort((short) MAGIC_HEADER);
        buffer.put((byte) 1);     // Version 1
        buffer.put((byte) 0x01);  // Type: Video Frame Chunk
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

        // Keep track of active client address for video streaming
        this.connectedClient = packet.getSocketAddress();

        ByteBuffer buffer = ByteBuffer.wrap(packet.getData(), 0, packet.getLength());
        if (buffer.remaining() < 8) return;

        int magic = buffer.getShort() & 0xFFFF;
        if (magic != MAGIC_HEADER) return;

        int version = buffer.get() & 0xFF;
        int packetType = buffer.get() & 0xFF;
        int seq = buffer.getInt();

        if (packetType == 0x10 && buffer.remaining() >= 12) {
            // Touch / Pointer Event
            int action = buffer.get() & 0xFF;
            int pointerId = buffer.get() & 0xFF;
            buffer.getShort(); // Reserved
            int normX = buffer.getShort() & 0xFFFF;
            int normY = buffer.getShort() & 0xFFFF;
            float pressure = buffer.getFloat();

            injector.injectTouchEvent(action, pointerId, normX, normY, pressure);
        }
    }

    public void close() {
        if (socket != null && !socket.isClosed()) {
            socket.close();
        }
    }
}
