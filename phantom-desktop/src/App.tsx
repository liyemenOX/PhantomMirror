import { useState } from 'react';
import { Smartphone, Zap, Settings, Shield, RefreshCw } from 'lucide-react';
import StreamCanvas from './components/StreamCanvas';

interface Device {
  name: string;
  ip: string;
  port: number;
  latency_ms: number;
}

export default function App() {
  const [devices] = useState<Device[]>([
    { name: 'Pixel 8 Pro (Phantom-01)', ip: '192.168.1.105', port: 49152, latency_ms: 11 },
    { name: 'Samsung Galaxy S24 (Phantom-02)', ip: '192.168.1.120', port: 49152, latency_ms: 14 }
  ]);
  const [connected, setConnected] = useState(false);
  const [activeDevice, setActiveDevice] = useState<Device | null>(null);

  return (
    <div className="flex h-screen w-screen bg-[#0a0e14] text-gray-200 font-sans select-none overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-80 border-r border-gray-800/60 bg-[#0d121c]/80 backdrop-blur-xl p-5 flex flex-col justify-between z-10">
        <div>
          {/* Brand Header */}
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shadow-[0_0_15px_rgba(0,255,102,0.15)]">
              <Zap className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="font-semibold text-white tracking-wide">PhantomMirror</h1>
              <p className="text-xs text-emerald-400/80 font-mono">v1.0.0 • Ultra-Low Latency</p>
            </div>
          </div>

          {/* Device Discovery Panel */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-gray-400 font-medium uppercase tracking-wider">
              <span>Discovered Devices</span>
              <RefreshCw className="w-3.5 h-3.5 hover:rotate-180 transition-transform cursor-pointer text-gray-500 hover:text-white" />
            </div>

            {devices.map((dev, idx) => (
              <div
                key={idx}
                onClick={() => {
                  setActiveDevice(dev);
                  setConnected(true);
                }}
                className={`p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  connected && activeDevice?.ip === dev.ip
                    ? 'bg-emerald-500/10 border-emerald-500/40 text-white shadow-[0_0_20px_rgba(0,255,102,0.1)]'
                    : 'bg-gray-900/40 border-gray-800/80 hover:border-gray-700 text-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 rounded-lg bg-gray-800/50">
                    <Smartphone className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{dev.name}</p>
                    <p className="text-xs text-gray-500 font-mono">{dev.ip}</p>
                  </div>
                </div>
                <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5 rounded-full">
                  {dev.latency_ms}ms
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Status / Quick Action */}
        <div className="pt-4 border-t border-gray-800/60 text-xs text-gray-500 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <span>H.265 / HEVC Direct</span>
          </div>
          <Settings className="w-4 h-4 hover:text-white cursor-pointer transition-colors" />
        </div>
      </aside>

      {/* Main Streaming Viewport */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative bg-gradient-to-br from-[#0a0e14] via-[#0d121c] to-[#070a0e]">
        {connected && activeDevice ? (
          <StreamCanvas 
            deviceIp={activeDevice.ip} 
            devicePort={activeDevice.port}
            onDisconnect={() => setConnected(false)}
          />
        ) : (
          <div className="text-center max-w-sm">
            <div className="w-16 h-16 rounded-2xl bg-gray-900/80 border border-gray-800 flex items-center justify-center mx-auto mb-4 shadow-xl">
              <Smartphone className="w-8 h-8 text-gray-500" />
            </div>
            <h2 className="text-lg font-medium text-white mb-2">Select a Device to Mirror</h2>
            <p className="text-sm text-gray-400 mb-6 leading-relaxed">
              Launch the Phantom server daemon on your phone. It will automatically advertise over mDNS and appear in the sidebar.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
