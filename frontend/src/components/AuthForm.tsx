"use client";
import { useState } from "react";

interface Props {
  mode: "login" | "register";
  onSubmit: (data: Record<string, string>) => Promise<void>;
}

export default function AuthForm({ mode, onSubmit }: Props) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [customerCode, setCustomerCode] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onSubmit({ email, password, displayName, customerCode, authToken });
    } catch (err: any) {
      setError(err.message || "Operation failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 w-full max-w-md">
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Email</label>
        <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)}
          className="input-field" placeholder="you@example.com" />
      </div>
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Password</label>
        <input type="password" required minLength={6} value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="input-field" placeholder="••••••••" />
      </div>
      {mode === "register" && (
        <>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Display Name</label>
            <input type="text" value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="input-field" placeholder="Your name" />
          </div>
          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-100" /></div>
            <div className="relative flex justify-center">
              <span className="px-3 text-[10px] text-gray-400 bg-white uppercase tracking-widest">API Credentials</span>
            </div>
          </div>
          <p className="text-xs text-gray-400 -mt-1">Required for real API access, optional for mock mode.</p>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Customer Code</label>
            <input type="text" value={customerCode}
              onChange={(e) => setCustomerCode(e.target.value)}
              className="input-field font-mono" placeholder="e.g. CUS001" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Auth Token</label>
            <input type="text" value={authToken}
              onChange={(e) => setAuthToken(e.target.value)}
              className="input-field font-mono" placeholder="API authorization token" />
          </div>
        </>
      )}
      {error && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-red-50 border border-red-200/70 text-red-600 text-sm animate-slide-up">
          <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      )}
      <button type="submit" disabled={loading}
        className="w-full py-3 btn-primary text-sm">
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Processing...
          </span>
        ) : mode === "login" ? "Sign In" : "Create Account"}
      </button>
    </form>
  );
}
