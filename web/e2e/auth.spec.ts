import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("redirects unauthenticated user to login", async ({ page }) => {
    await page.goto("/inbox");
    // Verify login heading is visible
    await expect(page.getByText("Staff Support Console")).toBeVisible();
  });

  test("allows admin to log in and access dashboard", async ({ page }) => {
    await page.goto("/login");

    // Click Admin quick switch demo button
    await page.getByRole("button", { name: "Admin Role" }).click();
    await page.getByRole("button", { name: "Sign In to Console" }).click();

    // Verify redirected to inbox
    await expect(page).toHaveURL(/.*inbox/);
    await expect(page.getByText("WhatsApp AI Desk")).toBeVisible();
  });
});
