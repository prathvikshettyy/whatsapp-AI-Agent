import React, { useState } from "react";
import { Eye, Edit3, Save, X, Trash2 } from "lucide-react";
import { KbArticle } from "../../api/types";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";
import { useCreateKbArticle, useDeleteKbArticle, useUpdateKbArticle } from "../../api/kb";
import { useToast } from "../../components/Toast";

interface KbEditorProps {
  article: Partial<KbArticle> | null;
  onClose: () => void;
}

export const KbEditor: React.FC<KbEditorProps> = ({ article, onClose }) => {
  const isEditing = Boolean(article?.id);
  const [title, setTitle] = useState(article?.title || "");
  const [key, setKey] = useState(article?.key || "");
  const [content, setContent] = useState(article?.content || "");
  const [tags, setTags] = useState(article?.tags?.join(", ") || "");
  const [previewMode, setPreviewMode] = useState(false);

  const { mutate: createArticle, isPending: isCreating } = useCreateKbArticle();
  const { mutate: updateArticle, isPending: isUpdating } = useUpdateKbArticle();
  const { mutate: deleteArticle, isPending: isDeleting } = useDeleteKbArticle();
  const { toast } = useToast();

  const handleSave = () => {
    if (!title.trim() || !content.trim()) return;

    const payload = {
      title: title.trim(),
      key: key.trim().toLowerCase() || title.toLowerCase().replace(/\s+/g, "_"),
      content: content.trim(),
      tags: tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean),
    };

    if (isEditing && article?.id) {
      updateArticle(
        { id: article.id, ...payload },
        {
          onSuccess: () => {
            toast({ title: "Article Updated", description: "Claude can now use this FAQ entry in WhatsApp conversations.", variant: "success" });
            onClose();
          },
        }
      );
    } else {
      createArticle(payload, {
        onSuccess: () => {
          toast({ title: "Article Created", description: "New knowledge base article saved.", variant: "success" });
          onClose();
        },
      });
    }
  };

  const handleDelete = () => {
    if (!article?.id || !confirm("Are you sure you want to delete this FAQ entry?")) return;
    deleteArticle(article.id, {
      onSuccess: () => {
        toast({ title: "Article Deleted", description: "Article removed from knowledge base.", variant: "default" });
        onClose();
      },
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <div className="flex h-[90vh] w-full max-w-3xl flex-col rounded-2xl border border-border bg-card shadow-2xl overflow-hidden animate-in fade-in-50 zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-4 bg-muted/20">
          <div>
            <h3 className="font-bold text-base">
              {isEditing ? "Edit FAQ & Knowledge Article" : "Create Knowledge Base Article"}
            </h3>
            <p className="text-xs text-muted-foreground">
              These guidelines and answers are directly searched by Claude when customers ask questions.
            </p>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-muted-foreground hover:bg-accent">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-semibold text-foreground">Article Title</label>
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Return and Refund Policy"
                className="mt-1"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-foreground">Lookup Keyword / Slug</label>
              <Input
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="e.g. return_policy"
                className="mt-1 font-mono text-xs"
              />
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-foreground">Tags (comma-separated)</label>
            <Input
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. policy, returns, refunds, moneyback"
              className="mt-1"
            />
          </div>

          {/* Markdown Content & Preview Toggle */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-foreground">Article Content (Markdown)</label>
              <div className="flex items-center rounded-lg border border-border bg-muted/40 p-0.5 text-xs">
                <button
                  type="button"
                  onClick={() => setPreviewMode(false)}
                  className={`flex items-center gap-1 rounded-md px-2 py-0.5 font-medium transition-colors ${
                    !previewMode ? "bg-card text-foreground shadow-xs" : "text-muted-foreground"
                  }`}
                >
                  <Edit3 className="h-3 w-3" /> Edit
                </button>
                <button
                  type="button"
                  onClick={() => setPreviewMode(true)}
                  className={`flex items-center gap-1 rounded-md px-2 py-0.5 font-medium transition-colors ${
                    previewMode ? "bg-card text-foreground shadow-xs" : "text-muted-foreground"
                  }`}
                >
                  <Eye className="h-3 w-3" /> Preview
                </button>
              </div>
            </div>

            {previewMode ? (
              <div className="h-64 overflow-y-auto rounded-xl border border-input bg-muted/10 p-4 text-sm whitespace-pre-wrap leading-relaxed">
                {content || <span className="text-muted-foreground italic">No content to preview</span>}
              </div>
            ) : (
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={10}
                placeholder="Write the clear factual answer or policy that Claude should use when responding on WhatsApp..."
                className="w-full rounded-xl border border-input bg-transparent p-3 text-sm focus:outline-none focus:ring-1 focus:ring-primary font-mono leading-relaxed"
              />
            )}
          </div>
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between border-t border-border p-4 bg-muted/20">
          {isEditing ? (
            <Button
              variant="destructive"
              size="sm"
              loading={isDeleting}
              onClick={handleDelete}
              className="gap-1.5"
            >
              <Trash2 className="h-4 w-4" /> Delete
            </Button>
          ) : <div />}

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button
              size="sm"
              loading={isCreating || isUpdating}
              onClick={handleSave}
              className="bg-emerald-600 hover:bg-emerald-700 text-white gap-1.5 shadow-sm"
            >
              <Save className="h-4 w-4" /> Save Article
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
