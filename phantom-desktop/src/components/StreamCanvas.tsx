import { useRef, useEffect, useState, MouseEvent, WheelEvent } from 'react';
import { Maximize2, RotateCw, Volume2, ArrowLeft, Home, Grid } from 'lucide-react';

interface StreamCanvasProps {
  deviceIp: string;
  devicePort: number;
  onDisconnect: () => void;
}

export default function StreamCanvas({ onDisconnect }: StreamCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [fps, setFps] = useState(60);
  const [latency, setLatency] = useState(11.4);
  const [isDragging, setIsDragging] = useState(false);
  const [rotated, setRotated] = useState(false);

  // Send input packet to backend
  const sendInput = (action: number, normX: number, normY: number, pressure: number = 1.0) => {
    // If Tauri is available in runtime
    if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
      import('@tauri-apps/api/core').then(({ invoke }) => {
        invoke('send_input_event', { action, normX, normY, pressure }).catch(() => {});
      });
    }
  };

  // Convert client mouse coordinates to normalized (0 - 65535) touch coordinates
  const getNormalizedCoords = (e: MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));

    return {
      x: Math.round(x * 65535),
      y: Math.round(y * 65535),
    };
  };

  const handleMouseDown = (e: MouseEvent<HTMLCanvasElement>) => {
    if (e.button === 0) { // Left click = Tap
      setIsDragging(true);
      const { x, y } = getNormalizedCoords(e);
      sendInput(0, x, y); // ACTION_DOWN
    } else if (e.button === 1) { // Middle click = Home
      e.preventDefault();
      sendInput(5, 0, 0); // KEYCODE_HOME
    } else if (e.button === 2) { // Right click = Back
      e.preventDefault();
      sendInput(4, 0, 0); // KEYCODE_BACK
    }
  };

  const handleMouseMove = (e: MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return;
    const { x, y } = getNormalizedCoords(e);
    sendInput(2, x, y); // ACTION_MOVE
  };

  const handleMouseUp = (e: MouseEvent<HTMLCanvasElement>) => {
    if (isDragging) {
      setIsDragging(false);
      const { x, y } = getNormalizedCoords(e);
      sendInput(1, x, y); // ACTION_UP
    }
  };

  const handleWheel = (e: WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const { x, y } = getNormalizedCoords(e);
    // Delta Y maps to scroll gesture
    sendInput(8, x, y, e.deltaY); // ACTION_SCROLL
  };

  // Canvas visual test animation when running standalone in browser
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let frame = 0;

    const render = () => {
      frame++;
      ctx.fillStyle = '#0f172a';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Grid background
      ctx.strokeStyle = '#1e293b';
      ctx.lineWidth = 1;
      for (let x = 0; x < canvas.width; x += 40) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }
      for (let y = 0; y < canvas.height; y += 40) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }

      // Simulated phone screen elements
      ctx.fillStyle = '#00ff66';
      ctx.font = 'bold 24px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('⚡ PHANTOM MIRROR', canvas.width / 2, 280);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '14px monospace';
      ctx.fillText('Ultra Low-Latency H.265 / UDP Direct', canvas.width / 2, 320);

      // Simulated animated wave
      ctx.strokeStyle = '#00ff66';
      ctx.lineWidth = 3;
      ctx.beginPath();
      for (let x = 40; x < canvas.width - 40; x++) {
        const y = 460 + Math.sin((x + frame * 4) * 0.03) * 25;
        if (x === 40) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();

      // Bottom bar
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(60, canvas.height - 120, canvas.width - 120, 50);
      ctx.fillStyle = '#38bdf8';
      ctx.font = '13px monospace';
      ctx.fillText('READY • 1080x2400 @ 60fps', canvas.width / 2, canvas.height - 90);

      animId = requestAnimationFrame(render);
    };

    render();

    // RTT jitter simulation
    const interval = setInterval(() => {
      setLatency(Number((10.5 + Math.random() * 2.5).toFixed(1)));
      setFps(Math.round(59 + Math.random() * 2));
    }, 1500);

    return () => {
      cancelAnimationFrame(animId);
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="relative flex flex-col items-center">
      {/* Phone Mockup Frame */}
      <div 
        className={`relative bg-black rounded-[48px] border-4 border-gray-800 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden transition-all duration-300 ${
          rotated ? 'w-[780px] h-[360px]' : 'w-[360px] h-[780px]'
        }`}
      >
        {/* Dynamic Island */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 w-28 h-4 bg-gray-900/90 rounded-full z-20 flex items-center justify-between px-3">
          <div className="w-2 h-2 rounded-full bg-emerald-500/80 animate-pulse" />
          <div className="w-2.5 h-2.5 rounded-full bg-gray-800" />
        </div>

        {/* Video Canvas */}
        <canvas
          ref={canvasRef}
          width={1080}
          height={2400}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onContextMenu={(e) => { e.preventDefault(); handleMouseDown(e); }}
          onWheel={handleWheel}
          className="w-full h-full object-cover cursor-crosshair active:cursor-grabbing"
        />

        {/* Floating Quick Action Overlay */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center space-x-6 bg-black/60 backdrop-blur-md px-6 py-2 rounded-full border border-gray-800/80 text-gray-400 z-20">
          <button 
            title="Back (Right Click)" 
            onClick={() => sendInput(4, 0, 0)}
            className="hover:text-emerald-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button 
            title="Home (Middle Click)" 
            onClick={() => sendInput(5, 0, 0)}
            className="hover:text-emerald-400 transition-colors"
          >
            <Home className="w-4 h-4" />
          </button>
          <button 
            title="App Switcher" 
            onClick={() => sendInput(6, 0, 0)}
            className="hover:text-emerald-400 transition-colors"
          >
            <Grid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Floating Diagnostics & Controls Bar */}
      <div className="mt-4 flex items-center space-x-4 bg-gray-900/90 backdrop-blur-md border border-gray-800/80 px-5 py-2 rounded-full text-xs font-mono text-gray-300 shadow-lg">
        <span className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-emerald-400 font-semibold">LIVE</span>
        </span>
        <span className="text-gray-600">|</span>
        <span>Latency: <strong className="text-emerald-400">{latency} ms</strong></span>
        <span className="text-gray-600">|</span>
        <span>FPS: <strong className="text-white">{fps}</strong></span>
        <span className="text-gray-600">|</span>
        <div className="flex items-center space-x-2 text-gray-400">
          <button 
            onClick={() => setRotated(!rotated)}
            title="Rotate Screen" 
            className="p-1 hover:text-white transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
          </button>
          <button 
            title="Toggle Audio" 
            className="p-1 hover:text-white transition-colors"
          >
            <Volume2 className="w-3.5 h-3.5" />
          </button>
          <button 
            title="Fullscreen" 
            className="p-1 hover:text-white transition-colors"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
        </div>
        <span className="text-gray-600">|</span>
        <button 
          onClick={onDisconnect}
          className="text-red-400 hover:text-red-300 font-medium transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
}
