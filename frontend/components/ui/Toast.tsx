'use client';
import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';
import { cn, FOCUS_RING } from '@/lib/utils';

export type ToastTone = 'default' | 'success' | 'error' | 'warning';

interface ToastItem {
  id: number;
  tone: ToastTone;
  message: string;
  action?: { label: string; onClick: () => void };
}
export interface ToastInput {
  tone?: ToastTone;
  message: string;
  duration?: number;
  action?: ToastItem['action'];
}

interface ToastApi {
  toast: (t: ToastInput) => number;
  dismiss: (id: number) => void;
}

const ToastCtx = createContext<ToastApi | null>(null);

export function useToast(): ToastApi {
  const ctx = useContext(ToastCtx);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
}

const TONE: Record<ToastTone, { icon: typeof Info; border: string; iconCls: string }> = {
  default: { icon: Info, border: 'border-idbi-teal', iconCls: 'text-idbi-teal' },
  success: { icon: CheckCircle2, border: 'border-idbi-green', iconCls: 'text-idbi-green' },
  error: { icon: AlertCircle, border: 'border-red-500', iconCls: 'text-red-500' },
  warning: { icon: AlertTriangle, border: 'border-idbi-orange', iconCls: 'text-idbi-orange' },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const [mounted, setMounted] = useState(false);
  const idRef = useRef(0);
  const timers = useRef<Record<number, ReturnType<typeof setTimeout>>>({});

  useEffect(() => setMounted(true), []);

  const dismiss = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id));
    const tm = timers.current[id];
    if (tm) {
      clearTimeout(tm);
      delete timers.current[id];
    }
  }, []);

  const toast = useCallback(
    ({ tone = 'default', message, duration = 4500, action }: ToastInput) => {
      const id = ++idRef.current;
      setItems((prev) => [...prev, { id, tone, message, action }]);
      if (duration > 0) timers.current[id] = setTimeout(() => dismiss(id), duration);
      return id;
    },
    [dismiss],
  );

  return (
    <ToastCtx.Provider value={{ toast, dismiss }}>
      {children}
      {mounted &&
        createPortal(
          <div className="fixed top-4 right-4 z-[60] flex flex-col gap-2 w-[calc(100vw-2rem)] max-w-sm pointer-events-none">
            <AnimatePresence>
              {items.map((t) => {
                const cfg = TONE[t.tone];
                const Icon = cfg.icon;
                return (
                  <motion.div
                    key={t.id}
                    layout
                    initial={{ opacity: 0, y: -12, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 24 }}
                    transition={{ duration: 0.25, ease: 'easeOut' }}
                    className={cn(
                      'pointer-events-auto flex items-start gap-3 bg-white border-l-4 rounded-field shadow-pop px-4 py-3',
                      cfg.border,
                    )}
                    role={t.tone === 'error' ? 'alert' : 'status'}
                  >
                    <Icon size={18} className={cn('mt-0.5 shrink-0', cfg.iconCls)} />
                    <p className="flex-1 text-sm text-idbi-slate">{t.message}</p>
                    {t.action && (
                      <button
                        type="button"
                        onClick={() => {
                          t.action!.onClick();
                          dismiss(t.id);
                        }}
                        className={cn('text-xs font-bold text-idbi-green hover:underline', FOCUS_RING)}
                      >
                        {t.action.label}
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => dismiss(t.id)}
                      aria-label="Dismiss"
                      className={cn('text-idbi-faint hover:text-idbi-ink', FOCUS_RING)}
                    >
                      <X size={15} />
                    </button>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>,
          document.body,
        )}
    </ToastCtx.Provider>
  );
}
