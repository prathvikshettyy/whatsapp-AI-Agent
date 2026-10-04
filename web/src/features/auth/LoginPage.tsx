import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { MessageSquare, Lock, Mail, ShieldCheck, ArrowRight } from "lucide-react";
import { useAuth } from "../../auth/useAuth";
import { Button } from "../../components/Button";
import { Input } from "../../components/Input";
import { useToast } from "../../components/Toast";

const loginSchema = z.object({
  email: z.string().email("Please enter a valid email address"),
  password: z.string().min(6, "Password must be at least 6 characters"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  const from = (location.state as any)?.from?.pathname || "/inbox";

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "admin@company.com",
      password: "password123",
    },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setLoading(true);
    try {
      await login(data.email, data.password);
      toast({
        title: "Welcome back!",
        description: `Logged in as ${data.email}`,
        variant: "success",
      });
      navigate(from, { replace: true });
    } catch (err: any) {
      toast({
        title: "Authentication Failed",
        description: err.message || "Invalid credentials",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (role: "admin" | "agent") => {
    if (role === "admin") {
      setValue("email", "admin@company.com");
    } else {
      setValue("email", "agent.alex@company.com");
    }
    setValue("password", "password123");
  };

  return (
    <div className="flex min-h-screen w-screen items-center justify-center bg-gradient-to-br from-background via-muted/30 to-emerald-950/20 p-4">
      <div className="w-full max-w-md space-y-6 rounded-3xl border border-border/80 bg-card/90 p-8 shadow-2xl backdrop-blur-xl">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-[#128C7E] to-[#25D366] text-white shadow-lg shadow-[#25D366]/25 mb-3">
            <MessageSquare className="h-7 w-7" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight">Staff Support Console</h2>
          <p className="text-xs text-muted-foreground mt-1 max-w-xs">
            Sign in to manage live customer WhatsApp chats, review Claude tool executions, and configure bot rules.
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-foreground">Work Email</label>
            <div className="relative mt-1">
              <Mail className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                {...register("email")}
                type="email"
                placeholder="you@company.com"
                className="pl-9"
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-xs text-destructive">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label className="text-xs font-semibold text-foreground">Password</label>
            <div className="relative mt-1">
              <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                {...register("password")}
                type="password"
                placeholder="••••••••"
                className="pl-9"
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-destructive">{errors.password.message}</p>
            )}
          </div>

          <Button
            type="submit"
            loading={loading}
            className="w-full bg-[#128C7E] hover:bg-[#0e6f64] text-white font-semibold h-10 gap-2 shadow-md"
          >
            <span>Sign In to Console</span>
            <ArrowRight className="h-4 w-4" />
          </Button>
        </form>

        {/* Demo Quick Logins */}
        <div className="pt-2 border-t border-border">
          <p className="text-[11px] text-center text-muted-foreground mb-2">
            Demo quick switch:
          </p>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("admin")}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-border bg-background/50 p-2 text-xs font-medium hover:bg-accent hover:border-primary/50 transition-colors"
            >
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" />
              <span>Admin Role</span>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("agent")}
              className="flex items-center justify-center gap-1.5 rounded-xl border border-border bg-background/50 p-2 text-xs font-medium hover:bg-accent hover:border-primary/50 transition-colors"
            >
              <MessageSquare className="h-3.5 w-3.5 text-amber-500" />
              <span>Agent Role</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
