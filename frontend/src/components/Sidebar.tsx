import React from "react";
import type { LlmConfig, SessionSummary } from "../types";

export type SidebarProps = {
  userId: string;
  onUserIdChange: (value: string) => void;

  config: LlmConfig | null;
  models: string[];
  configModel: string;
  configBaseUrl: string;
  configApiKey: string;
  configLoading: boolean;
  modelsLoading: boolean;
  onConfigModelChange: (value: string) => void;
  onConfigBaseUrlChange: (value: string) => void;
  onConfigApiKeyChange: (value: string) => void;
  onSaveConfig: () => void;
  onFetchModels: () => void;

  sessions: SessionSummary[];
  currentSessionId: string;
  onNewChat: () => void;
  onRefreshSessions: () => void;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
};

export const Sidebar: React.FC<SidebarProps> = ({
  userId,
  onUserIdChange,
  config,
  models,
  configModel,
  configBaseUrl,
  configApiKey,
  configLoading,
  modelsLoading,
  onConfigModelChange,
  onConfigBaseUrlChange,
  onConfigApiKeyChange,
  onSaveConfig,
  onFetchModels,
  sessions,
  currentSessionId,
  onNewChat,
  onRefreshSessions,
  onSelectSession,
  onDeleteSession,
}) => {
  return (
    <aside className="w-72 border-r border-slate-700 flex flex-col shrink-0 bg-slate-800/50">
      <div className="p-3 border-b border-slate-700 space-y-2">
        <div>
          <label className="block text-xs text-slate-400 mb-1">用户 ID</label>
          <input
            value={userId}
            onChange={(e) => onUserIdChange(e.target.value)}
            placeholder="default"
            className="w-full rounded-lg bg-slate-700 border border-slate-600 px-3 py-2 text-sm focus:ring-2 focus:ring-cyan-500 focus:border-transparent"
          />
        </div>

        <div className="mt-2">
          <div className="text-xs text-slate-400 font-medium mb-2">
            模型配置
          </div>
          <table className="w-full text-sm">
            <tbody>
              <tr>
                <td className="text-slate-400 py-1 pr-2 align-top w-20">
                  模型
                </td>
                <td className="py-1">
                  <select
                    value={configModel}
                    onChange={(e) => onConfigModelChange(e.target.value)}
                    className="w-full rounded bg-slate-700 border border-slate-600 px-2 py-1.5 text-sm focus:ring-1 focus:ring-cyan-500"
                  >
                    {models.length === 0 ? (
                      <option value="">
                        {configLoading ? "加载中…" : "请先获取模型列表"}
                      </option>
                    ) : (
                      models.map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))
                    )}
                  </select>
                </td>
              </tr>
              <tr>
                <td />
                <td className="py-1">
                  <button
                    type="button"
                    disabled={modelsLoading}
                    onClick={onFetchModels}
                    className="text-xs rounded bg-slate-600 hover:bg-slate-500 px-2 py-1 disabled:opacity-50"
                  >
                    {modelsLoading ? "获取中…" : "获取模型列表"}
                  </button>
                </td>
              </tr>
              <tr>
                <td className="text-slate-400 py-1 pr-2 align-top">Base URL</td>
                <td className="py-1">
                  <input
                    value={configBaseUrl}
                    onChange={(e) => onConfigBaseUrlChange(e.target.value)}
                    placeholder="可选，如 https://api.openai.com/v1"
                    className="w-full rounded bg-slate-700 border border-slate-600 px-2 py-1.5 text-sm focus:ring-1 focus:ring-cyan-500"
                  />
                </td>
              </tr>
              <tr>
                <td className="text-slate-400 py-1 pr-2 align-top">
                  API Key
                </td>
                <td className="py-1">
                  <input
                    type="password"
                    value={configApiKey}
                    onChange={(e) => onConfigApiKeyChange(e.target.value)}
                    placeholder={
                      config?.api_key_set
                        ? "已配置（输入新值可覆盖）"
                        : "可选，不填用环境变量"
                    }
                    className="w-full rounded bg-slate-700 border border-slate-600 px-2 py-1.5 text-sm focus:ring-1 focus:ring-cyan-500"
                  />
                </td>
              </tr>
            </tbody>
          </table>
          <button
            type="button"
            onClick={onSaveConfig}
            className="mt-2 w-full rounded-lg bg-slate-600 hover:bg-slate-500 px-3 py-2 text-sm"
          >
            保存配置
          </button>
        </div>
      </div>

      <div className="p-3 border-b border-slate-700">
        <button
          type="button"
          onClick={onNewChat}
          className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 px-3 py-2 text-sm font-medium"
        >
          新会话
        </button>
        <button
          type="button"
          onClick={onRefreshSessions}
          className="w-full mt-2 rounded-lg bg-slate-600 hover:bg-slate-500 px-3 py-2 text-sm"
        >
          刷新会话列表
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3">
        <div className="text-xs text-slate-400 mb-2">会话列表</div>
        {sessions.length === 0 ? (
          <p className="text-slate-500 text-sm">
            暂无会话，发送消息将自动创建
          </p>
        ) : (
          <ul className="space-y-1">
            {sessions.map((s) => (
              <li key={s.session_id} className="flex items-center gap-1 group">
                <button
                  type="button"
                  onClick={() => onSelectSession(s.session_id)}
                  className={
                    "flex-1 min-w-0 rounded-lg px-3 py-2 text-sm text-left hover:bg-slate-700 truncate " +
                    (s.session_id === currentSessionId
                      ? "bg-slate-700 text-cyan-400"
                      : "")
                  }
                >
                  {s.session_id.slice(0, 8)}… ({s.message_count || 0} 条)
                </button>
                <button
                  type="button"
                  title="删除会话"
                  onClick={() => onDeleteSession(s.session_id)}
                  className="shrink-0 rounded p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 opacity-0 group-hover:opacity-100 transition-opacity text-lg leading-none"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;

