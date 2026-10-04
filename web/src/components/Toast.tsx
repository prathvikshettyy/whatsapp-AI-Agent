import React, { createContext, useContext, useState } from "react";
import { cn } from "../lib/utils";

interface Toast {
  id: string;
  title: string;
  description?: string;
  variant?: "default" | "destructive" | "success" | "warning";
}

interface ToastContextType {
  toast: (options: Omit<Toast, "id">) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used within ToastProvider");
  return context;
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = ({ title, description, variant = "default" }: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, variant }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  };

  const remove = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            onClick={() => remove(t.id)}
            className={cn(
              "pointer-events-auto flex items-start justify-between rounded-lg p-4 shadow-lg border backdrop-blur-md transition-all animate-in slide-in-from-bottom-5 cursor-pointer",
              t.variant === "destructive" && "bg-destructive/95 text-destructive-foreground border-destructive",
              t.variant === "success" && "bg-emerald-800 text-white border-emerald-600",
              t.variant === "warning" && "bg-amber-800 text-white border-amber-600",
              (!t.variant || t.variant === "default") && "bg-card/95 text-card-foreground border-border"
            )}
          >
            <div>
              <h4 className="font-semibold text-sm">{t.title}</h4>
              {t.description && <p className="text-xs opacity-90 mt-1">{t.description}</p>}
            </div>
            <button className="text-xs opacity-60 hover:opacity-100 ml-3">✕</button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};
