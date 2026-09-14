import { useState, type SubmitEvent} from "react";

import { login } from "../api/auth";

interface LoginFormProps {
    onLogin: (token: string) => void;
}

export default function LoginForm({
    onLogin,
}: LoginFormProps) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>
    ) {
        event.preventDefault();

        if (!username.trim() || !password) {
            return;
          }

        setError("");
        setLoading(true);

        try {
            const result = await login(
                username,
                password
            );

            sessionStorage.setItem(
                "access_token",
                result.access_token
            );

            onLogin(result.access_token);
        } catch (err) {
          const message = err instanceof Error? err.message: "Login failed";
          setError(message);
            // setError("Invalid username or password");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="login-page">
          <div className="login-card">
            <div className="login-heading">
              <h1>Personal RAG Chatbot</h1>
    
              <p>
                Sign in to chat with your documents.
              </p>
            </div>
    
            <form
              className="login-form"
              onSubmit={handleSubmit}
            >
              <div className="form-group">
                <label htmlFor="username">
                  Username
                </label>
    
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  placeholder="Enter your username"
                  autoComplete="username"
                  disabled={loading}
                />
              </div>
    
              <div className="form-group">
                <label htmlFor="password">
                  Password
                </label>
    
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  disabled={loading}
                />
              </div>
    
              {error && (
                <p className="login-error">
                  {error}
                </p>
              )}
    
              <button
                className="login-button"
                type="submit"
                disabled={
                  loading ||
                  !username.trim() ||
                  !password
                }
              >
                {loading
                  ? "Signing in..."
                  : "Sign in"}
              </button>
            </form>
          </div>
        </div>
      );
}