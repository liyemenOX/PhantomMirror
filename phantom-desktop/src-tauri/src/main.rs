// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::UdpSocket;
use std::sync::{Arc, Mutex};
use tauri::State;

struct AppState {
    socket: Arc<Mutex<Option<UdpSocket>>>,
}

#[derive(serde::Serialize)]
struct DeviceInfo {
    name: String,
    ip: String,
    port: u16,
    latency_ms: u32,
}

#[tauri::command]
async fn scan_devices() -> Result<Vec<DeviceInfo>, String> {
    // In production, listens for mDNS _phantom-mirror._udp.local beacons
    Ok(vec![
        DeviceInfo {
            name: "Pixel 8 Pro (Phantom-01)".into(),
            ip: "192.168.1.105".into(),
            port: 49152,
            latency_ms: 12,
        }
    ])
}

#[tauri::command]
async fn connect_device(ip: String, port: u16, state: State<'_, AppState>) -> Result<String, String> {
    let socket = UdpSocket::bind("0.0.0.0:0").map_err(|e| e.to_string())?;
    socket.connect(format!("{}:{}", ip, port)).map_err(|e| e.to_string())?;

    // Send connection handshake ping
    let ping = [0x50, 0x4D, 0x01, 0x20, 0x00, 0x00, 0x00, 0x01];
    socket.send(&ping).map_err(|e| e.to_string())?;

    let mut sock_guard = state.socket.lock().unwrap();
    *sock_guard = Some(socket);

    Ok(format!("Connected to {}:{}", ip, port))
}

#[tauri::command]
fn send_input_event(action: u8, norm_x: u16, norm_y: u16, state: State<'_, AppState>) -> Result<(), String> {
    let sock_guard = state.socket.lock().unwrap();
    if let Some(ref socket) = *sock_guard {
        let mut packet = vec![
            0x50, 0x4D, 0x01, 0x10, // Magic + Version + Type (0x10 Input)
            0x00, 0x00, 0x00, 0x00, // Seq
            action, 0x00, 0x00, 0x00,
        ];
        packet.extend_from_slice(&norm_x.to_be_bytes());
        packet.extend_from_slice(&norm_y.to_be_bytes());
        packet.extend_from_slice(&[0x00, 0x00, 0x80, 0x3F]); // Pressure 1.0f

        let _ = socket.send(&packet);
    }
    Ok(())
}

fn main() {
    let state = AppState {
        socket: Arc::new(Mutex::new(None)),
    };

    tauri::Builder::default()
        .manage(state)
        .invoke_handler(tauri::generate_handler![
            scan_devices,
            connect_device,
            send_input_event
        ])
        .run(tauri::generate_context!())
        .expect("error while running PhantomMirror desktop client");
}
