import React, { useEffect, useMemo, useState } from "react";
import {
  deleteSessionApi,
  fetchConfig,
  fetchHistory,
  fetchModels,
  fetchSessions,
  sendChat,
  updateConfig,
} from "./api";
import type { ChatMessage, LlmConfig, SessionSummary } from "./types";
import Sidebar from "./components/Sidebar";
import MessageList from "./components/MessageList";
import MessageInput from "./components/MessageInput";

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

  const prettyCurrentSession = useMemo(() => {
    if (!currentSessionId) return "未选择";
    return currentSessionId.length > 12
      ? `${currentSessionId.slice(0, 12)}…`
      : currentSessionId;
  }, [currentSessionId]);

  async function loadSessions() {
    const list = await fetchSessions(userId);
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
    await deleteSessionApi(sessionId, userId);
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
    const localUserId = (userId || "").trim() || undefined;
    setSending(true);
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    try {
      const data = await sendChat({
        sessionId: currentSessionId || undefined,
        userId: localUserId,
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
    const body: Record<string, unknown> = {
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

  useEffect(() => {
    loadSessions();
    loadConfig();
  }, []);

  return (
    <div className="bg-slate-900 text-slate-100 min-h-screen flex flex-col">
      <header className="border-b border-slate-700 px-4 py-3 flex items-center gap-3 shrink-0">
        <span className="font-semibold text-lg">漏洞扫描 Agent</span>
        <span className="text-slate-400 text-sm">Skill · 工具 · 会话</span>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* 侧栏 */}
        <Sidebar
          userId={userId}
          onUserIdChange={setUserId}
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
          sessions={sessions}
          currentSessionId={currentSessionId}
          onNewChat={handleNewChat}
          onRefreshSessions={loadSessions}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
        />

        {/* 主区 */}
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
    </div>
  );
};

export default App;

