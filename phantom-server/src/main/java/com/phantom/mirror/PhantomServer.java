package com.phantom.mirror;

import com.phantom.mirror.capture.ScreenEncoder;
import com.phantom.mirror.input.InputInjector;
import com.phantom.mirror.net.UdpStreamer;
import com.phantom.mirror.discovery.MdnsAdvertiser;

import java.io.IOException;

/**
 * Main entrypoint for PhantomMirror Android server daemon.
 * Executed via app_process:
 * CLASSPATH=/data/local/tmp/phantom-server.jar app_process / com.phantom.mirror.PhantomServer
 */
public class PhantomServer {

    private static final int DEFAULT_PORT = 49152;
    private static volatile boolean isRunning = true;

    public static void main(String[] args) {
        System.out.println("==================================================");
        System.out.println("[*] PhantomMirror Daemon v1.0.0 initializing...");
        System.out.println("[*] Mode: High-Performance Low-Latency UDP/H.265");
        System.out.println("==================================================");

        int port = DEFAULT_PORT;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException ignored) {}
        }

        try {
            // 1. Initialize Network Streamer
            UdpStreamer streamer = new UdpStreamer(port);
            System.out.println("[+] UDP Streamer listening on port " + port);

            // 2. Initialize Kernel/System Input Injector
            InputInjector inputInjector = new InputInjector();
            inputInjector.initialize();
            System.out.println("[+] Input Injector hooked into InputManager");

            // 3. Initialize Zero-Config mDNS Advertiser
            MdnsAdvertiser mdnsAdvertiser = new MdnsAdvertiser(port);
            mdnsAdvertiser.startAdvertising();
            System.out.println("[+] mDNS Service beacon active (_phantom-mirror._udp.local)");

            // 4. Initialize Hardware Video Encoder (MediaCodec H.265)
            ScreenEncoder screenEncoder = new ScreenEncoder(streamer);
            screenEncoder.start();
            System.out.println("[+] MediaCodec H.265 Hardware Encoder running (KEY_LATENCY=0)");

            // Setup input listener thread
            Thread inputThread = new Thread(() -> {
                while (isRunning) {
                    try {
                        streamer.processIncomingInput(inputInjector);
                    } catch (Exception e) {
                        if (isRunning) {
                            System.err.println("[-] Error processing input packet: " + e.getMessage());
                        }
                    }
                }
            }, "Phantom-Input-Worker");
            inputThread.start();

            // Register shutdown hook
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("[*] Shutting down PhantomMirror daemon...");
                isRunning = false;
                screenEncoder.stop();
                mdnsAdvertiser.stop();
                streamer.close();
            }));

            // Keep main daemon thread alive
            while (isRunning) {
                Thread.sleep(1000);
            }

        } catch (Exception e) {
            System.err.println("[-] Fatal daemon exception: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}
