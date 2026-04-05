"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Progressive typewriter hook.
 *
 * Call `pushText(newTarget)` whenever more text arrives from the SSE stream.
 * The hook will smoothly reveal characters towards the target at `speed`
 * characters per frame (~60 fps).
 *
 * Returns:
 * - `displayed`  — the currently visible text (always a prefix of `target`)
 * - `pushText`   — push a new target string (must include all previous text)
 * - `reset`      — clear everything for a new conversation turn
 * - `flush`      — immediately reveal all remaining text (returns full text)
 * - `isTyping`   — true while the animation is still catching up
 */
export function useTypewriter(speed: number = 3) {
  const [displayed, setDisplayed] = useState("");

  const targetRef = useRef("");   // full text received so far
  const indexRef = useRef(0);     // how far we've revealed
  const rafRef = useRef(0);       // requestAnimationFrame handle

  const animate = useCallback(() => {
    if (indexRef.current < targetRef.current.length) {
      // Reveal `speed` characters per frame
      const next = Math.min(indexRef.current + speed, targetRef.current.length);
      indexRef.current = next;
      setDisplayed(targetRef.current.slice(0, next));
      rafRef.current = requestAnimationFrame(animate);
    } else {
      rafRef.current = 0;
    }
  }, [speed]);

  const pushText = useCallback(
    (newTarget: string) => {
      targetRef.current = newTarget;
      // Start animation if not already running
      if (!rafRef.current && indexRef.current < targetRef.current.length) {
        rafRef.current = requestAnimationFrame(animate);
      }
    },
    [animate],
  );

  const reset = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = 0;
    targetRef.current = "";
    indexRef.current = 0;
    setDisplayed("");
  }, []);

  const flush = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = 0;
    const full = targetRef.current;
    indexRef.current = full.length;
    setDisplayed(full);
    return full;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const isTyping = indexRef.current < targetRef.current.length;

  return { displayed, pushText, reset, flush, isTyping } as const;
}

