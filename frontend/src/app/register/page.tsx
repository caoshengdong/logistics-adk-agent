"use client";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AuthForm from "@/components/AuthForm";
import { register } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function RegisterPage() {
  const router = useRouter();

  const handleRegister = async (data: Record<string, string>) => {
    const res = await register(
      data.email, data.password, data.displayName,
      data.customerCode, data.authToken,
    );
    setToken(res.access_token);
    router.push("/chat");
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-80 h-80 bg-indigo-400/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -right-40 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl" />
      </div>

      <div className="card w-full max-w-md overflow-hidden animate-fade-in">
        <div className="bg-gradient-to-br from-indigo-600 via-indigo-600 to-purple-700 px-8 py-10 text-white relative overflow-hidden">
          {/* Background pattern */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-4 right-4 w-24 h-24 border-2 border-white rounded-2xl rotate-12" />
            <div className="absolute bottom-4 left-4 w-16 h-16 border-2 border-white rounded-xl -rotate-12" />
          </div>
          <div className="relative">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-11 h-11 rounded-xl bg-white/20 backdrop-blur flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zM4 19.235v-.11a6.375 6.375 0 0112.75 0v.109A12.318 12.318 0 0110.374 21c-2.331 0-4.512-.645-6.374-1.766z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">Create Account</h1>
                <p className="text-indigo-200 text-xs">Join Logistics AI</p>
              </div>
            </div>
            <p className="text-sm text-indigo-100 mt-3 leading-relaxed">Set up your account to start using AI-powered logistics management.</p>
          </div>
        </div>
        <div className="px-8 py-8">
          <AuthForm mode="register" onSubmit={handleRegister} />
          <p className="mt-6 text-center text-sm text-gray-400">
            Already have an account?{" "}
            <Link href="/login" className="text-blue-600 font-medium hover:text-blue-500 transition-colors">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
