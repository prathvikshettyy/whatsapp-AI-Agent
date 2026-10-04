import { describe, it, expect } from "vitest";
import { maskPhoneNumber, getHoursRemainingIn24hWindow, formatDateSeparator } from "../lib/utils";
import { ApiError } from "../api/client";

describe("Frontend Utilities & 24h Window", () => {
  it("masks phone numbers properly to protect PII", () => {
    expect(maskPhoneNumber("+15552348921")).toBe("+15 ••••• 8921");
    expect(maskPhoneNumber("15559876543")).toBe("155 ••••• 6543");
    expect(maskPhoneNumber("")).toBe("Unknown");
  });

  it("calculates 24-hour window countdown accurately", () => {
    // 2 hours ago: ~22 hours remaining
    const twoHoursAgo = new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString();
    const remaining = getHoursRemainingIn24hWindow(twoHoursAgo);
    expect(remaining).toBeGreaterThan(21.9);
    expect(remaining).toBeLessThan(22.1);

    // 25 hours ago: window expired (<= 0)
    const twentyFiveHoursAgo = new Date(Date.now() - 25 * 60 * 60 * 1000).toISOString();
    expect(getHoursRemainingIn24hWindow(twentyFiveHoursAgo)).toBeLessThanOrEqual(0);
  });

  it("formats date separators for chat messages correctly", () => {
    const today = new Date().toISOString();
    expect(formatDateSeparator(today)).toBe("Today");

    const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
    expect(formatDateSeparator(yesterday)).toBe("Yesterday");
  });

  it("handles ApiError properly with status and custom data", () => {
    const err = new ApiError(403, "Access restricted", { code: "FORBIDDEN" });
    expect(err.status).toBe(403);
    expect(err.message).toBe("Access restricted");
    expect(err.data).toEqual({ code: "FORBIDDEN" });
  });
});
