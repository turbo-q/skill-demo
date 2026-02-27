import React from "react";
import type { SkillSummary } from "../types";

export interface SkillListProps {
  skills: SkillSummary[];
}

const SkillList: React.FC<SkillListProps> = ({ skills }) => {
  if (!skills.length) {
    return <p className="text-slate-500 text-sm">当前还没有已索引的技能。</p>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {skills.map((s) => (
        <article
          key={s.id}
          className="rounded-xl border border-slate-700 bg-slate-800/60 p-4 flex flex-col gap-2"
        >
          <header>
            <h3 className="text-sm font-semibold text-slate-50 truncate">
              {s.name || s.id}
            </h3>
            {s.id !== s.name && (
              <p className="text-xs text-slate-400 mt-0.5 break-all">{s.id}</p>
            )}
          </header>
          <p className="text-sm text-slate-200 line-clamp-3 whitespace-pre-wrap">
            {s.description}
          </p>
          {s.tags && s.tags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {s.tags.map((t) => (
                <span
                  key={t}
                  className="inline-flex items-center rounded-full bg-slate-700/80 px-2 py-0.5 text-[11px] text-slate-200"
                >
                  {t}
                </span>
              ))}
            </div>
          )}
        </article>
      ))}
    </div>
  );
};

export default SkillList;

