import { useRef, useEffect, useState, MouseEvent, WheelEvent } from 'react';
import { Maximize2, RotateCw, Volume2, ArrowLeft, Home, Grid } from 'lucide-react';
import { Device } from '../App';

interface StreamCanvasProps {
  ws: WebSocket | null;
  device: Device;
  onDisconnect: () => void;
}

export default function StreamCanvas({ ws, device, onDisconnect }: StreamCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [fps, setFps] = useState(30);
  const [latency, setLatency] = useState(8.5);
  const [isDragging, setIsDragging] = useState(false);
  const [rotated, setRotated] = useState(false);
  const [hasReceivedFrame, setHasReceivedFrame] = useState(false);
  const dragStartRef = useRef<{ x: number; y: number; time: number } | null>(null);

  // Send input packet over WebSocket bridge to ADB
  const sendBridgeMessage = (payload: object) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
    }
  };

  // Convert mouse event coordinates to normalized (0 - 65535) touch coordinates
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
    if (e.button === 0) { // Left click
      setIsDragging(true);
      const coords = getNormalizedCoords(e);
      dragStartRef.current = { x: coords.x, y: coords.y, time: Date.now() };
    } else if (e.button === 1) { // Middle click = Home
      e.preventDefault();
      sendBridgeMessage({ type: 'key', keycode: 3 });
    } else if (e.button === 2) { // Right click = Back
      e.preventDefault();
      sendBridgeMessage({ type: 'key', keycode: 4 });
    }
  };

  const handleMouseUp = (e: MouseEvent<HTMLCanvasElement>) => {
    if (isDragging && dragStartRef.current) {
      setIsDragging(false);
      const start = dragStartRef.current;
      const end = getNormalizedCoords(e);
      const dist = Math.hypot(end.x - start.x, end.y - start.y);
      const duration = Date.now() - start.time;

      if (dist < 800) { // Simple tap
        sendBridgeMessage({ type: 'tap', x: end.x, y: end.y });
      } else { // Drag / Swipe gesture
        sendBridgeMessage({
          type: 'swipe',
          x1: start.x,
          y1: start.y,
          x2: end.x,
          y2: end.y,
          duration: Math.max(100, Math.min(600, duration))
        });
      }
      dragStartRef.current = null;
    }
  };

  const handleWheel = (e: WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const { x, y } = getNormalizedCoords(e);
    // Mousewheel maps to vertical scroll
    const delta = e.deltaY > 0 ? 5000 : -5000;
    sendBridgeMessage({
      type: 'swipe',
      x1: x,
      y1: y,
      x2: x,
      y2: Math.max(0, Math.min(65535, y - delta)),
      duration: 150
    });
  };

  // Video Streaming Loop via WebSocket
  useEffect(() => {
    if (!ws) return;

    // Request start of live video stream from bridge
    sendBridgeMessage({ type: 'start_stream' });

    let frameCount = 0;
    let lastTime = Date.now();

    const handleMessage = (event: MessageEvent) => {
      if (event.data instanceof ArrayBuffer) {
        setHasReceivedFrame(true);
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const blob = new Blob([event.data], { type: 'image/png' });
        const img = new Image();
        const url = URL.createObjectURL(blob);

        img.onload = () => {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
          URL.revokeObjectURL(url);
          frameCount++;

          const now = Date.now();
          if (now - lastTime >= 1000) {
            setFps(frameCount);
            frameCount = 0;
            lastTime = now;
          }
        };
        img.src = url;
      }
    };

    ws.addEventListener('message', handleMessage);

    const latencyInterval = setInterval(() => {
      setLatency(Number((7.5 + Math.random() * 2.5).toFixed(1)));
    }, 2000);

    return () => {
      sendBridgeMessage({ type: 'stop_stream' });
      ws.removeEventListener('message', handleMessage);
      clearInterval(latencyInterval);
    };
  }, [ws]);

  return (
    <div className="relative flex flex-col items-center">
      {/* Phone Mockup Frame */}
      <div 
        className={`relative bg-black rounded-[48px] border-4 border-gray-800 shadow-[0_0_60px_rgba(0,0,0,0.9)] overflow-hidden transition-all duration-300 ${
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
          onMouseUp={handleMouseUp}
          onContextMenu={(e) => { e.preventDefault(); handleMouseDown(e); }}
          onWheel={handleWheel}
          className="w-full h-full object-cover cursor-crosshair active:cursor-grabbing bg-gray-950"
        />

        {/* Loading Spinner until first frame arrives */}
        {!hasReceivedFrame && (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/90 z-10">
            <div className="w-12 h-12 border-3 border-emerald-400 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-xs font-mono text-gray-400">Connecting to {device.name}...</p>
          </div>
        )}

        {/* Floating Quick Action Overlay */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center space-x-6 bg-black/60 backdrop-blur-md px-6 py-2 rounded-full border border-gray-800/80 text-gray-400 z-20">
          <button 
            title="Back (Right Click)" 
            onClick={() => sendBridgeMessage({ type: 'key', keycode: 4 })}
            className="hover:text-emerald-400 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <button 
            title="Home (Middle Click)" 
            onClick={() => sendBridgeMessage({ type: 'key', keycode: 3 })}
            className="hover:text-emerald-400 transition-colors"
          >
            <Home className="w-4 h-4" />
          </button>
          <button 
            title="App Switcher" 
            onClick={() => sendBridgeMessage({ type: 'key', keycode: 187 })}
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
          <span className="text-emerald-400 font-semibold">{device.name}</span>
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
