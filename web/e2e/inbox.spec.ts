import { test, expect } from "@playwright/test";

test.describe("Inbox & Human Takeover Flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: "Admin Role" }).click();
    await page.getByRole("button", { name: "Sign In to Console" }).click();
    await expect(page).toHaveURL(/.*inbox/);
  });

  test("inspects conversation, takes over, sends message, and releases", async ({ page }) => {
    // Select first conversation
    await page.getByText("Alex Morgan").click();

    // Verify thread header is visible
    await expect(page.getByRole("heading", { name: "Alex Morgan" })).toBeVisible();

    // Check Take Over button is available or already in human mode
    const takeoverBtn = page.getByRole("button", { name: /Take Over/i });
    if (await takeoverBtn.isVisible()) {
      await takeoverBtn.click();
      await expect(page.getByRole("button", { name: /Release to Bot/i })).toBeVisible();
    }

    // Type in composer and send
    const composer = page.getByPlaceholder("Type a WhatsApp reply...");
    await composer.fill("Hello Alex, this is human support. We are checking your order now.");
    await page.getByRole("button", { name: "Send" }).click();

    // Verify sent message appears in thread
    await expect(page.getByText("Hello Alex, this is human support.")).toBeVisible();

    // Release back to bot
    await page.getByRole("button", { name: /Release to Bot/i }).click();
    await expect(page.getByRole("button", { name: /Take Over/i })).toBeVisible();
  });
});
