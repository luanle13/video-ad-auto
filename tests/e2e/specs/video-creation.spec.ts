import { test, expect } from '@playwright/test';

test.describe('Video Creation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure user is logged in before starting the test
    await page.goto('/login');
    await page.locator('#email').fill('test@example.com');
    await page.locator('#password').fill('password123');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await expect(page).toHaveURL(/\/dashboard$/);
  });

  test('test_create_product_and_video', async ({ page }) => {
    // Navigate to create video page
    await page.getByRole('button', { name: 'Create Video' }).click();
    await expect(page).toHaveURL(/\/videos\/new$/);

    // Fill in product details
    await page.locator('#title').fill('Test Product');
    await page.locator('#description').fill('This is a test product description');
    await page.locator('#price').fill('29.99');

    // Upload product image
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./test-assets/product-image.jpg');

    // Submit the form
    await page.getByRole('button', { name: 'Generate Video' }).click();

    // Verify video creation process started
    await expect(page.getByText('Video generation in progress')).toBeVisible();
    
    // Wait for video to be processed (this might take some time)
    await page.waitForTimeout(10000); // Wait 10 seconds for processing
    
    // Verify video was created successfully
    await expect(page.getByText('Video Ready')).toBeVisible();
  });

  test('test_view_video_preview', async ({ page }) => {
    // Navigate to dashboard to see existing videos
    await page.goto('/dashboard');
    
    // Find and click on a video preview
    const videoCard = page.locator('.video-card').first();
    await videoCard.click();
    
    // Verify video preview page loads
    await expect(page).toHaveURL(/\/videos\/[a-zA-Z0-9-]+$/);
    await expect(page.locator('video')).toBeVisible();
    
    // Verify video controls are available
    await expect(page.getByRole('button', { name: 'Play' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Download' })).toBeVisible();
  });
});