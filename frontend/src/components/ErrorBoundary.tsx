import { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, RefreshCw, ArrowLeft } from "lucide-react";

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
  fallbackMessage?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Uncaught Error Boundary catch:", error, errorInfo);
    this.setState({ errorInfo });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  private handleGoBack = () => {
    window.history.back();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            padding: "32px",
            margin: "24px",
            backgroundColor: "#1e293b",
            border: "1px solid #ef444433",
            borderRadius: "12px",
            color: "#f8fafc",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            textAlign: "center",
            gap: "16px",
            boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5)",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#ef4444",
            }}
          >
            <AlertTriangle size={24} />
          </div>

          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 600, margin: "0 0 6px 0", color: "#f8fafc" }}>
              {this.props.fallbackTitle || "Component Rendering Error"}
            </h2>
            <p style={{ fontSize: "14px", color: "#94a3b8", margin: 0, maxWidth: "500px" }}>
              {this.props.fallbackMessage ||
                "An unexpected rendering error occurred. The view has been isolated to prevent application disruption."}
            </p>
          </div>

          {this.state.error && (
            <div
              style={{
                width: "100%",
                maxWidth: "600px",
                textAlign: "left",
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: "8px",
                padding: "12px",
                fontSize: "12px",
                fontFamily: "monospace",
                color: "#fca5a5",
                overflowX: "auto",
                whiteSpace: "pre-wrap",
                maxHeight: "150px",
              }}
            >
              {this.state.error.toString()}
            </div>
          )}

          <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
            <button
              onClick={this.handleReset}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                backgroundColor: "#2563eb",
                color: "#ffffff",
                border: "none",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              <RefreshCw size={15} /> Retry Render
            </button>
            <button
              onClick={this.handleGoBack}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "8px",
                padding: "8px 16px",
                backgroundColor: "transparent",
                color: "#94a3b8",
                border: "1px solid #334155",
                borderRadius: "6px",
                fontSize: "13px",
                fontWeight: 500,
                cursor: "pointer",
              }}
            >
              <ArrowLeft size={15} /> Go Back
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
