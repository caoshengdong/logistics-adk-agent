"use client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthForm from "@/components/AuthForm";
import { login } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();

  const handleLogin = async (data: Record<string, string>) => {
    const res = await login(data.email, data.password);
    setToken(res.access_token);
    router.push("/chat");
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
