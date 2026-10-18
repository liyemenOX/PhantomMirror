import { useState } from 'react';
import { Smartphone, Wifi, Zap, Settings, Shield, RefreshCw, Power } from 'lucide-react';

interface Device {
  name: string;
  ip: string;
  port: number;
  latency_ms: number;
}

export default function App() {
  const [devices] = useState<Device[]>([
    { name: 'Android Device (mDNS)', ip: '192.168.1.105', port: 49152, latency_ms: 11 }
  ]);
  const [connected, setConnected] = useState(false);
  const [activeDevice, setActiveDevice] = useState<Device | null>(null);

  return (
    <div className="flex h-screen w-screen bg-[#0a0e14] text-gray-200 font-sans">
      {/* Sidebar Navigation */}
      <aside className="w-72 border-r border-gray-800/60 bg-[#0d121c]/80 backdrop-blur-xl p-5 flex flex-col justify-between">
        <div>
          {/* Brand Header */}
          <div className="flex items-center space-x-3 mb-8">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center">
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
              <RefreshCw className="w-3.5 h-3.5 hover:rotate-180 transition-transform cursor-pointer" />
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
                    ? 'bg-emerald-500/10 border-emerald-500/40 text-white'
                    : 'bg-gray-900/40 border-gray-800/80 hover:border-gray-700 text-gray-300'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <Smartphone className="w-4 h-4 text-emerald-400" />
                  <div>
                    <p className="text-sm font-medium">{dev.name}</p>
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
      <main className="flex-1 flex flex-col items-center justify-center p-6 relative">
        {connected ? (
          <div className="relative flex flex-col items-center">
            {/* Phone Frame Mockup */}
            <div className="w-[360px] h-[780px] bg-black rounded-[48px] border-4 border-gray-800/80 shadow-2xl overflow-hidden relative flex flex-col justify-between p-3">
              {/* Dynamic Island / Notch */}
              <div className="w-24 h-4 bg-gray-900 rounded-full mx-auto" />
              
              <div className="flex-1 flex items-center justify-center text-center p-6">
                <div>
                  <div className="w-16 h-16 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto mb-4 animate-pulse">
                    <Wifi className="w-8 h-8 text-emerald-400" />
                  </div>
                  <h3 className="text-white font-medium mb-1">Mirroring Active</h3>
                  <p className="text-xs text-gray-400 font-mono">1080x2400 @ 60 FPS • UDP Direct</p>
                </div>
              </div>

              {/* Home indicator bar */}
              <div className="w-32 h-1 bg-gray-700 rounded-full mx-auto mb-1" />
            </div>

            {/* Floating Control HUD */}
            <div className="mt-4 flex items-center space-x-3 bg-gray-900/80 backdrop-blur-md border border-gray-800 px-4 py-2 rounded-full text-xs font-mono text-gray-300">
              <span className="flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>LIVE</span>
              </span>
              <span>•</span>
              <span>Latency: 11.2ms</span>
              <span>•</span>
              <button 
                onClick={() => setConnected(false)}
                className="text-red-400 hover:text-red-300 flex items-center space-x-1"
              >
                <Power className="w-3 h-3" />
                <span>Disconnect</span>
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center max-w-sm">
            <div className="w-16 h-16 rounded-2xl bg-gray-900 border border-gray-800 flex items-center justify-center mx-auto mb-4">
              <Smartphone className="w-8 h-8 text-gray-600" />
            </div>
            <h2 className="text-lg font-medium text-white mb-2">No Active Stream</h2>
            <p className="text-sm text-gray-500 mb-6">
              Launch the Phantom server daemon on your phone. It will automatically appear in the sidebar via mDNS.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
