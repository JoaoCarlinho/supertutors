import React, { useState, useRef, useEffect } from 'react';
import { Stage, Layer, Line } from 'react-konva';
import Konva from 'konva';

interface LineData {
  points: number[];
  stroke: string;
  strokeWidth: number;
  tool: 'pen' | 'eraser';
}

type Tool = 'pen' | 'eraser';

interface DrawingCanvasProps {
  onExport?: (dataUrl: string) => void;
}

export const DrawingCanvas: React.FC<DrawingCanvasProps> = ({ onExport }) => {
  const [lines, setLines] = useState<LineData[]>([]);
  const [isDrawing, setIsDrawing] = useState(false);
  const [tool, setTool] = useState<Tool>('pen');
  const [strokeWidth, setStrokeWidth] = useState(2);
  const [strokeColor, setStrokeColor] = useState('#000000');
  const stageRef = useRef<Konva.Stage>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const [stageSize, setStageSize] = useState({
    width: 800,
    height: 600,
  });

  // Responsive canvas sizing based on container
  useEffect(() => {
    const updateSize = () => {
      if (containerRef.current) {
        const containerWidth = containerRef.current.offsetWidth;
        const width = containerWidth; // Use full container width
        const height = Math.floor((width * 3) / 4); // Maintain 4:3 aspect ratio
        setStageSize({ width, height });
      }
    };

    // Initial size
    updateSize();

    // Update on window resize
    window.addEventListener('resize', updateSize);

    // Use ResizeObserver for container size changes
    const resizeObserver = new ResizeObserver(updateSize);
    if (containerRef.current) {
      resizeObserver.observe(containerRef.current);
    }

    return () => {
      window.removeEventListener('resize', updateSize);
      resizeObserver.disconnect();
    };
  }, []);

  const handleMouseDown = (e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => {
    setIsDrawing(true);
    const stage = e.target.getStage();
    if (!stage) return;

    const pos = stage.getPointerPosition();
    if (!pos) return;

    const newLine: LineData = {
      points: [pos.x, pos.y],
      stroke: tool === 'eraser' ? '#ffffff' : strokeColor,
      strokeWidth: tool === 'eraser' ? strokeWidth * 3 : strokeWidth,
      tool,
    };

    setLines([...lines, newLine]);
  };

  const handleMouseMove = (e: Konva.KonvaEventObject<MouseEvent | TouchEvent>) => {
    if (!isDrawing) return;

    const stage = e.target.getStage();
    if (!stage) return;

    const point = stage.getPointerPosition();
    if (!point) return;

    const lastLine = lines[lines.length - 1];
    if (!lastLine) return;

    const updatedLine = {
      ...lastLine,
      points: [...lastLine.points, point.x, point.y],
    };

    setLines([...lines.slice(0, -1), updatedLine]);
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleClear = () => {
    if (lines.length === 0) return;

    const userConfirmed = window.confirm('Clear canvas? This cannot be undone.');
    if (userConfirmed) {
      setLines([]);
    }
  };

  const handleExport = () => {
    if (!stageRef.current) {
      console.error('Canvas export failed: stageRef is null');
      return;
    }

    if (lines.length === 0) {
      alert('Canvas is empty. Please draw something first.');
      return;
    }

    console.log('Exporting canvas drawing...');
    const dataUrl = stageRef.current.toDataURL({
      pixelRatio: 2,
      mimeType: 'image/png',
    });

    console.log('Canvas exported to data URL, length:', dataUrl.length);

    if (onExport) {
      console.log('Calling onExport callback...');
      onExport(dataUrl);
    } else {
      console.warn('No onExport callback provided');
      alert('Export handler not configured. Please check console.');
    }
  };

  const handleUndo = () => {
    if (lines.length > 0) {
      setLines(lines.slice(0, -1));
    }
  };

  return (
    <div className="drawing-canvas-container" ref={containerRef}>
      {/* Toolbar */}
      <div className="toolbar flex items-center gap-2 mb-3 p-2 bg-gray-100 rounded flex-wrap">
        {/* Tool Selection */}
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => setTool('pen')}
            className={`px-3 py-2 rounded text-sm font-medium ${
              tool === 'pen'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            title="Pen Tool"
            aria-label="Pen tool"
          >
            ✏️ Pen
          </button>
          <button
            type="button"
            onClick={() => setTool('eraser')}
            className={`px-3 py-2 rounded text-sm font-medium ${
              tool === 'eraser'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            title="Eraser Tool"
            aria-label="Eraser tool"
          >
            🧹 Eraser
          </button>
        </div>

        <div className="w-px h-6 bg-gray-300" />

        {/* Color Picker */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-700">Color:</label>
          <input
            type="color"
            value={strokeColor}
            onChange={(e) => setStrokeColor(e.target.value)}
            className="w-10 h-10 rounded cursor-pointer"
            title="Stroke color"
          />
        </div>

        {/* Stroke Width */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-700">Width:</label>
          <input
            type="range"
            min="1"
            max="20"
            value={strokeWidth}
            onChange={(e) => setStrokeWidth(Number(e.target.value))}
            className="w-20"
            title="Stroke width"
          />
          <span className="text-sm text-gray-600 w-6">{strokeWidth}</span>
        </div>

        <div className="w-px h-6 bg-gray-300" />

        {/* Actions */}
        <button
          type="button"
          onClick={handleUndo}
          disabled={lines.length === 0}
          className="px-3 py-2 bg-white text-gray-700 rounded text-sm font-medium hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Undo last stroke"
          aria-label="Undo last stroke"
        >
          ↶ Undo
        </button>
        <button
          type="button"
          onClick={handleClear}
          disabled={lines.length === 0}
          className="px-3 py-2 bg-white text-red-600 rounded text-sm font-medium hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Clear canvas"
          aria-label="Clear canvas"
        >
          🗑️ Clear
        </button>
        <button
          type="button"
          onClick={handleExport}
          className="px-3 py-2 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700"
          title="Export drawing"
          aria-label="Export drawing"
        >
          💾 Export
        </button>
      </div>

      {/* Canvas */}
      <div className="canvas-wrapper border-2 border-gray-300 rounded overflow-hidden bg-white shadow-sm">
        <Stage
          ref={stageRef}
          width={stageSize.width}
          height={stageSize.height}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onTouchStart={handleMouseDown}
          onTouchMove={handleMouseMove}
          onTouchEnd={handleMouseUp}
          style={{ touchAction: 'none' }}
        >
          <Layer>
            {lines.map((line, i) => (
              <Line
                key={i}
                points={line.points}
                stroke={line.stroke}
                strokeWidth={line.strokeWidth}
                tension={0.5}
                lineCap="round"
                lineJoin="round"
                globalCompositeOperation={
                  line.tool === 'eraser' ? 'destination-out' : 'source-over'
                }
              />
            ))}
          </Layer>
        </Stage>
      </div>

      {/* Instructions */}
      <div className="mt-2 text-xs text-gray-500 text-center">
        Draw with your mouse or finger • Use eraser to remove strokes
      </div>
    </div>
  );
};
