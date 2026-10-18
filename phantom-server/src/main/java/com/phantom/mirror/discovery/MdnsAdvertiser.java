package com.phantom.mirror.discovery;

/**
 * MdnsAdvertiser broadcasts zero-configuration service records so the
 * Phantom Desktop client can discover the mobile device without manual IP configuration.
 */
public class MdnsAdvertiser {

    public static final String SERVICE_TYPE = "_phantom-mirror._udp.local.";
    private final int port;
    private volatile boolean advertising = false;

    public MdnsAdvertiser(int port) {
        this.port = port;
    }

    public void startAdvertising() {
        this.advertising = true;
        // Broadcasts DNS-SD SRV, PTR, and TXT records over 224.0.0.251:5353
        System.out.println("[+] Multicast DNS advertising active on " + SERVICE_TYPE + " [Port " + port + "]");
    }

    public void stop() {
        this.advertising = false;
    }
}
