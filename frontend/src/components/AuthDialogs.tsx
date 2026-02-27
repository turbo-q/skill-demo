import React, { useState } from "react";

export interface AuthDialogsProps {
  onLogin: (username: string, password: string) => Promise<void>;
  onRegister: (username: string, password: string) => Promise<void>;
}

const AuthDialogs: React.FC<AuthDialogsProps> = ({ onLogin, onRegister }) => {
  const [mode, setMode] = useState<"login" | "register" | null>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const close = () => {
    setMode(null);
    setUsername("");
    setPassword("");
    setError(null);
  };

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!mode) return;
    setLoading(true);
    setError(null);
    try {
      if (mode === "login") {
        await onLogin(username, password);
      } else {
        await onRegister(username, password);
        await onLogin(username, password);
      }
      close();
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  if (!mode) {
    return (
      <>
        <button
          type="button"
          onClick={() => setMode("login")}
          className="px-3 py-1.5 text-xs rounded-full border border-slate-600 text-slate-200 hover:bg-slate-800"
        >
          登录
        </button>
        <button
          type="button"
          onClick={() => setMode("register")}
          className="px-3 py-1.5 text-xs rounded-full border border-cyan-600 bg-cyan-600/20 text-cyan-200 hover:bg-cyan-600/30"
        >
          注册
        </button>
      </>
    );
  }

  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-sm rounded-xl bg-slate-900 border border-slate-700 shadow-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-50">
            {mode === "login" ? "登录" : "注册新账号"}
          </h2>
          <button
            type="button"
            onClick={close}
            className="text-slate-400 hover:text-slate-200 text-lg leading-none"
          >
            ×
          </button>
        </div>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div className="space-y-1">
            <label className="block text-xs text-slate-400">用户名</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm focus:ring-1 focus:ring-cyan-500"
            />
          </div>
          <div className="space-y-1">
            <label className="block text-xs text-slate-400">密码</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded bg-slate-800 border border-slate-600 px-3 py-2 text-sm focus:ring-1 focus:ring-cyan-500"
            />
            <p className="text-[11px] text-slate-500">
              密码至少 6 位，建议在本地开发环境使用测试账号。
            </p>
          </div>
          {error && (
            <p className="text-xs text-red-400 bg-red-900/40 rounded px-2 py-1">
              {error}
            </p>
          )}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 px-3 py-2 text-sm font-medium disabled:opacity-50"
          >
            {loading
              ? "提交中…"
              : mode === "login"
              ? "登录"
              : "注册并登录"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default AuthDialogs;

