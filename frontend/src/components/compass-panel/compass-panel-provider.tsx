"use client";

import { usePathname } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useAuth } from "@/features/auth";
import { CompassPanel } from "./compass-panel";
import { availableCompassScopes } from "./compass-scope";

interface CompassPanelContextValue {
  /** False when Compass has nothing it can answer for this user on this page. */
  canAsk: boolean;
  open: () => void;
  shortcutLabel: string;
}

const CompassPanelContext = createContext<CompassPanelContextValue | null>(null);

/**
 * Owns the global "Ask Compass" panel: the open/closed state, the
 * Cmd/Ctrl+K shortcut, and which scopes apply on the current page.
 * Mounted once in the protected layout, so the panel is reachable
 * from anywhere in the app shell — and from nowhere else, because a
 * public or login page has no signed-in user to ask on behalf of.
 */
export function CompassPanelProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth();
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [shortcutLabel, setShortcutLabel] = useState("Ctrl K");

  const scopes = useMemo(
    () => (user ? availableCompassScopes(user, pathname) : []),
    [user, pathname],
  );
  const canAsk = scopes.length > 0;

  // Decided after mount, not during render: the server can't know the
  // visitor's platform, and guessing there would mismatch on hydration.
  useEffect(() => {
    if (/Mac|iPhone|iPad/.test(navigator.userAgent)) setShortcutLabel("⌘K");
  }, []);

  useEffect(() => {
    if (!canAsk) return;
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setIsOpen((open) => !open);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [canAsk]);

  // Navigating somewhere (or losing the right to ask) closes the panel,
  // so it never lingers over a page it no longer matches.
  useEffect(() => {
    setIsOpen(false);
  }, [pathname, canAsk]);

  const open = useCallback(() => setIsOpen(true), []);
  const close = useCallback(() => setIsOpen(false), []);
  const value = useMemo(() => ({ canAsk, open, shortcutLabel }), [canAsk, open, shortcutLabel]);

  return (
    <CompassPanelContext.Provider value={value}>
      {children}
      {canAsk && <CompassPanel isOpen={isOpen} onClose={close} scopes={scopes} />}
    </CompassPanelContext.Provider>
  );
}

export function useCompassPanel(): CompassPanelContextValue {
  const ctx = useContext(CompassPanelContext);
  if (!ctx) throw new Error("useCompassPanel must be used inside <CompassPanelProvider>.");
  return ctx;
}
