import React from "react";
import type { LlmConfig } from "../types";

export interface SettingsPanelProps {
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
}

const SettingsPanel: React.FC<SettingsPanelProps> = ({
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
}) => {
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
      <section className="rounded-xl border border-slate-700 bg-slate-800/60 p-4">
        <h2 className="text-sm font-semibold text-slate-50 mb-3">
          模型配置（全局默认）
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          这里配置的是全局默认模型和提供商信息，所有会话都会使用当前配置。你可以在这里切换默认模型，而无需在会话里单独配置。
        </p>
        <table className="w-full text-sm">
          <tbody>
            <tr>
              <td className="text-slate-400 py-1 pr-2 align-top w-24">模型</td>
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
              <td className="text-slate-400 py-1 pr-2 align-top">
                Base URL
              </td>
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
              <td className="text-slate-400 py-1 pr-2 align-top">API Key</td>
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
          className="mt-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 px-4 py-2 text-sm font-medium"
        >
          保存为默认配置
        </button>
      </section>
    </div>
  );
};

export default SettingsPanel;

