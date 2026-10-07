import React, { useEffect, useState } from "react";
import { Settings as SettingsIcon, Save, History, ShieldAlert, Cpu, Sliders } from "lucide-react";
import { useSettings, useUpdateSettings } from "../../api/settings";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";
import { PromptHistory } from "./PromptHistory";
import { useToast } from "../../components/Toast";

export const SettingsPage: React.FC = () => {
  const { data: initialSettings, isLoading } = useSettings();
  const { mutate: updateSettings, isPending: isSaving } = useUpdateSettings();
  const { toast } = useToast();

  const [prompt, setPrompt] = useState("");
  const [model, setModel] = useState("claude-3-5-sonnet-latest");
  const [rateLimit, setRateLimit] = useState(10);
  const [maxTurns, setMaxTurns] = useState(20);
  const [handoffKeywords, setHandoffKeywords] = useState("");
  const [optOutKeywords, setOptOutKeywords] = useState("");
  const [versionSummary, setVersionSummary] = useState("");
  const [showHistory, setShowHistory] = useState(false);
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (initialSettings) {
      setPrompt(initialSettings.system_prompt || "");
      setModel(initialSettings.model || "claude-3-5-sonnet-latest");
      setRateLimit(initialSettings.rate_limit_per_min || 10);
      setMaxTurns(initialSettings.max_history_turns || 20);
      setHandoffKeywords(initialSettings.handoff_keywords?.join(", ") || "");
      setOptOutKeywords(initialSettings.opt_out_keywords?.join(", ") || "");
      setIsDirty(false);
    }
  }, [initialSettings]);

  const handleSave = () => {
    updateSettings(
      {
        system_prompt: prompt,
        model,
        rate_limit_per_min: Number(rateLimit),
        max_history_turns: Number(maxTurns),
        handoff_keywords: handoffKeywords.split(",").map((k) => k.trim().toLowerCase()).filter(Boolean),
        opt_out_keywords: optOutKeywords.split(",").map((k) => k.trim().toLowerCase()).filter(Boolean),
        version_summary: versionSummary.trim() || "Settings updated from Admin Dashboard",
      },
      {
        onSuccess: () => {
          setIsDirty(false);
          setVersionSummary("");
          toast({
            title: "Settings Saved Successfully",
            description: "Claude configuration and WhatsApp policies have been updated.",
            variant: "success",
          });
        },
        onError: (err: any) => {
          toast({
            title: "Save Failed",
            description: err.message || "Failed to update settings.",
            variant: "destructive",
          });
        },
      }
    );
  };

  const handleRollback = (historicalPrompt: string) => {
    setPrompt(historicalPrompt);
    setIsDirty(true);
    toast({
      title: "Prompt Reverted",
      description: "Remember to click 'Save Changes' to apply this version to live WhatsApp replies.",
      variant: "warning",
    });
  };

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-4 md:p-8 space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <SettingsIcon className="h-6 w-6 text-primary" />
            <span>Agent Configuration & Prompts</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Configure Claude's persona, tool behavior, safety rules, and WhatsApp rate limit parameters.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => setShowHistory(true)}
            className="gap-1.5"
          >
            <History className="h-4 w-4" /> Version History
          </Button>

          <Button
            onClick={handleSave}
            loading={isSaving}
            disabled={!isDirty && !versionSummary}
            className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 shadow-sm"
          >
            <Save className="h-4 w-4" /> Save Changes
          </Button>
        </div>
      </div>

      {isDirty && (
        <div className="flex items-center justify-between rounded-xl bg-amber-500/10 border border-amber-500/20 px-4 py-2.5 text-xs text-amber-700 dark:text-amber-400">
          <span>You have unsaved changes. Make sure to click <strong>Save Changes</strong> before leaving.</span>
          <span className="font-semibold underline cursor-pointer" onClick={handleSave}>Save now</span>
        </div>
      )}

      {/* Main Grid: Prompt Editor & System Parameters */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: System Prompt (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm">Claude System Prompt & Persona</h3>
                <p className="text-xs text-muted-foreground">
                  Instructions directing Claude how to reply, format responses, and call tools.
                </p>
              </div>
            </div>

            <textarea
              value={prompt}
              onChange={(e) => {
                setPrompt(e.target.value);
                setIsDirty(true);
              }}
              rows={16}
              className="w-full rounded-xl border border-input bg-muted/20 p-4 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-primary leading-relaxed resize-y"
            />

            <div>
              <label className="text-xs font-semibold text-foreground">Change Summary (optional)</label>
              <Input
                value={versionSummary}
                onChange={(e) => {
                  setVersionSummary(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="e.g. Added return policy guidance and formatted bullet list"
                className="mt-1"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Model & Safety Controls (1 col) */}
        <div className="space-y-4">
          {/* Model Card */}
          <div className="rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xs">
            <h3 className="font-bold text-sm flex items-center gap-2">
              <Cpu className="h-4 w-4 text-primary" /> Claude AI Model
            </h3>

            <div>
              <label className="text-xs font-semibold text-foreground">Model Identifier</label>
              <select
                value={model}
                onChange={(e) => {
                  setModel(e.target.value);
                  setIsDirty(true);
                }}
                className="mt-1 w-full rounded-xl border border-input bg-background p-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="claude-3-5-sonnet-latest">claude-3-5-sonnet-latest (Recommended)</option>
                <option value="claude-3-5-haiku-latest">claude-3-5-haiku-latest (Fastest / Low cost)</option>
                <option value="claude-3-opus-latest">claude-3-opus-latest (Deep reasoning)</option>
              </select>
            </div>
          </div>

          {/* Operational Controls Card */}
          <div className="rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xs">
            <h3 className="font-bold text-sm flex items-center gap-2">
              <Sliders className="h-4 w-4 text-emerald-500" /> Operational & Limits
            </h3>

            <div>
              <label className="text-xs font-semibold text-foreground">Rate Limit (Messages/min per user)</label>
              <Input
                type="number"
                value={rateLimit}
                onChange={(e) => {
                  setRateLimit(Number(e.target.value));
                  setIsDirty(true);
                }}
                min={1}
                max={60}
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground">Max Chat History Turns in Context</label>
              <Input
                type="number"
                value={maxTurns}
                onChange={(e) => {
                  setMaxTurns(Number(e.target.value));
                  setIsDirty(true);
                }}
                min={5}
                max={50}
                className="mt-1"
              />
            </div>
          </div>

          {/* Safety & Compliance Card */}
          <div className="rounded-2xl border border-border bg-card p-5 space-y-4 shadow-xs">
            <h3 className="font-bold text-sm flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-amber-500" /> WhatsApp Compliance
            </h3>

            <div>
              <label className="text-xs font-semibold text-foreground">Human Handoff Keywords</label>
              <Input
                value={handoffKeywords}
                onChange={(e) => {
                  setHandoffKeywords(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="agent, human, support, helpdesk"
                className="mt-1 text-xs"
              />
              <p className="text-[10px] text-muted-foreground mt-0.5">Triggers human handoff and pauses bot.</p>
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground">Opt-Out Keywords (WhatsApp Policy)</label>
              <Input
                value={optOutKeywords}
                onChange={(e) => {
                  setOptOutKeywords(e.target.value);
                  setIsDirty(true);
                }}
                placeholder="stop, unsubscribe, cancel"
                className="mt-1 text-xs"
              />
              <p className="text-[10px] text-muted-foreground mt-0.5">Mandatory unsubscribe compliance.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Version History Modal */}
      {showHistory && (
        <PromptHistory
          currentPrompt={prompt}
          onRollback={handleRollback}
          onClose={() => setShowHistory(false)}
        />
      )}
    </div>
  );
};
