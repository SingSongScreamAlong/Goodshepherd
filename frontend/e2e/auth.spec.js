// @ts-check
const { test, expect } = require('@playwright/test');

/**
 * E2E tests for authentication flows
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    // Clear any stored auth data
    await page.goto('/');
    await page.evaluate(() => {
      localStorage.clear();
    });
    await page.reload();
  });

  test.describe('Sign In Modal', () => {
    test('should open sign in modal when clicking Sign In button', async ({ page }) => {
      await page.goto('/');
      
      // Click sign in button
      await page.click('.App-signin-button');
      
      // Modal should be visible
      await expect(page.locator('.auth-modal')).toBeVisible();
      await expect(page.locator('.auth-form-container h2')).toHaveText('Sign In');
    });

    test('should close modal when clicking X button', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Close modal
      await page.click('.auth-modal-close');
      
      // Modal should be hidden
      await expect(page.locator('.auth-modal')).not.toBeVisible();
    });

    test('should close modal when pressing Escape', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Press Escape
      await page.keyboard.press('Escape');
      
      // Modal should be hidden
      await expect(page.locator('.auth-modal')).not.toBeVisible();
    });

    test('should switch to register form', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Click create account button
      await page.click('button:has-text("Create Account")');
      
      // Should show register form
      await expect(page.locator('.auth-form-container h2')).toHaveText('Create Account');
    });

    test('should switch to forgot password form', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Click forgot password link
      await page.click('button:has-text("Forgot password?")');
      
      // Should show forgot password form
      await expect(page.locator('.auth-form-container h2')).toHaveText('Reset Password');
    });
  });

  test.describe('Login Form Validation', () => {
    test('should show error for empty fields', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Try to submit empty form
      await page.click('button[type="submit"]:has-text("Sign In")');
      
      // Should show validation error (HTML5 validation)
      const emailInput = page.locator('#login-email');
      await expect(emailInput).toHaveAttribute('required', '');
    });

    test('should show error for invalid credentials', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      
      // Fill in invalid credentials
      await page.fill('#login-email', 'invalid@example.com');
      await page.fill('#login-password', 'wrongpassword');
      
      // Submit form
      await page.click('button[type="submit"]:has-text("Sign In")');
      
      // Should show error message
      await expect(page.locator('.auth-error')).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Registration Form', () => {
    test('should validate password length', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      await page.click('button:has-text("Create Account")');
      
      // Fill form with short password
      await page.fill('#register-email', 'test@example.com');
      await page.fill('#register-password', 'short');
      await page.fill('#register-confirm', 'short');
      
      // Submit
      await page.click('button[type="submit"]:has-text("Create Account")');
      
      // Should show password length error
      await expect(page.locator('.auth-error')).toContainText('8 characters');
    });

    test('should validate password confirmation', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      await page.click('button:has-text("Create Account")');
      
      // Fill form with mismatched passwords
      await page.fill('#register-email', 'test@example.com');
      await page.fill('#register-password', 'password123');
      await page.fill('#register-confirm', 'password456');
      
      // Submit
      await page.click('button[type="submit"]:has-text("Create Account")');
      
      // Should show mismatch error
      await expect(page.locator('.auth-error')).toContainText('do not match');
    });

    test('should switch back to login form', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      await page.click('button:has-text("Create Account")');
      
      // Click sign in button
      await page.click('button:has-text("Sign In")');
      
      // Should show login form
      await expect(page.locator('.auth-form-container h2')).toHaveText('Sign In');
    });
  });

  test.describe('Forgot Password Form', () => {
    test('should show success message after submitting', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      await page.click('button:has-text("Forgot password?")');
      
      // Fill email
      await page.fill('#reset-email', 'test@example.com');
      
      // Submit
      await page.click('button[type="submit"]:has-text("Send Reset Link")');
      
      // Should show success message (API returns success even for non-existent emails)
      await expect(page.locator('.auth-success-icon')).toBeVisible({ timeout: 5000 });
      await expect(page.locator('h2')).toHaveText('Check Your Email');
    });

    test('should go back to login form', async ({ page }) => {
      await page.goto('/');
      await page.click('.App-signin-button');
      await page.click('button:has-text("Forgot password?")');
      
      // Click back button
      await page.click('button:has-text("Back to Sign In")');
      
      // Should show login form
      await expect(page.locator('.auth-form-container h2')).toHaveText('Sign In');
    });
  });

  test.describe('Authenticated State', () => {
    test.skip('should show user menu when authenticated', async ({ page }) => {
      // This test requires a valid user account
      // Skip for now as it requires backend setup
      await page.goto('/');
      
      // Set mock auth data
      await page.evaluate(() => {
        localStorage.setItem('gs_access_token', 'mock_token');
        localStorage.setItem('gs_user', JSON.stringify({
          id: '123',
          email: 'test@example.com',
          name: 'Test User',
          roles: ['user'],
        }));
      });
      
      await page.reload();
      
      // Should show user menu instead of sign in button
      await expect(page.locator('.user-menu')).toBeVisible();
      await expect(page.locator('.App-signin-button')).not.toBeVisible();
    });
  });
});

test.describe('URL-based Auth Flows', () => {
  test('should open reset password modal from URL', async ({ page }) => {
    await page.goto('/?action=reset-password&token=test-token');
    
    // Should show reset password form
    await expect(page.locator('.auth-modal')).toBeVisible();
    await expect(page.locator('.auth-form-container h2')).toHaveText('Set New Password');
  });

  test('should open email verification from URL', async ({ page }) => {
    await page.goto('/?action=verify-email&token=test-token');
    
    // Should show verification in progress or result
    await expect(page.locator('.auth-modal')).toBeVisible();
  });

  test('should clean URL after processing auth action', async ({ page }) => {
    await page.goto('/?action=reset-password&token=test-token');
    
    // Wait for URL to be cleaned
    await page.waitForFunction(() => {
      return !window.location.search.includes('token');
    });
    
    // URL should be clean
    expect(page.url()).not.toContain('token');
  });
});
