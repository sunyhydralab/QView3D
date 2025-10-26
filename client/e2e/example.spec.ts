import { test, expect } from '@playwright/test'

test.describe('QView3D Application', () => {
  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/')

    // Wait for the page to be fully loaded
    await page.waitForLoadState('networkidle')

    // Check that we're on the dashboard (home page)
    await expect(page).toHaveURL('/')

    // Verify the page title or main heading exists
    await expect(page.locator('body')).toBeVisible()
  })

  test('can navigate to dashboard', async ({ page }) => {
    await page.goto('/')

    // Wait for navigation to be ready
    await page.waitForLoadState('networkidle')

    // Look for dashboard navigation link or verify we're already on dashboard
    const dashboardLink = page.locator('a[href="/"]').first()

    if (await dashboardLink.isVisible()) {
      await dashboardLink.click()
    }

    // Verify we're on the dashboard
    await expect(page).toHaveURL('/')
  })

  test('can view job history', async ({ page }) => {
    await page.goto('/')

    // Navigate to job history page
    await page.goto('/history')

    // Wait for the page to load
    await page.waitForLoadState('networkidle')

    // Verify we're on the history page
    await expect(page).toHaveURL('/history')

    // Verify the page content is visible
    await expect(page.locator('body')).toBeVisible()
  })

  test('application starts and is accessible', async ({ page }) => {
    // Simple smoke test to verify the app is running
    const response = await page.goto('/')

    // Check that the response is successful
    expect(response?.status()).toBe(200)

    // Verify the page has loaded
    await expect(page.locator('body')).toBeVisible()

    // Check that the page has some content
    const bodyText = await page.locator('body').textContent()
    expect(bodyText).toBeTruthy()
  })
})
