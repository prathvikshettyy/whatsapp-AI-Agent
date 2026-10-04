import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { StaffRole } from "../api/types";
import { useAuth } from "./useAuth";

interface RequireAuthProps {
  children: React.ReactNode;
  requiredRole?: StaffRole;
}

export const RequireAuth: React.FC<RequireAuthProps> = ({ children, requiredRole }) => {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent" />
          <p className="text-sm text-muted-foreground font-medium">Authenticating staff session...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user.role !== requiredRole && user.role !== "admin") {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-4 bg-background p-6 text-center">
        <div className="rounded-full bg-destructive/10 p-4 text-destructive">
          <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-bold">Access Restricted</h2>
        <p className="max-w-md text-sm text-muted-foreground">
          You need <strong>{requiredRole}</strong> permissions to access this management console. Your current role is <strong>{user.role}</strong>.
        </p>
        <a
          href="/inbox"
          className="mt-2 rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700"
        >
          Return to Inbox
        </a>
      </div>
    );
  }

  return <>{children}</>;
};
