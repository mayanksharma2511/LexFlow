import { useEffect, useState, useRef } from "react";
import { Loader2, CheckCircle2, AlertCircle, X, Sparkles } from "lucide-react";
import "./ProgressOverlay.css";

export interface TaskProgressMessage {
  task_id: string;
  client_id: string;
  status: "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED";
  progress_percentage: number;
  current_step: string;
  details?: string | null;
  error?: string | null;
}

interface ProgressOverlayProps {
  clientId?: string;
}

export function ProgressOverlay({ clientId = "default_user" }: ProgressOverlayProps) {
  const [activeTask, setActiveTask] = useState<TaskProgressMessage | null>(null);
  const [visible, setVisible] = useState(false);
  const autoHideTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/tasks/${clientId}`;

    let socket: WebSocket | null = null;
    let isComponentMounted = true;

    function connectWebSocket() {
      if (!isComponentMounted) return;

      try {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
          reconnectAttemptsRef.current = 0;
        };

        socket.onmessage = (event) => {
          if (!isComponentMounted) return;
          try {
            const data: TaskProgressMessage = JSON.parse(event.data);
            if (data.task_id) {
              setActiveTask(data);
              setVisible(true);

              if (autoHideTimerRef.current) {
                clearTimeout(autoHideTimerRef.current);
                autoHideTimerRef.current = null;
              }

              if (data.status === "SUCCESS" || data.status === "FAILED") {
                autoHideTimerRef.current = setTimeout(() => {
                  if (isComponentMounted) {
                    setVisible(false);
                  }
                }, 5000);
              }
            }
          } catch {
            // Ignore non-JSON control messages
          }
        };

        socket.onclose = () => {
          if (!isComponentMounted) return;
          if (reconnectAttemptsRef.current < 5) {
            const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 16000);
            reconnectAttemptsRef.current += 1;
            reconnectTimerRef.current = setTimeout(connectWebSocket, delay);
          }
        };

        socket.onerror = () => {
          // Silent fallback for WebSocket errors
        };
      } catch {
        // Fallback for socket instantiation issues
      }
    }

    connectWebSocket();

    return () => {
      isComponentMounted = false;
      if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
        socket.close();
      }
      if (autoHideTimerRef.current) {
        clearTimeout(autoHideTimerRef.current);
      }
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
    };
  }, [clientId]);

  if (!visible || !activeTask) {
    return null;
  }

  const isFailed = activeTask.status === "FAILED";
  const isSuccess = activeTask.status === "SUCCESS";

  return (
    <div className={`progress-overlay-card ${isFailed ? "failed" : isSuccess ? "success" : "processing"}`}>
      <div className="progress-overlay-header">
        <div className="progress-overlay-title">
          {isSuccess ? (
            <CheckCircle2 size={18} className="text-emerald-400" />
          ) : isFailed ? (
            <AlertCircle size={18} className="text-rose-400" />
          ) : (
            <Loader2 size={18} className="animate-spin text-blue-400" />
          )}
          <span>
            {isSuccess
              ? "Task Complete"
              : isFailed
              ? "Processing Failed"
              : "Background AI Task"}
          </span>
        </div>

        <button
          className="progress-overlay-close"
          onClick={() => setVisible(false)}
          title="Dismiss"
          type="button"
        >
          <X size={14} />
        </button>
      </div>

      <div className="progress-overlay-body">
        <div className="progress-step-text">
          <Sparkles size={13} style={{ opacity: 0.8 }} />
          <span>{activeTask.current_step}</span>
        </div>

        {!isFailed && (
          <div className="progress-bar-container">
            <div
              className="progress-bar-fill"
              style={{ width: `${activeTask.progress_percentage}%` }}
            />
          </div>
        )}

        {isFailed && activeTask.error && (
          <div className="progress-error-text">{activeTask.error}</div>
        )}

        {isSuccess && activeTask.details && (
          <div className="progress-success-text">{activeTask.details}</div>
        )}
      </div>

      <div className="progress-overlay-footer">
        <span className="progress-percentage-label">
          {activeTask.progress_percentage}%
        </span>
        <span className="progress-status-pill">{activeTask.status}</span>
      </div>
    </div>
  );
}
