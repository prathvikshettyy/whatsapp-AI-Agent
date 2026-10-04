import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function maskPhoneNumber(phone?: string): string {
  if (!phone) return "Unknown";
  const cleaned = phone.replace(/[^\d+]/g, "");
  if (cleaned.length <= 6) return "****";
  // Format as +XX ••••• XXXX
  const prefix = cleaned.slice(0, 3);
  const suffix = cleaned.slice(-4);
  return `${prefix} ••••• ${suffix}`;
}

export function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function formatDateSeparator(isoString: string): string {
  try {
    const date = new Date(isoString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) return "Today";
    if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
    return date.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
  } catch {
    return isoString;
  }
}

export function formatRelative(isoString: string): string {
  try {
    const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  } catch {
    return "";
  }
}

export function getHoursRemainingIn24hWindow(lastUserMsgIso: string): number {
  try {
    const lastMsgTime = new Date(lastUserMsgIso).getTime();
    const diffMs = Date.now() - lastMsgTime;
    const windowMs = 24 * 60 * 60 * 1000;
    const remainingMs = windowMs - diffMs;
    return remainingMs / (1000 * 60 * 60);
  } catch {
    return 0;
  }
}
