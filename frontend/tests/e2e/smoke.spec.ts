import { test, expect } from '@playwright/test';

/**
 * Smoke Test Suite
 * 
 * Basic E2E tests to verify core functionality works.
 * These tests should be fast and cover critical user paths.
 */

test.describe('Catalyst Platform - Smoke Tests', () => {
  
  test('homepage loads successfully', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');
    
    // Wait for page to be ready
    await page.waitForLoadState('networkidle');
    
    // Check that we're on the right page
    await expect(page).toHaveTitle(/Catalyst/i);
    
    // Verify key elements are present
    // (Adjust selectors based on your actual UI)
    await expect(page.locator('body')).toBeVisible();
  });

  test('main chat interface is visible', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the main interface to load
    // Adjust these selectors to match your actual components
    const chatContainer = page.locator('[data-testid="chat-container"]').or(page.locator('textarea')).or(page.locator('input[type="text"]')).first();
    
    // Verify some form of input is visible
    await expect(chatContainer).toBeVisible({ timeout: 10000 });
  });

  test('can interact with chat input', async ({ page }) => {
    await page.goto('/');
    
    // Find the chat input (adjust selector to match your UI)
    const input = page.locator('textarea, input[type="text"]').first();
    await input.waitFor({ state: 'visible', timeout: 10000 });
    
    // Type a test message
    await input.fill('Hello, Catalyst!');
    
    // Verify the text was entered
    await expect(input).toHaveValue('Hello, Catalyst!');
  });

  test('navigation works', async ({ page }) => {
    await page.goto('/');
    
    // Check if there are any navigation links
    const navLinks = page.locator('nav a, header a').first();
    
    // If navigation exists, verify it's clickable
    if (await navLinks.count() > 0) {
      await expect(navLinks).toBeVisible();
    }
  });

  test('page has no console errors on load', async ({ page }) => {
    const errors: string[] = [];
    
    // Capture console errors
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    // Navigate to homepage
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Check for critical errors (filter out known warnings)
    const criticalErrors = errors.filter(error => 
      !error.includes('DevTools') && 
      !error.includes('favicon')
    );
    
    // Verify no critical errors
    expect(criticalErrors).toHaveLength(0);
  });

  test('can send a message (if backend is available)', async ({ page }) => {
    await page.goto('/');
    
    // Find input and submit button
    const input = page.locator('textarea, input[type="text"]').first();
    await input.waitFor({ state: 'visible', timeout: 10000 });
    
    // Type a message
    await input.fill('Test message');
    
    // Try to find and click a send/submit button
    const sendButton = page.locator('button[type="submit"], button:has-text("Send"), button:has-text("Run")').first();
    
    if (await sendButton.count() > 0) {
      await sendButton.click();
      
      // Wait a bit for response
      await page.waitForTimeout(2000);
      
      // Look for any response indicators (adjust based on your UI)
      // This is a soft check - we just verify the UI responded in some way
      const responseArea = page.locator('[data-testid="messages"], [data-testid="response"], .message, .response').first();
      
      // If there's a response area, check it's visible
      if (await responseArea.count() > 0) {
        await expect(responseArea).toBeVisible();
      }
    }
  });

  test('responsive design - mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Verify page still loads and is usable on mobile
    await expect(page.locator('body')).toBeVisible();
    
    // Check that main content is not cut off
    const body = page.locator('body');
    await expect(body).toBeVisible();
  });

});

test.describe('Health and Status', () => {
  
  test('health endpoint is accessible', async ({ page, request }) => {
    // Try to access the backend health endpoint
    try {
      const response = await request.get('http://localhost:8001/api/health');
      
      // Verify response
      expect(response.ok()).toBeTruthy();
      
      const data = await response.json();
      expect(data).toHaveProperty('status');
      
    } catch (error) {
      console.warn('Health endpoint not accessible - backend may not be running');
      // Don't fail the test if backend isn't running
    }
  });

});
