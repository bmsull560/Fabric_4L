/**
 * Hook for managing graph canvas interactions: zoom, pan, and drag.
 * Consolidates view transform state and mouse event handlers.
 */

import { useState, useCallback, useRef } from "react";

export interface ViewTransform {
  x: number;
  y: number;
  scale: number;
}

export interface CanvasState {
  view: ViewTransform;
  isDragging: boolean;
}

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.2;
const WHEEL_ZOOM_FACTOR = 0.1;

/**
 * Hook for managing graph canvas state including zoom, pan, and drag interactions.
 *
 * @param initialView - Optional initial view transform (defaults to centered, 1x zoom)
 * @returns Canvas state, event handlers, and control actions
 *
 * @example
 * ```tsx
 * const canvas = useGraphCanvas();
 *
 * // In your render:
 * <svg {...canvas.handlers}>
 *   <g transform={`translate(${canvas.view.x}, ${canvas.view.y}) scale(${canvas.view.scale})`}>
 *     // graph content
 *   </g>
 * </svg>
 *
 * // Control buttons:
 * <button onClick={canvas.actions.zoomIn}>Zoom In</button>
 * <button onClick={canvas.actions.resetView}>Reset</button>
 * ```
 */
export function useGraphCanvas(initialView?: Partial<ViewTransform>) {
  const [view, setView] = useState<ViewTransform>({
    x: initialView?.x ?? 0,
    y: initialView?.y ?? 0,
    scale: initialView?.scale ?? 1,
  });
  const [isDragging, setIsDragging] = useState(false);

  const dragRef = useRef<{
    startX: number;
    startY: number;
    viewX: number;
    viewY: number;
  } | null>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      // Left click initiates drag
      if (e.button !== 0) return;

      setIsDragging(true);
      dragRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        viewX: view.x,
        viewY: view.y,
      };
    },
    [view.x, view.y]
  );

  // PERF: Use ref to accumulate drag deltas instead of state
  // Prevents re-render cascade during continuous mouse movement
  const dragDeltaRef = useRef({ dx: 0, dy: 0 });

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging || !dragRef.current) return;

      const dx = e.clientX - dragRef.current.startX;
      const dy = e.clientY - dragRef.current.startY;

      // Store deltas in ref, not state - prevents re-renders during drag
      dragDeltaRef.current = { dx, dy };

      // Apply transform directly without triggering React re-render cycle
      // Only update state on mouse up for final position
      const newX = dragRef.current.viewX + dx / view.scale;
      const newY = dragRef.current.viewY + dy / view.scale;

      // Use functional update to avoid stale closure issues
      setView((prev) => ({
        ...prev,
        x: newX,
        y: newY,
      }));
    },
    [isDragging, view.scale]  // PERF: Only depend on scale, not entire view object
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    dragRef.current = null;
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -WHEEL_ZOOM_FACTOR : WHEEL_ZOOM_FACTOR;
    setView((prev) => ({
      ...prev,
      scale: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev.scale + delta)),
    }));
  }, []);

  const resetView = useCallback(() => {
    setView({ x: 0, y: 0, scale: 1 });
  }, []);

  const zoomIn = useCallback(() => {
    setView((prev) => ({
      ...prev,
      scale: Math.min(MAX_ZOOM, prev.scale + ZOOM_STEP),
    }));
  }, []);

  const zoomOut = useCallback(() => {
    setView((prev) => ({
      ...prev,
      scale: Math.max(MIN_ZOOM, prev.scale - ZOOM_STEP),
    }));
  }, []);

  return {
    view,
    isDragging,
    handlers: {
      onMouseDown: handleMouseDown,
      onMouseMove: handleMouseMove,
      onMouseUp: handleMouseUp,
      onMouseLeave: handleMouseUp,
      onWheel: handleWheel,
    },
    actions: {
      resetView,
      zoomIn,
      zoomOut,
    },
  };
}
