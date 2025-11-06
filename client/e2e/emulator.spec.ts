import { test, expect } from '@playwright/test'

test.describe('Emulator Workflow', () => {
  // Enable debug mode before each test
  test.beforeEach(async ({ page }) => {
    // Navigate to homepage first to set localStorage
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // Set debug mode in localStorage (required to access emulator page)
    await page.evaluate(() => {
      localStorage.setItem('debugMode', 'true')
    })
  })

  test('can navigate to emulator page (/emulator)', async ({ page }) => {
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Verify we're on the emulator page
    await expect(page).toHaveURL('/emulator')

    // Verify the page heading is visible
    await expect(page.getByText('Virtual Emulator')).toBeVisible()

    // Verify subtitle is present
    await expect(page.getByText('Test the system without physical hardware')).toBeVisible()
  })

  test('can see emulator form and input fields', async ({ page }) => {
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Verify the emulator name input is visible
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await expect(nameInput).toBeVisible()

    // Verify the input has default value
    await expect(nameInput).toHaveValue('Virtual Printer')

    // Verify the start button is visible
    const startButton = page.getByRole('button', { name: /start emulator/i })
    await expect(startButton).toBeVisible()
    await expect(startButton).toBeEnabled()

    // Verify status section shows "Inactive"
    await expect(page.getByText('Status')).toBeVisible()
    await expect(page.getByText('Inactive')).toBeVisible()
  })

  test('can enter emulator name', async ({ page }) => {
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Find the emulator name input
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await expect(nameInput).toBeVisible()

    // Clear the default value and enter a custom name
    await nameInput.clear()
    await nameInput.fill('Test Emulator E2E')

    // Verify the value was set correctly
    await expect(nameInput).toHaveValue('Test Emulator E2E')
  })

  test('can click start emulator button', async ({ page }) => {
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Enter emulator name
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await nameInput.clear()
    await nameInput.fill('Test Emulator Button Click')

    // Find and click the start button
    const startButton = page.getByRole('button', { name: /start emulator/i })
    await expect(startButton).toBeEnabled()
    await startButton.click()

    // Wait for the button to show loading state
    await expect(page.getByRole('button', { name: /starting/i })).toBeVisible({ timeout: 2000 })
  })

  test('success notification appears', async ({ page }) => {
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Enter emulator name
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await nameInput.clear()
    await nameInput.fill('Test Emulator Success')

    // Click the start button
    const startButton = page.getByRole('button', { name: /start emulator/i })
    await startButton.click()

    // Wait for success toast notification
    // Based on EmulatorView.vue line 41: addToast(`${emulatorName.value} started successfully`, 'success')
    const successToast = page.locator('.toast-notification').filter({
      hasText: /started successfully/i
    })

    // Toast should appear within 10 seconds
    await expect(successToast).toBeVisible({ timeout: 10000 })

    // Verify the status changed to "Active"
    await expect(page.getByText('Active')).toBeVisible({ timeout: 5000 })
  })

  test('navigate to dashboard and verify emulator appears in printer list', async ({ page }) => {
    const emulatorName = 'Test Emulator Dashboard'

    // Step 1: Start the emulator
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Enter emulator name
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await nameInput.clear()
    await nameInput.fill(emulatorName)

    // Click start button
    const startButton = page.getByRole('button', { name: /start emulator/i })
    await startButton.click()

    // Wait for success notification
    const successToast = page.locator('.toast-notification').filter({
      hasText: /started successfully/i
    })
    await expect(successToast).toBeVisible({ timeout: 10000 })

    // Wait for the Dashboard button to appear (only visible when emulator is active)
    const dashboardButton = page.getByRole('button', { name: /dashboard/i })
    await expect(dashboardButton).toBeVisible({ timeout: 5000 })

    // Step 2: Navigate to dashboard
    await dashboardButton.click()
    await page.waitForURL('/')
    await expect(page).toHaveURL('/')
    await page.waitForLoadState('networkidle')

    // Step 3: Verify emulator appears in printer list
    // The Dashboard.vue shows printer names in table cells (line 197)
    // Look for the emulator name in the table
    const printerNameElement = page.locator('td').filter({
      hasText: emulatorName
    }).first()

    // Give it some time to appear in the list
    await expect(printerNameElement).toBeVisible({ timeout: 10000 })
  })

  test('complete emulator workflow - start, verify, and navigate', async ({ page }) => {
    const emulatorName = 'Complete Workflow Test'

    // Step 1: Navigate to emulator page
    await page.goto('/emulator')
    await page.waitForLoadState('networkidle')

    // Verify we're on the correct page
    await expect(page.getByText('Virtual Emulator')).toBeVisible()

    // Step 2: Enter emulator name
    const nameInput = page.getByPlaceholder('Enter a name for the virtual printer')
    await nameInput.clear()
    await nameInput.fill(emulatorName)
    await expect(nameInput).toHaveValue(emulatorName)

    // Step 3: Start the emulator
    const startButton = page.getByRole('button', { name: /start emulator/i })
    await expect(startButton).toBeEnabled()
    await startButton.click()

    // Step 4: Verify success notification
    const successToast = page.locator('.toast-notification').filter({
      hasText: /started successfully/i
    })
    await expect(successToast).toBeVisible({ timeout: 10000 })

    // Step 5: Verify status changed to Active
    await expect(page.getByText('Active')).toBeVisible()

    // Step 6: Verify Dashboard button appears and Stop button is visible
    const dashboardButton = page.getByRole('button', { name: /dashboard/i })
    await expect(dashboardButton).toBeVisible()

    const stopButton = page.getByRole('button', { name: /stop emulator/i })
    await expect(stopButton).toBeVisible()

    // Step 7: Navigate to dashboard
    await dashboardButton.click()
    await page.waitForURL('/')

    // Step 8: Verify emulator is listed on dashboard
    await page.waitForLoadState('networkidle')
    const printerNameElement = page.locator('td').filter({
      hasText: emulatorName
    }).first()
    await expect(printerNameElement).toBeVisible({ timeout: 10000 })
  })
})
