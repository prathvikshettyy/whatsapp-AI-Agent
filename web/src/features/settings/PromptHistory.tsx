import React, { useState } from "react";
import { History, RotateCcw, X } from "lucide-react";
import { PromptVersion } from "../../api/types";
import { usePromptHistory } from "../../api/settings";
import { Button } from "../../components/Button";
import { formatDateSeparator } from "../../lib/utils";

interface PromptHistoryProps {
  currentPrompt?: string;
  onRollback: (historicalPrompt: string) => void;
  onClose: () => void;
}

export const PromptHistory: React.FC<PromptHistoryProps> = ({
  currentPrompt: _currentPrompt,
  onRollback,
  onClose,
}) => {
  const { data: versions, isLoading } = usePromptHistory();
  const [selectedVersion, setSelectedVersion] = useState<PromptVersion | null>(null);

  const active = selectedVersion || (versions && versions.length > 0 ? versions[0] : null);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="flex h-[88vh] w-full max-w-4xl flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-4 bg-muted/20">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <History className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-base">Prompt Version History & Rollback</h3>
              <p className="text-xs text-muted-foreground">
                Inspect previous iterations of the Claude system prompt and restore prior versions.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-muted-foreground hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Two-column layout: versions list on left, diff view on right */}
        <div className="flex flex-1 overflow-hidden">
          {/* Versions Sidebar */}
          <div className="w-72 border-r border-border overflow-y-auto p-3 space-y-2 bg-muted/10">
            {isLoading && <p className="text-xs text-muted-foreground p-3">Loading history...</p>}

            {versions?.map((v) => {
              const isSelected = active?.id === v.id;
              return (
                <div
                  key={v.id}
                  onClick={() => setSelectedVersion(v)}
                  className={`cursor-pointer rounded-xl border p-3 text-xs transition-all ${
                    isSelected
                      ? "border-primary bg-primary/10 font-medium shadow-xs"
                      : "border-border hover:bg-accent/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-foreground font-mono">{v.id}</span>
                    <span className="text-[10px] text-muted-foreground">
                      {formatDateSeparator(v.created_at)}
                    </span>
                  </div>
                  <p className="font-medium text-foreground line-clamp-1 mb-1">{v.summary}</p>
                  <p className="text-[10px] text-muted-foreground">by {v.created_by}</p>
                </div>
              );
            })}
          </div>

          {/* Diff / Details Panel */}
          <div className="flex-1 flex flex-col overflow-hidden p-6 space-y-4">
            {active ? (
              <>
                <div className="flex items-center justify-between border-b border-border pb-3">
                  <div>
                    <h4 className="font-bold text-sm flex items-center gap-2">
                      <span>Version {active.id}</span>
                      <span className="text-xs text-muted-foreground font-normal">
                        ({formatDateSeparator(active.created_at)} by {active.created_by})
                      </span>
                    </h4>
                    <p className="text-xs text-muted-foreground mt-0.5">{active.summary}</p>
                  </div>

                  <Button
                    size="sm"
                    onClick={() => {
                      onRollback(active.prompt);
                      onClose();
                    }}
                    className="bg-amber-600 hover:bg-amber-700 text-white gap-1.5 shadow-sm"
                  >
                    <RotateCcw className="h-3.5 w-3.5" /> Rollback to this version
                  </Button>
                </div>

                <div className="flex-1 overflow-y-auto rounded-xl border border-input bg-muted/20 p-4 font-mono text-xs whitespace-pre-wrap leading-relaxed">
                  {active.prompt}
                </div>
              </>
            ) : (
              <div className="flex h-full items-center justify-center text-xs text-muted-foreground">
                Select a version from the left panel to inspect.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
