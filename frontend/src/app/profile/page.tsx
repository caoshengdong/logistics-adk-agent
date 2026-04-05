"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";
import { getMe, updateProfile } from "@/lib/api";
import type { User } from "@/types";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [customerCode, setCustomerCode] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) { router.replace("/login"); return; }
    getMe().then((u) => {
      setUser(u);
      setDisplayName(u.display_name);
      setCustomerCode(u.customer_code);
    });
  }, [router]);

  const handleSave = async () => {
    setSaving(true);
    const updated = await updateProfile({
      display_name: displayName,
      customer_code: customerCode,
      auth_token: authToken || undefined,
    });
    setUser(updated);
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  if (!user) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex flex-col items-center gap-3">
        <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        <p className="text-sm text-gray-400">Loading profile…</p>
      </div>
    </div>
  );

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      {/* Background decoration */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-gray-400/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-blue-400/5 rounded-full blur-3xl" />
      </div>

      <div className="card w-full max-w-lg overflow-hidden animate-fade-in">
        <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 px-8 py-8 text-white relative overflow-hidden">
          {/* Background pattern */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute top-4 right-4 w-24 h-24 border-2 border-white rounded-2xl rotate-12" />
          </div>
          <div className="relative flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xl font-bold shadow-xl shadow-blue-500/20">
              {user.display_name?.[0]?.toUpperCase() || user.email[0].toUpperCase()}
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">Profile Settings</h1>
              <p className="text-gray-400 text-sm">{user.email}</p>
            </div>
          </div>
        </div>
        <div className="px-8 py-8 space-y-5">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Email</label>
            <input value={user.email} disabled className="input-field bg-gray-50 text-gray-500 cursor-not-allowed" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Display Name</label>
            <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="input-field" />
          </div>

          <div className="relative py-2">
            <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-100" /></div>
            <div className="relative flex justify-center">
              <span className="px-3 text-[10px] text-gray-400 bg-white uppercase tracking-widest">API Credentials</span>
            </div>
          </div>

          <p className="text-xs text-gray-400 -mt-1">
            Update your logistics API credentials. These are injected into agent sessions automatically.
          </p>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Customer Code</label>
            <input value={customerCode} onChange={(e) => setCustomerCode(e.target.value)}
              className="input-field font-mono" placeholder="e.g. CUS001" />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">Auth Token</label>
            <input value={authToken} onChange={(e) => setAuthToken(e.target.value)}
              type="password" className="input-field font-mono" placeholder="Leave empty to keep current" />
          </div>

          <button onClick={handleSave} disabled={saving}
            className="w-full py-3 btn-primary text-sm">
            {saving ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Saving...
              </span>
            ) : "Save Changes"}
          </button>

          {saved && (
            <div className="flex items-center gap-2 px-4 py-3 rounded-xl bg-emerald-50 border border-emerald-200/70 text-emerald-700 text-sm animate-slide-up">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Saved successfully!
            </div>
          )}

          <button onClick={() => router.push("/chat")}
            className="w-full py-3 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 hover:border-gray-300 transition-all flex items-center justify-center gap-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
            </svg>
            Back to Chat
          </button>
        </div>
      </div>
    </div>
  );
}
