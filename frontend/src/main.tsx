import React from "react";
import ReactDOM from "react-dom/client";
import {
  BrowserRouter,
  Route,
  Routes,
} from "react-router-dom";

import App from "./App";
import Dashboard from "./pages/Dashboard";
import Activity from "./pages/Activity";
import Login from "./pages/Login";
import Cases from "./pages/Cases";
import CaseDetails from "./pages/CaseDetails";
import DocumentDetails from "./pages/DocumentDetails";
import Documents from "./pages/Documents";
import AIAnalysis from "./pages/AIAnalysis";
import AnalyticsDashboard from "./pages/AnalyticsDashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import { ErrorBoundary } from "./components/ErrorBoundary";

import "./index.css";

ReactDOM.createRoot(
  document.getElementById("root")!,
).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>

        {/* Public route */}
        <Route
          path="/login"
          element={<ErrorBoundary><Login /></ErrorBoundary>}
        />

        {/* Protected Application routes */}
        <Route element={<ProtectedRoute />}>
          <Route element={<App />}>

            <Route
              path="/"
              element={<ErrorBoundary fallbackTitle="Dashboard Error"><Dashboard /></ErrorBoundary>}
            />

            <Route
              path="/cases"
              element={<ErrorBoundary fallbackTitle="Cases Error"><Cases /></ErrorBoundary>}
            />

            <Route
              path="/cases/:caseId"
              element={<ErrorBoundary fallbackTitle="Case Details Error"><CaseDetails /></ErrorBoundary>}
            />

            <Route
              path="/documents"
              element={<ErrorBoundary fallbackTitle="Documents Error"><Documents /></ErrorBoundary>}
            />

            <Route
              path="/documents/:documentId"
              element={<ErrorBoundary fallbackTitle="Document Viewer Error"><DocumentDetails /></ErrorBoundary>}
            />

            <Route
              path="/ai"
              element={<ErrorBoundary fallbackTitle="AI Analysis Error"><AIAnalysis /></ErrorBoundary>}
            />
        
            <Route
              path="/activity"
              element={<ErrorBoundary fallbackTitle="Activity Log Error"><Activity /></ErrorBoundary>}
            />

            <Route
              path="/analytics"
              element={<ErrorBoundary fallbackTitle="Analytics Dashboard Error"><AnalyticsDashboard /></ErrorBoundary>}
            />

          </Route>
        </Route>

      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);