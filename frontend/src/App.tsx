import React, { useEffect, useMemo, useState } from "react";
import {
  deleteSessionApi,
  fetchConfig,
  fetchHistory,
  fetchModels,
  fetchSessions,
  fetchSkills,
  login,
  logout,
  me,
  register,
  sendChat,
  updateConfig,
} from "./api";
import type {
  AuthUser,
  ChatMessage,
  LlmConfig,
  SessionSummary,
  SkillSummary,
} from "./types";
import Sidebar from "./components/Sidebar";
import MessageList from "./components/MessageList";
import MessageInput from "./components/MessageInput";
import SkillList from "./components/SkillList";
import SettingsPanel from "./components/SettingsPanel";
import AuthDialogs from "./components/AuthDialogs";

const App: React.FC = () => {
  const [userId, setUserId] = useState("default");
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const [config, setConfig] = useState<LlmConfig | null>(null);
  const [models, setModels] = useState<string[]>([]);
  const [configModel, setConfigModel] = useState("");
  const [configBaseUrl, setConfigBaseUrl] = useState("");
  const [configApiKey, setConfigApiKey] = useState("");
  const [configLoading, setConfigLoading] = useState(false);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [skills, setSkills] = useState<SkillSummary[]>([]);
  const [activeTab, setActiveTab] = useState<"chat" | "skills" | "settings">(
    "chat",
  );
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  const prettyCurrentSession = useMemo(() => {
    if (!currentSessionId) return "未选择";
    return currentSessionId.length > 12
      ? `${currentSessionId.slice(0, 12)}…`
      : currentSessionId;
  }, [currentSessionId]);

  async function loadSessions() {
    const list = await fetchSessions();
    setSessions(list);
  }

  async function loadHistory(sessionId: string) {
    const msgs = await fetchHistory(sessionId);
    setMessages(msgs);
  }

  async function handleSelectSession(sessionId: string) {
    setCurrentSessionId(sessionId);
    await loadHistory(sessionId);
    await loadSessions();
  }

  async function handleDeleteSession(sessionId: string) {
    if (
      !window.confirm(
        "确定删除该会话？将同时删除该会话下的全部消息，且不可恢复。",
      )
    ) {
      return;
    }
    await deleteSessionApi(sessionId);
    if (currentSessionId === sessionId) {
      setCurrentSessionId("");
      setMessages([]);
    }
    await loadSessions();
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || sending) return;
    if (!currentUser) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "请先登录后再发送消息。" },
      ]);
      return;
    }
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    try {
      const data = await sendChat({
        sessionId: currentSessionId || undefined,
        message: text,
      });
      if (data.session_id) {
        setCurrentSessionId(data.session_id);
        await loadSessions();
      }
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.reply || "", tool_calls: data.tool_calls || [] },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `请求失败: ${err?.message || String(err)}` },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function loadConfig() {
    setConfigLoading(true);
    try {
      const c = await fetchConfig();
      setConfig(c);
      setConfigBaseUrl(c.base_url || "");
      setConfigApiKey("");
      if (c.api_key_set || (c.base_url && c.base_url.length > 0)) {
        await loadModels(false, c.model);
      }
    } finally {
      setConfigLoading(false);
    }
  }

  async function loadModels(useFormCredentials: boolean, selectedId?: string) {
    setModelsLoading(true);
    try {
      const params = useFormCredentials
        ? {
            base_url: configBaseUrl.trim() || undefined,
            api_key: configApiKey || undefined,
          }
        : undefined;
      const list = await fetchModels(params);
      setModels(list);
      const finalSelected =
        (selectedId && list.includes(selectedId)) ||
        (configModel && list.includes(configModel))
          ? selectedId || configModel
          : list[0] || "";
      setConfigModel(finalSelected || "");
    } finally {
      setModelsLoading(false);
    }
  }

  async function handleSaveConfig() {
    const body: { model: string; base_url: string; api_key?: string } = {
      model: configModel,
      base_url: configBaseUrl.trim(),
    };
    if (configApiKey !== "") {
      body.api_key = configApiKey;
    }
    const data = await updateConfig(body);
    setConfig({
      model: data.model,
      base_url: data.base_url,
      api_key_set: data.api_key_set,
    });
    setConfigApiKey("");
  }

  function handleNewChat() {
    setCurrentSessionId("");
    setMessages([]);
    loadSessions();
  }

  async function loadSkills() {
    const list = await fetchSkills();
    setSkills(list);
  }

  useEffect(() => {
    (async () => {
      try {
        const u = await me();
        setCurrentUser(u);
        await loadSessions();
        await loadSkills();
      } catch {
        setCurrentUser(null);
      } finally {
        setAuthChecked(true);
      }
    })();
    void loadConfig();
  }, []);

  async function handleLogin(username: string, password: string) {
    const u = await login(username, password);
    setCurrentUser(u);
    await loadSessions();
    await loadSkills();
    setActiveTab("chat");
  }

  async function handleRegister(username: string, password: string) {
    await register(username, password);
  }

  async function handleLogout() {
    await logout();
    setCurrentUser(null);
    setSessions([]);
    setMessages([]);
  }

  return (
    <div className="bg-slate-900 text-slate-100 min-h-screen flex flex-col">
      <header className="border-b border-slate-700 px-4 py-3 flex items-center justify-between gap-4 shrink-0">
        <div className="flex items-center gap-3">
          <span className="font-semibold text-lg">漏洞扫描 Agent</span>
          <span className="text-slate-400 text-sm">Skill · 工具 · 会话</span>
          {currentUser && (
            <span className="text-xs text-slate-400 border border-slate-600 rounded-full px-2 py-0.5">
              用户：<span className="text-slate-100">{currentUser.username}</span>
            </span>
          )}
        </div>
        <nav className="flex items-center gap-3 text-sm">
          <button
            type="button"
            className={
              "px-3 py-1.5 rounded-full border " +
              (activeTab === "chat"
                ? "border-cyan-500 bg-cyan-600/20 text-cyan-200"
                : "border-transparent text-slate-300 hover:bg-slate-800")
            }
            onClick={() => setActiveTab("chat")}
          >
            对话
          </button>
          <button
            type="button"
            className={
              "px-3 py-1.5 rounded-full border " +
              (activeTab === "skills"
                ? "border-cyan-500 bg-cyan-600/20 text-cyan-200"
                : "border-transparent text-slate-300 hover:bg-slate-800")
            }
            onClick={() => setActiveTab("skills")}
          >
            技能
          </button>
          <button
            type="button"
            className={
              "px-3 py-1.5 rounded-full border " +
              (activeTab === "settings"
                ? "border-cyan-500 bg-cyan-600/20 text-cyan-200"
                : "border-transparent text-slate-300 hover:bg-slate-800")
            }
            onClick={() => setActiveTab("settings")}
          >
            设置
          </button>
          <div className="h-5 w-px bg-slate-700" />
          <div className="flex items-center gap-2">
            {currentUser ? (
              <>
                <span className="text-xs text-slate-300">
                  已登录：{currentUser.username}
                </span>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="px-2 py-1 text-xs rounded-full border border-slate-600 text-slate-200 hover:bg-slate-800"
                >
                  退出
                </button>
              </>
            ) : (
              <AuthDialogs
                onLogin={handleLogin}
                onRegister={handleRegister}
              />
            )}
          </div>
        </nav>
      </header>

      {activeTab === "chat" && (
        <div className="flex flex-1 min-h-0">
          <Sidebar
            sessions={sessions}
            currentSessionId={currentSessionId}
            onNewChat={handleNewChat}
            onRefreshSessions={loadSessions}
            onSelectSession={handleSelectSession}
            onDeleteSession={handleDeleteSession}
          />

          <main className="flex-1 flex flex-col min-w-0">
            <div className="border-b border-slate-700 px-4 py-2 flex items-center gap-2 shrink-0">
              <span className="text-slate-400 text-sm">当前会话：</span>
              <code className="text-cyan-400 text-sm truncate flex-1">
                {prettyCurrentSession}
              </code>
            </div>

            <MessageList messages={messages} />
            <MessageInput
              value={input}
              onChange={setInput}
              onSubmit={handleSend}
              disabled={sending}
              placeholder={
                currentSessionId
                  ? "继续输入消息…"
                  : "输入消息，发送将自动创建新会话"
              }
            />
          </main>
        </div>
      )}

      {activeTab === "skills" && (
        <main className="flex-1 min-h-0 px-4 py-4">
          <h2 className="text-sm font-semibold text-slate-50 mb-3">
            已加载的技能
          </h2>
          <p className="text-xs text-slate-400 mb-4">
            这些技能由 SkillsMiddleware 从后端技能仓库中自动加载，你可以在这里快速查看有哪些可用能力。
          </p>
          <SkillList skills={skills} />
        </main>
      )}

      {activeTab === "settings" && (
        <main className="flex-1 min-h-0">
          <SettingsPanel
            config={config}
            models={models}
            configModel={configModel}
            configBaseUrl={configBaseUrl}
            configApiKey={configApiKey}
            configLoading={configLoading}
            modelsLoading={modelsLoading}
            onConfigModelChange={setConfigModel}
            onConfigBaseUrlChange={setConfigBaseUrl}
            onConfigApiKeyChange={setConfigApiKey}
            onSaveConfig={handleSaveConfig}
            onFetchModels={() => loadModels(true)}
          />
        </main>
      )}
    </div>
  );
};

export default App;

