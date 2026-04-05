"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthForm from "@/components/AuthForm";
import { login, mockLogin } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoError, setDemoError] = useState("");

  const handleLogin = async (data: Record<string, string>) => {
    const res = await login(data.email, data.password);
    setToken(res.access_token);
    router.push("/chat");
  };

  const handleDemoLogin = async () => {
    setDemoLoading(true);
    setDemoError("");
    try {
      const res = await mockLogin();
      setToken(res.access_token);
      router.push("/chat");
    } catch (err: any) {
      setDemoError(err.message || "Demo login failed");
    } finally {
      setDemoLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-400/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-400/10 rounded-full blur-3xl" />
      </div>

      <div className="card w-full max-w-md overflow-hidden animate-fade-in">
        <div className="bg-gradient-to-br from-blue-600 via-blue-600 to-indigo-700 px-8 py-10 text-white relative overflow-hidden">
          {/* Background pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-4 right-4 w-24 h-24 border-2 border-white rounded-2xl rotate-12" />
            <div className="absolute bottom-4 left-4 w-16 h-16 border-2 border-white rounded-xl -rotate-12" />
          </div>
          <div className="relative">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 18.75a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h6m-9 0H3.375a1.125 1.125 0 01-1.125-1.125V14.25m17.25 4.5a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m3 0h1.125c.621 0 1.129-.504 1.09-1.124a17.902 17.902 0 00-3.213-9.193 2.056 2.056 0 00-1.58-.86H14.25M16.5 18.75h-2.25m0-11.177v-.958c0-.568-.422-1.048-.987-1.106a48.554 48.554 0 00-10.026 0 1.106 1.106 0 00-.987 1.106v7.635m12-6.677v6.677m0 4.5v-4.5m0 0h-12" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">Logistics AI</h1>
                <p className="text-blue-200 text-xs">Intelligent Shipping Agent</p>
              </div>
            </div>
            <p className="text-sm text-blue-100 mt-3 leading-relaxed">Sign in to manage your shipments with AI-powered intelligence.</p>
          </div>
        </div>
        <div className="px-8 py-8">
          {/* ── Demo Login Button ── */}
          <button
            onClick={handleDemoLogin}
            disabled={demoLoading}
            className="w-full py-3 mb-5 rounded-xl text-sm font-semibold transition-all duration-200
                       bg-gradient-to-r from-emerald-500 to-teal-500 text-white
                       hover:from-emerald-600 hover:to-teal-600 hover:shadow-lg hover:shadow-emerald-500/25
                       active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed
                       flex items-center justify-center gap-2"
          >
            {demoLoading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Entering Demo…
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.59 14.37a6 6 0 01-5.84 7.38v-4.8m5.84-2.58a14.98 14.98 0 006.16-12.12A14.98 14.98 0 009.631 8.41m5.96 5.96a14.926 14.926 0 01-5.841 2.58m-.119-8.54a6 6 0 00-7.381 5.84h4.8m2.58-5.84a14.927 14.927 0 00-2.58 5.84m2.699 2.7c-.103.021-.207.041-.311.06a15.09 15.09 0 01-2.448-2.448 14.9 14.9 0 01.06-.312m-2.24 2.39a4.493 4.493 0 00-1.757 4.306 4.493 4.493 0 004.306-1.758M16.5 9a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0z" />
                </svg>
                🚀 Quick Demo Login
              </>
            )}
          </button>
          {demoError && (
            <div className="mb-4 flex items-center gap-2 px-4 py-3 rounded-xl bg-red-50 border border-red-200/70 text-red-600 text-sm">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              {demoError}
            </div>
          )}

          {/* Divider */}
          <div className="relative mb-5">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-200" /></div>
            <div className="relative flex justify-center">
              <span className="px-3 text-xs text-gray-400 bg-white">or sign in with credentials</span>
            </div>
          </div>

          <AuthForm mode="login" onSubmit={handleLogin} />
          <p className="mt-6 text-center text-sm text-gray-400">
            No account?{" "}
            <Link href="/register" className="text-blue-600 font-medium hover:text-blue-500 transition-colors">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
