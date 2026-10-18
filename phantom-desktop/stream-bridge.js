import { WebSocketServer } from 'ws';
import { exec, spawn } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const WS_PORT = 49153;

const wss = new WebSocketServer({ port: WS_PORT });
console.log(`[+] PhantomMirror Stream Bridge active on ws://localhost:${WS_PORT}`);

// Active device state
let activeDevice = null;
let isStreaming = false;

// Query connected ADB devices
async function getConnectedDevices() {
  try {
    const { stdout } = await execAsync('adb devices -l');
    const lines = stdout.trim().split('\n').slice(1);
    const devices = [];

    for (const line of lines) {
      const parts = line.trim().split(/\s+/);
      if (parts.length >= 2 && parts[1] === 'device') {
        const serial = parts[0];
        let model = 'Android Device';
        try {
          const { stdout: modelOut } = await execAsync(`adb -s ${serial} shell "getprop ro.product.brand; getprop ro.product.model"`);
          const [brand, mod] = modelOut.trim().split('\n');
          model = `${brand || ''} ${mod || ''}`.trim() || model;
        } catch (_) {}

        devices.push({
          name: model,
          serial: serial,
          ip: '127.0.0.1 (ADB Direct)',
          port: 49152,
          latency_ms: 8,
        });
      }
    }
    return devices;
  } catch (err) {
    return [];
  }
}

wss.on('connection', async (ws) => {
  console.log('[+] Client connected to Stream Bridge');

  // Send discovered devices immediately
  const devices = await getConnectedDevices();
  ws.send(JSON.stringify({ type: 'devices', devices }));

  let streamLoopActive = false;

  ws.on('message', async (data) => {
    try {
      const msg = JSON.parse(data.toString());

      if (msg.type === 'start_stream') {
        streamLoopActive = true;
        startScreenCapture(ws, () => streamLoopActive);
      } else if (msg.type === 'stop_stream') {
        streamLoopActive = false;
      } else if (msg.type === 'touch_down' || msg.type === 'tap') {
        // Map normalized (0 - 65535) to screen coordinates
        const { x, y } = msg;
        const screenX = Math.round((x / 65535) * 1272);
        const screenY = Math.round((y / 65535) * 2772);
        exec(`adb shell input tap ${screenX} ${screenY}`);
      } else if (msg.type === 'swipe') {
        const { x1, y1, x2, y2, duration = 200 } = msg;
        const sx1 = Math.round((x1 / 65535) * 1272);
        const sy1 = Math.round((y1 / 65535) * 2772);
        const sx2 = Math.round((x2 / 65535) * 1272);
        const sy2 = Math.round((y2 / 65535) * 2772);
        exec(`adb shell input swipe ${sx1} ${sy1} ${sx2} ${sy2} ${duration}`);
      } else if (msg.type === 'key') {
        // 4 = Back, 3 = Home, 187 = AppSwitch
        exec(`adb shell input keyevent ${msg.keycode}`);
      }
    } catch (_) {}
  });

  ws.on('close', () => {
    streamLoopActive = false;
    console.log('[-] Client disconnected from Stream Bridge');
  });
});

// Live high-speed screen capture loop
async function startScreenCapture(ws, isActive) {
  while (isActive() && ws.readyState === 1) {
    try {
      // Capture frame directly from device display pipeline
      const { stdout } = await execAsync('adb exec-out screencap -p', {
        encoding: 'buffer',
        maxBuffer: 10 * 1024 * 1024
      });

      if (isActive() && ws.readyState === 1) {
        ws.send(stdout);
      }
    } catch (err) {
      await new Promise((r) => setTimeout(r, 200));
    }
  }
}
