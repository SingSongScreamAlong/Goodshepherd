// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * E2E tests for Good Shepherd application.
 */

test.describe('Application', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the app to load
    await expect(page.locator('body')).toBeVisible();
    
    // Check that the page has loaded (not showing error)
    const pageContent = await page.textContent('body');
    expect(pageContent).not.toContain('Cannot GET');
  });

  test('should have a title', async ({ page }) => {
    await page.goto('/');
    
    // Check page title contains app name
    await expect(page).toHaveTitle(/Good Shepherd|React/);
  });

  test('should be responsive', async ({ page }) => {
    await page.goto('/');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('body')).toBeVisible();
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.locator('body')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Navigation', () => {
  test('should navigate without errors', async ({ page }) => {
    await page.goto('/');
    
    // Check for console errors
    const errors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Wait for page to stabilize
    await page.waitForTimeout(2000);
    
    // Filter out expected errors (like missing API)
    const criticalErrors = errors.filter(e => 
      !e.includes('Failed to fetch') && 
      !e.includes('Network') &&
      !e.includes('API')
    );
    
    expect(criticalErrors).toHaveLength(0);
  });
});

test.describe('Accessibility', () => {
  test('should have proper document structure', async ({ page }) => {
    await page.goto('/');
    
    // Check for main landmark
    const main = page.locator('main, [role="main"], #root');
    await expect(main).toBeVisible();
  });

  test('should have no duplicate IDs', async ({ page }) => {
    await page.goto('/');
    
    // Check for duplicate IDs
    const duplicateIds = await page.evaluate(() => {
      const ids = Array.from(document.querySelectorAll('[id]')).map(el => el.id);
      const duplicates = ids.filter((id, index) => ids.indexOf(id) !== index);
      return duplicates;
    });
    
    expect(duplicateIds).toHaveLength(0);
  });
});

test.describe('Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);
  });

  test('should not have memory leaks on navigation', async ({ page }) => {
    await page.goto('/');
    
    // Get initial memory usage (if available)
    const initialMetrics = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize;
      }
      return null;
    });
    
    // Navigate multiple times
    for (let i = 0; i < 5; i++) {
      await page.goto('/');
      await page.waitForLoadState('networkidle');
    }
    
    // Check memory didn't grow excessively
    if (initialMetrics !== null) {
      const finalMetrics = await page.evaluate(() => {
        if (performance.memory) {
          return performance.memory.usedJSHeapSize;
        }
        return null;
      });
      
      if (finalMetrics !== null) {
        // Memory shouldn't grow more than 50%
        expect(finalMetrics).toBeLessThan(initialMetrics * 1.5);
      }
    }
  });
});
