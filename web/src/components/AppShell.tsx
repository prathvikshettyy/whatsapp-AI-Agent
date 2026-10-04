import React, { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Inbox,
  BookOpen,
  Settings as SettingsIcon,
  BarChart3,
  Wrench,
  LogOut,
  Moon,
  Sun,
  Shield,
  Menu,
  X,
  MessageSquare,
} from "lucide-react";
import { useAuth } from "../auth/useAuth";
import { useConversations } from "../api/conversations";
import { useSSE } from "../hooks/useSSE";
import { useToast } from "./Toast";
import { cn } from "../lib/utils";

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const { toast } = useToast();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(() => document.documentElement.classList.contains("dark"));

  // Fetch conversations count to badge human-attention conversations
  const { data: conversations } = useConversations();
  const needsHumanCount = conversations?.filter((c) => c.status === "human").length || 0;

  // Listen to SSE live events
  useSSE((convo) => {
    toast({
      title: "🚨 Human Agent Requested",
      description: `${convo.name || convo.wa_id_masked}: ${convo.last_message_preview}`,
      variant: "warning",
    });
  });

  const toggleDarkMode = () => {
    if (darkMode) {
      document.documentElement.classList.remove("dark");
      setDarkMode(false);
    } else {
      document.documentElement.classList.add("dark");
      setDarkMode(true);
    }
  };

  const navItems = [
    {
      label: "Inbox",
      path: "/inbox",
      icon: Inbox,
      badge: needsHumanCount > 0 ? needsHumanCount : undefined,
      badgeColor: "bg-amber-500 text-white",
    },
    {
      label: "Knowledge Base",
      path: "/kb",
      icon: BookOpen,
    },
    {
      label: "Prompt & Rules",
      path: "/settings",
      icon: SettingsIcon,
      adminOnly: true,
    },
    {
      label: "Tool Logs",
      path: "/tools",
      icon: Wrench,
    },
    {
      label: "Analytics",
      path: "/analytics",
      icon: BarChart3,
    },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background text-foreground">
      {/* Sidebar Desktop */}
      <aside className="hidden md:flex w-64 flex-col border-r border-border bg-card/60 backdrop-blur-md">
        {/* Brand header */}
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-[#128C7E] to-[#25D366] text-white shadow-md shadow-[#25D366]/20">
            <MessageSquare className="h-5 w-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight flex items-center gap-1.5">
              WhatsApp AI <span className="rounded bg-emerald-500/10 px-1 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">Desk</span>
            </h1>
            <p className="text-[11px] text-muted-foreground font-mono">Cloud API Live</p>
          </div>
        </div>

        {/* Navigation items */}
        <nav className="flex-1 space-y-1.5 p-3 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname.startsWith(item.path);
            const isRestricted = item.adminOnly && user?.role !== "admin";

            if (isRestricted) return null;

            const Icon = item.icon;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-all group",
                  isActive
                    ? "bg-primary/10 text-primary font-semibold shadow-xs"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )}
              >
                <div className="flex items-center gap-3">
                  <Icon className={cn("h-4 w-4 transition-colors", isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground")} />
                  <span>{item.label}</span>
                </div>
                {item.badge !== undefined && (
                  <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-bold shadow-xs", item.badgeColor)}>
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* User profile & controls */}
        <div className="border-t border-border p-3 space-y-2 bg-card/80">
          <div className="flex items-center justify-between rounded-lg bg-accent/40 p-2.5">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-700/20 text-emerald-600 font-bold text-xs uppercase">
                {user?.name?.slice(0, 2) || "AD"}
              </div>
              <div className="truncate">
                <p className="truncate text-xs font-semibold">{user?.name || "Support Staff"}</p>
                <div className="flex items-center gap-1 text-[10px] text-muted-foreground">
                  <Shield className="h-3 w-3 text-emerald-500" />
                  <span className="capitalize">{user?.role || "Staff"}</span>
                </div>
              </div>
            </div>

            <button
              onClick={toggleDarkMode}
              className="rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
              title="Toggle theme"
            >
              {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
          </div>

          <button
            onClick={() => logout()}
            className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-destructive hover:bg-destructive/10 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Mobile Header */}
        <header className="flex h-14 items-center justify-between border-b border-border bg-card px-4 md:hidden">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="rounded-md p-1.5 hover:bg-accent"
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
            <span className="font-bold text-sm">WhatsApp AI Desk</span>
          </div>
          <button onClick={toggleDarkMode} className="rounded-md p-1.5 text-muted-foreground">
            {darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>
        </header>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="fixed inset-0 top-14 z-40 bg-background/95 backdrop-blur-md md:hidden p-4">
            <nav className="space-y-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center justify-between rounded-lg p-3 text-base font-medium hover:bg-accent"
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5" />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className="rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              })}
              <button
                onClick={() => logout()}
                className="flex w-full items-center gap-3 rounded-lg p-3 text-base text-destructive hover:bg-destructive/10"
              >
                <LogOut className="h-5 w-5" />
                <span>Sign out</span>
              </button>
            </nav>
          </div>
        )}

        {/* Route view container */}
        <main className="flex-1 overflow-hidden relative">
          {children}
        </main>
      </div>
    </div>
  );
};
