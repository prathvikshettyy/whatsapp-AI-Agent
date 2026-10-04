import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { RequireAuth } from "./auth/RequireAuth";
import { AppShell } from "./components/AppShell";
import { LoginPage } from "./features/auth/LoginPage";
import { InboxPage } from "./features/inbox/InboxPage";
import { KbPage } from "./features/kb/KbPage";
import { SettingsPage } from "./features/settings/SettingsPage";
import { ToolsPage } from "./features/tools/ToolsPage";
import { AnalyticsPage } from "./features/analytics/AnalyticsPage";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        path="/inbox"
        element={
          <RequireAuth>
            <AppShell>
              <InboxPage />
            </AppShell>
          </RequireAuth>
        }
      />

      <Route
        path="/kb"
        element={
          <RequireAuth>
            <AppShell>
              <KbPage />
            </AppShell>
          </RequireAuth>
        }
      />

      <Route
        path="/settings"
        element={
          <RequireAuth requiredRole="admin">
            <AppShell>
              <SettingsPage />
            </AppShell>
          </RequireAuth>
        }
      />

      <Route
        path="/tools"
        element={
          <RequireAuth>
            <AppShell>
              <ToolsPage />
            </AppShell>
          </RequireAuth>
        }
      />

      <Route
        path="/analytics"
        element={
          <RequireAuth>
            <AppShell>
              <AnalyticsPage />
            </AppShell>
          </RequireAuth>
        }
      />

      <Route path="/" element={<Navigate to="/inbox" replace />} />
      <Route path="*" element={<Navigate to="/inbox" replace />} />
    </Routes>
  );
};
