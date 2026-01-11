import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('test_login_flow', async ({ page }) => {
    // Navigate to login page
    await page.getByRole('link', { name: 'Login' }).click();
    await expect(page).toHaveURL(/\/login$/);

    // Fill in login credentials
    await page.locator('#email').fill('test@example.com');
    await page.locator('#password').fill('password123');

    // Submit the form
    await page.getByRole('button', { name: 'Sign in' }).click();

    // Verify successful login and redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText('Dashboard')).toBeVisible();
  });

  test('test_register_flow', async ({ page }) => {
    // Navigate to register page
    await page.getByRole('link', { name: 'Sign up' }).click();
    await expect(page).toHaveURL(/\/register$/);

    // Fill in registration details
    await page.locator('#email').fill('newuser@example.com');
    await page.locator('#password').fill('password123');
    await page.locator('#confirmPassword').fill('password123');

    // Submit the form
    await page.getByRole('button', { name: 'Sign up' }).click();

    // Verify successful registration and redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard$/);
    await expect(page.getByText('Dashboard')).toBeVisible();
  });

  test('test_logout_flow', async ({ page }) => {
    // First, ensure we're logged in by navigating to dashboard
    await page.goto('/dashboard');
    
    // Click on user profile menu or logout button
    await page.getByRole('button', { name: 'Logout' }).click();
    
    // Verify logout and redirect to login page
    await expect(page).toHaveURL(/\/login$/);
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
  });
});