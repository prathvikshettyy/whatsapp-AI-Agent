import React, { useState } from "react";
import { Plus, Search, BookOpen, Clock, Tag } from "lucide-react";
import { KbArticle } from "../../api/types";
import { useKbArticles } from "../../api/kb";
import { Button } from "../../components/Button";
import { KbEditor } from "./KbEditor";
import { Skeleton } from "../../components/Input";
import { formatDateSeparator } from "../../lib/utils";

export const KbPage: React.FC = () => {
  const { data: articles, isLoading } = useKbArticles();
  const [search, setSearch] = useState("");
  const [editingArticle, setEditingArticle] = useState<Partial<KbArticle> | null>(null);

  const filtered = articles?.filter((a) => {
    const q = search.toLowerCase();
    return (
      a.title.toLowerCase().includes(q) ||
      a.key.toLowerCase().includes(q) ||
      a.content.toLowerCase().includes(q) ||
      a.tags.some((t) => t.toLowerCase().includes(q))
    );
  });

  return (
    <div className="flex h-full w-full flex-col overflow-y-auto p-4 md:p-8 space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-emerald-600" />
            <span>Knowledge Base & FAQs</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage factual business information, policies, and FAQs accessible to Claude during customer chats.
          </p>
        </div>

        <Button
          onClick={() => setEditingArticle({})}
          className="bg-emerald-600 hover:bg-emerald-700 text-white gap-2 shadow-sm shrink-0"
        >
          <Plus className="h-4 w-4" /> Add Article
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter knowledge entries by title, keyword or tag..."
          className="w-full rounded-xl border border-input bg-card pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-primary shadow-xs"
        />
      </div>

      {/* Articles Grid */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="rounded-xl border border-border p-4 space-y-3 bg-card">
              <Skeleton className="h-5 w-1/2" />
              <Skeleton className="h-14 w-full" />
              <Skeleton className="h-4 w-1/4" />
            </div>
          ))}
        </div>
      )}

      {!isLoading && filtered && filtered.length === 0 && (
        <div className="rounded-2xl border border-dashed border-border p-12 text-center">
          <BookOpen className="h-10 w-10 text-muted-foreground mx-auto mb-2 opacity-50" />
          <h3 className="font-semibold text-base">No knowledge base articles match</h3>
          <p className="text-xs text-muted-foreground mt-1">Try another search keyword or create a new article.</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filtered?.map((art) => (
          <div
            key={art.id}
            onClick={() => setEditingArticle(art)}
            className="group flex flex-col justify-between rounded-xl border border-border bg-card p-5 shadow-xs hover:border-primary/50 hover:shadow-md transition-all cursor-pointer"
          >
            <div>
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-semibold text-sm group-hover:text-primary transition-colors">
                  {art.title}
                </h3>
                <span className="rounded bg-muted px-2 py-0.5 font-mono text-[10px] text-muted-foreground shrink-0">
                  key: {art.key}
                </span>
              </div>

              <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed mb-4">
                {art.content}
              </p>
            </div>

            <div className="flex items-center justify-between border-t border-border/50 pt-3 text-[11px] text-muted-foreground">
              <div className="flex flex-wrap gap-1.5">
                {art.tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 rounded-md bg-accent/60 px-2 py-0.5 text-[10px] font-medium text-accent-foreground"
                  >
                    <Tag className="h-2.5 w-2.5" /> {tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center gap-1 shrink-0 ml-2">
                <Clock className="h-3 w-3" />
                <span>Updated {formatDateSeparator(art.updated_at)}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Editor Modal */}
      {editingArticle && (
        <KbEditor
          article={editingArticle}
          onClose={() => setEditingArticle(null)}
        />
      )}
    </div>
  );
};
