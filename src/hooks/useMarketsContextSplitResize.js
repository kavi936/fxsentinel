import { useCallback, useEffect, useRef, useState } from 'react';

const STORAGE_KEY = 'markets-context-split-left-ratio';
const DEFAULT_RATIO = 0.62;
const MIN_RATIO = 0.4;
const MAX_RATIO = 0.78;

function readStoredRatio() {
  try {
    const v = parseFloat(localStorage.getItem(STORAGE_KEY));
    if (!Number.isNaN(v) && v >= MIN_RATIO && v <= MAX_RATIO) return v;
  } catch {
    /* ignore */
  }
  return DEFAULT_RATIO;
}

/**
 * Draggable split between platform context and live news (Overview-style handle).
 */
export function useMarketsContextSplitResize({ enabled = true } = {}) {
  const containerRef = useRef(null);
  const [leftRatio, setLeftRatio] = useState(readStoredRatio);
  const [isDragging, setIsDragging] = useState(false);
  const leftRatioRef = useRef(leftRatio);
  const dragRef = useRef(null);
  const rafRef = useRef(null);

  leftRatioRef.current = leftRatio;

  const persistRatio = useCallback((ratio) => {
    const clamped = Math.max(MIN_RATIO, Math.min(MAX_RATIO, ratio));
    setLeftRatio(clamped);
    try {
      localStorage.setItem(STORAGE_KEY, String(clamped));
    } catch {
      /* ignore */
    }
  }, []);

  const endDrag = useCallback(() => {
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
    dragRef.current = null;
    setIsDragging(false);
    document.body.style.userSelect = '';
    document.body.style.cursor = '';
    document.removeEventListener('mousemove', onMouseMove);
    document.removeEventListener('mouseup', endDrag);
    document.removeEventListener('mouseleave', endDrag);
    document.removeEventListener('touchmove', onTouchMove);
    document.removeEventListener('touchend', endDrag);
    document.removeEventListener('touchcancel', endDrag);
    persistRatio(leftRatioRef.current);
  }, [persistRatio]);

  const applyMove = useCallback((clientX) => {
    if (!dragRef.current?.active || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const handleWidth = 20;
    const usable = rect.width - handleWidth;
    if (usable <= 0) return;
    const delta = (clientX - dragRef.current.startX) / usable;
    const next = dragRef.current.startRatio + delta;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => {
      setLeftRatio(Math.max(MIN_RATIO, Math.min(MAX_RATIO, next)));
    });
  }, []);

  const onMouseMove = useCallback(
    (e) => {
      applyMove(e.clientX);
    },
    [applyMove]
  );

  const onTouchMove = useCallback(
    (e) => {
      if (e.touches?.[0]) applyMove(e.touches[0].clientX);
    },
    [applyMove]
  );

  const onHandlePointerDown = useCallback(
    (e) => {
      if (!enabled) return;
      e.preventDefault();
      e.stopPropagation();
      const clientX = e.clientX ?? e.touches?.[0]?.clientX;
      if (clientX == null) return;

      dragRef.current = { active: true, startX: clientX, startRatio: leftRatioRef.current };
      setIsDragging(true);
      document.body.style.userSelect = 'none';
      document.body.style.cursor = 'col-resize';
      document.addEventListener('mousemove', onMouseMove);
      document.addEventListener('mouseup', endDrag);
      document.addEventListener('mouseleave', endDrag);
      document.addEventListener('touchmove', onTouchMove, { passive: false });
      document.addEventListener('touchend', endDrag);
      document.addEventListener('touchcancel', endDrag);
    },
    [enabled, onMouseMove, onTouchMove, endDrag]
  );

  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };
  }, []);

  return {
    containerRef,
    isDragging,
    onHandlePointerDown,
    leftWidthPercent: `${leftRatio * 100}%`,
  };
}
