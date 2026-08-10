import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Info, XCircle, X } from "lucide-react";
import { toastStore, type ToastMessage } from "../api/toast";

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    return toastStore.subscribe((newToasts) => {
      setToasts(newToasts);
    });
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "24px",
        right: "24px",
        zIndex: 9999,
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        maxWidth: "380px",
        width: "100%",
        pointerEvents: "none",
      }}
    >
      {toasts.map((t) => {
        const isError = t.type === "error";
        const isWarning = t.type === "warning";
        const isSuccess = t.type === "success";

        const bg = isError
          ? "#7f1d1d"
          : isWarning
          ? "#78350f"
          : isSuccess
          ? "#064e3b"
          : "#1e293b";

        const border = isError
          ? "#f87171"
          : isWarning
          ? "#fbbf24"
          : isSuccess
          ? "#34d399"
          : "#60a5fa";

        const Icon = isError
          ? XCircle
          : isWarning
          ? AlertTriangle
          : isSuccess
          ? CheckCircle2
          : Info;

        return (
          <div
            key={t.id}
            style={{
              pointerEvents: "auto",
              backgroundColor: bg,
              border: `1px solid ${border}`,
              borderRadius: "8px",
              padding: "12px 14px",
              color: "#f8fafc",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
              display: "flex",
              alignItems: "flex-start",
              gap: "10px",
              animation: "fadeIn 0.2s ease-in-out",
            }}
          >
            <Icon size={18} style={{ color: border, flexShrink: 0, marginTop: "2px" }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: "13px", fontWeight: 600, color: "#ffffff" }}>{t.title}</div>
              <div style={{ fontSize: "12px", color: "#e2e8f0", marginTop: "2px", lineHeight: 1.4, wordBreak: "break-word" }}>
                {t.message}
              </div>
            </div>
            <button
              onClick={() => toastStore.dismiss(t.id)}
              style={{
                background: "none",
                border: "none",
                color: "#94a3b8",
                cursor: "pointer",
                padding: 0,
                flexShrink: 0,
              }}
            >
              <X size={14} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
