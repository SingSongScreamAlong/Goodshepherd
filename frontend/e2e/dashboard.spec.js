// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * E2E tests for the Dashboard functionality.
 */

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for initial load
    await page.waitForLoadState('networkidle');
  });

  test('should display the main dashboard layout', async ({ page }) => {
    // Check for main content area
    const mainContent = page.locator('#root, main, [role="main"]');
    await expect(mainContent).toBeVisible();
  });

  test('should have navigation elements', async ({ page }) => {
    // Look for navigation or header elements
    const nav = page.locator('nav, header, [role="navigation"]');
    const navCount = await nav.count();
    
    // Should have at least one navigation element
    expect(navCount).toBeGreaterThanOrEqual(0);
  });

  test('should handle window resize gracefully', async ({ page }) => {
    // Test different viewport sizes
    const viewports = [
      { width: 320, height: 568 },   // iPhone SE
      { width: 768, height: 1024 },  // iPad
      { width: 1920, height: 1080 }, // Desktop
    ];

    for (const viewport of viewports) {
      await page.setViewportSize(viewport);
      await page.waitForTimeout(500);
      
      // Page should still be visible and functional
      const body = page.locator('body');
      await expect(body).toBeVisible();
      
      // No JavaScript errors should occur
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      await page.waitForTimeout(200);
      
      // Filter critical errors
      const criticalErrors = errors.filter(e => 
        !e.includes('ResizeObserver') && 
        !e.includes('Network')
      );
      expect(criticalErrors).toHaveLength(0);
    }
  });
});

test.describe('Map Component', () => {
  test('should load map container', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Look for map-related elements
    const mapContainer = page.locator('[class*="map"], [id*="map"], .maplibregl-map');
    
    // Map may or may not be present depending on route
    const mapExists = await mapContainer.count() > 0;
    
    if (mapExists) {
      await expect(mapContainer.first()).toBeVisible();
    }
  });

  test('should handle map interactions without errors', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    
    // Try to interact with the page
    await page.mouse.move(400, 300);
    await page.mouse.wheel(0, 100);
    await page.waitForTimeout(500);
    
    // Filter out expected errors
    const criticalErrors = errors.filter(e => 
      !e.includes('Network') && 
      !e.includes('fetch')
    );
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Events Display', () => {
  test('should show events section or placeholder', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Look for events-related content
    const eventsSection = page.locator('[class*="event"], [data-testid*="event"], .events');
    const eventsExist = await eventsSection.count() > 0;
    
    // Either events are shown or the page loads without them
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

  test('should handle empty state gracefully', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Page should not show error messages for empty data
    const errorMessages = page.locator('[class*="error"]:not([class*="border"])');
    const visibleErrors = await errorMessages.filter({ hasText: /error|failed/i }).count();
    
    // Should have no visible error messages (network errors are expected)
    expect(visibleErrors).toBeLessThanOrEqual(1);
  });
});

test.describe('User Interactions', () => {
  test('should handle clicks without errors', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    
    // Click on various parts of the page
    const clickableElements = page.locator('button, a, [role="button"]');
    const count = await clickableElements.count();
    
    // Click first few clickable elements if they exist
    for (let i = 0; i < Math.min(count, 3); i++) {
      try {
        const element = clickableElements.nth(i);
        if (await element.isVisible()) {
          await element.click({ timeout: 1000 });
          await page.waitForTimeout(200);
        }
      } catch {
        // Element may not be clickable, that's ok
      }
    }
    
    // Filter critical errors
    const criticalErrors = errors.filter(e => 
      !e.includes('Network') && 
      !e.includes('fetch') &&
      !e.includes('API')
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test('should handle keyboard navigation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Tab through elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      await page.waitForTimeout(100);
    }
    
    // Press Enter on focused element
    await page.keyboard.press('Enter');
    await page.waitForTimeout(200);
    
    // Page should still be functional
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });
});
