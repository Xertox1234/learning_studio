const { test, expect } = require('@playwright/test');

test('navigate to home section', async ({ page }) => {
    await page.goto('http://localhost:3000'); // Replace with your forum URL
    await page.click('text=Home');
    await expect(page).toHaveURL('http://localhost:3000/home'); // Replace with expected URL
});

test('navigate to topics section', async ({ page }) => {
    await page.goto('http://localhost:3000'); // Replace with your forum URL
    await page.click('text=Topics');
    await expect(page).toHaveURL('http://localhost:3000/topics'); // Replace with expected URL
});

test('navigate to profile section', async ({ page }) => {
    await page.goto('http://localhost:3000'); // Replace with your forum URL
    await page.click('text=Profile');
    await expect(page).toHaveURL('http://localhost:3000/profile'); // Replace with expected URL
});