import { useState } from "react";
import {
  Gavel,
  LockKeyhole,
  Mail,
  ArrowRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import apiClient from "../api/client";
import "../styles/login.css";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("mayank@example.com");
  const [password, setPassword] = useState("password123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(
    event: React.SubmitEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const response =
        await apiClient.post<LoginResponse>(
          "/auth/login",
          {
            email,
            password,
          },
        );

      localStorage.setItem(
        "access_token",
        response.data.access_token,
      );

      navigate("/");
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-background-glow" />

      <div className="login-card">
        <div className="login-brand">
          <div className="login-brand-mark">
            <Gavel size={22} strokeWidth={2} />
          </div>

          <div>
            <div className="login-brand-name">
              LexFlow
            </div>

            <div className="login-brand-subtitle">
              Legal Intelligence
            </div>
          </div>
        </div>

        <div className="login-heading">
          <h1>Welcome back.</h1>

          <p>
            Sign in to access your legal workspace.
          </p>
        </div>

        <form
          className="login-form"
          onSubmit={handleSubmit}
        >
          <div className="login-field">
            <label htmlFor="email">
              Email address
            </label>

            <div className="login-input-wrapper">
              <Mail size={17} />

              <input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                required
              />
            </div>
          </div>

          <div className="login-field">
            <label htmlFor="password">
              Password
            </label>

            <div className="login-input-wrapper">
              <LockKeyhole size={17} />

              <input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                required
              />
            </div>
          </div>

          {error && (
            <div className="login-error">
              {error}
            </div>
          )}

          <button
            className="login-submit"
            type="submit"
            disabled={loading}
          >
            <span>
              {loading
                ? "Signing in..."
                : "Sign in"}
            </span>

            {!loading && (
              <ArrowRight size={17} />
            )}
          </button>
        </form>

        <div className="login-security">
          <LockKeyhole size={14} />

          <span>
            Secure, encrypted legal workspace
          </span>
        </div>
      </div>
    </div>
  );
}

export default Login;