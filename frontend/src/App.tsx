import { useState } from "react";
import {
  Activity,
  BarChart3,
  Bell,
  BriefcaseBusiness,
  ChevronDown,
  FileText,
  Gavel,
  LayoutDashboard,
  LogOut,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import {
  NavLink,
  Outlet,
  useNavigate,
} from "react-router-dom";

import "./App.css";
import { SettingsModal } from "./components/SettingsModal";
import { ProgressOverlay } from "./components/ProgressOverlay";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { ToastContainer } from "./components/ToastContainer";

const navigation = [
  {
    label: "Dashboard",
    path: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Cases",
    path: "/cases",
    icon: BriefcaseBusiness,
  },
  {
    label: "Documents",
    path: "/documents",
    icon: FileText,
  },
  {
    label: "AI Analysis",
    path: "/ai",
    icon: Sparkles,
  },
  {
    label: "Activity",
    path: "/activity",
    icon: Activity,
  },
  {
    label: "Analytics",
    path: "/analytics",
    icon: BarChart3,
  },
];

function App() {
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  function handleSignOut() {
    localStorage.removeItem("access_token");
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <ToastContainer />
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
      <ProgressOverlay clientId="default_user" />

      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <Gavel size={20} strokeWidth={2.2} />
          </div>

          <div>
            <div className="brand-name">LexFlow</div>
            <div className="brand-subtitle">Legal Intelligence</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Workspace</div>

          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `nav-item ${isActive ? "active" : ""}`
                }
              >
                <Icon size={18} strokeWidth={1.9} />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        <div className="sidebar-bottom">
          <div className="security-card">
            <ShieldCheck size={18} />

            <div>
              <div className="security-title">
                Secure Workspace
              </div>
              <div className="security-text">
                Your documents are protected.
              </div>
            </div>
          </div>

          <button
            className="sidebar-action"
            onClick={() => setShowSettings(true)}
          >
            <Settings size={17} />
            <span>Settings</span>
          </button>

          <button
            className="sidebar-action"
            onClick={handleSignOut}
          >
            <LogOut size={17} />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            <span>LexFlow</span>
            <span className="breadcrumb-separator">/</span>
            <strong>Workspace</strong>
          </div>

          <div className="topbar-actions" style={{ position: "relative" }}>
            <button className="icon-button" title="Search Cases" onClick={() => navigate("/cases")}>
              <Search size={17} />
            </button>

            <button
              className="icon-button notification-button"
              title="Notifications"
              onClick={() => {
                setShowProfileMenu(false);
                setShowNotifications(!showNotifications);
              }}
            >
              <Bell size={18} />
              <span className="notification-dot" />
            </button>

            {showNotifications && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: "120px",
                  marginTop: "8px",
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "12px",
                  width: "280px",
                  boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                  zIndex: 1000,
                }}
              >
                <div style={{ fontSize: "13px", fontWeight: 600, color: "#f8fafc", marginBottom: "8px", borderBottom: "1px solid #334155", paddingBottom: "6px" }}>
                  Workspace Notifications
                </div>
                <div style={{ display: "grid", gap: "8px" }}>
                  <div style={{ fontSize: "12px", color: "#cbd5e1", background: "rgba(37, 99, 235, 0.1)", padding: "8px", borderRadius: "4px" }}>
                    🔒 <strong>Security Policy:</strong> Row-level owner data isolation active.
                  </div>
                  <div style={{ fontSize: "12px", color: "#cbd5e1", background: "rgba(34, 197, 94, 0.1)", padding: "8px", borderRadius: "4px" }}>
                    ⚡ <strong>OCR Engine:</strong> PyMuPDF / Tesseract extraction online.
                  </div>
                </div>
              </div>
            )}

            <button
              className="profile-button"
              onClick={() => setShowProfileMenu(!showProfileMenu)}
            >
              <div className="avatar">M</div>

              <div className="profile-info">
                <span className="profile-name">Mayank</span>
                <span className="profile-role">Attorney</span>
              </div>

              <ChevronDown size={15} />
            </button>

            {showProfileMenu && (
              <div
                style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: "8px",
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                  padding: "8px",
                  width: "200px",
                  boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.5)",
                  zIndex: 1000,
                }}
              >
                <div
                  style={{
                    padding: "8px 12px",
                    borderBottom: "1px solid #334155",
                    marginBottom: "4px",
                  }}
                >
                  <div style={{ fontSize: "14px", fontWeight: 600, color: "#f8fafc" }}>
                    Mayank Sharma
                  </div>
                  <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                    mayank@example.com
                  </div>
                  <span
                    style={{
                      display: "inline-block",
                      marginTop: "6px",
                      padding: "2px 6px",
                      backgroundColor: "rgba(37, 99, 235, 0.2)",
                      color: "#60a5fa",
                      borderRadius: "4px",
                      fontSize: "11px",
                      fontWeight: 600,
                    }}
                  >
                    LEAD COUNSEL
                  </span>
                </div>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    setShowSettings(true);
                  }}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "8px 12px",
                    background: "none",
                    border: "none",
                    color: "#cbd5e1",
                    fontSize: "13px",
                    cursor: "pointer",
                    borderRadius: "4px",
                    textAlign: "left",
                  }}
                >
                  <Settings size={15} /> Settings
                </button>

                <button
                  onClick={() => {
                    setShowProfileMenu(false);
                    handleSignOut();
                  }}
                  style={{
                    width: "100%",
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                    padding: "8px 12px",
                    background: "none",
                    border: "none",
                    color: "#ef4444",
                    fontSize: "13px",
                    cursor: "pointer",
                    borderRadius: "4px",
                    textAlign: "left",
                  }}
                >
                  <LogOut size={15} /> Sign Out
                </button>
              </div>
            )}
          </div>
        </header>

        <section className="page-content">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </section>
      </main>
    </div>
  );
}

export default App;