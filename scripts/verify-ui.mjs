import { spawn, spawnSync } from 'node:child_process';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import process from 'node:process';
import { chromium } from 'playwright';

const port = Number(process.env.UI_VERIFY_PORT ?? 5190);
const baseUrl = process.env.UI_VERIFY_BASE_URL ?? `http://127.0.0.1:${port}`;
const outputDir = path.resolve('artifacts/ui-verify');
const viewports = [
  { name: 'desktop', width: 1280, height: 720, isMobile: false },
  { name: 'tablet', width: 880, height: 720, isMobile: false },
  { name: 'mobile', width: 390, height: 844, isMobile: true },
];
const pages = [
  { path: '/', name: 'home' },
  { path: '/practice/create', name: 'practice-create' },
  { path: '/practice/solve', name: 'practice-solve' },
  { path: '/writing/setup', name: 'writing-setup' },
  { path: '/writing/53', name: 'writing-practice-53' },
  { path: '/writing/feedback', name: 'writing-feedback-list' },
  { path: '/mock/results', name: 'mock-results' },
  { path: '/mock/exam', name: 'mock-exam' },
];

function spawnVite() {
  if (process.env.UI_VERIFY_BASE_URL) {
    return undefined;
  }

  const command = process.platform === 'win32' ? 'npx.cmd' : 'npx';
  const child = spawn(command, ['vite', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
    cwd: process.cwd(),
    shell: process.platform === 'win32',
    stdio: ['ignore', 'pipe', 'pipe'],
  });

  child.stdout.on('data', (chunk) => process.stdout.write(chunk));
  child.stderr.on('data', (chunk) => process.stderr.write(chunk));
  return child;
}

async function waitForServer() {
  const startedAt = Date.now();
  let lastError;

  while (Date.now() - startedAt < 20_000) {
    try {
      const response = await fetch(baseUrl);
      if (response.ok) return;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }

  throw new Error(`UI verification server did not start at ${baseUrl}. ${lastError?.message ?? ''}`);
}

function intersects(a, b) {
  if (!a || !b) return false;
  return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
}

async function collectLayoutIssues(page, context) {
  return page.evaluate(({ contextName }) => {
    const issues = [];
    const rect = (selector) => {
      const node = document.querySelector(selector);
      if (!node) return null;
      const box = node.getBoundingClientRect();
      return {
        top: box.top,
        right: box.right,
        bottom: box.bottom,
        left: box.left,
        width: box.width,
        height: box.height,
      };
    };
    const overlaps = (a, b) => {
      if (!a || !b) return false;
      return !(a.right <= b.left || a.left >= b.right || a.bottom <= b.top || a.top >= b.bottom);
    };
    const header = rect('.app-header');
    const title = rect('.page-title');
    const content = rect('.app-content');
    const aiButton = rect('.ai-float-button');

    if (document.body.innerText.trim().length < 100) {
      issues.push(`${contextName}: body content is unexpectedly short`);
    }
    if (document.querySelector('.vite-error-overlay, #webpack-dev-server-client-overlay, [data-nextjs-dialog]')) {
      issues.push(`${contextName}: framework error overlay is visible`);
    }
    if (document.documentElement.scrollWidth > window.innerWidth + 1) {
      issues.push(`${contextName}: horizontal overflow detected`);
    }
    if (header && title && title.top < header.bottom - 1) {
      issues.push(`${contextName}: page title overlaps the sticky header`);
    }
    if (header && content && content.top < header.bottom - 1) {
      issues.push(`${contextName}: content starts behind the sticky header`);
    }

    if (location.pathname === '/mock/exam') {
      const criticalButtons = Array.from(document.querySelectorAll('button'))
        .filter((button) => /답안지|시험 종료|다음 문제|이전 문제/.test(button.textContent ?? ''))
        .map((button) => {
          const box = button.getBoundingClientRect();
          return {
            label: button.textContent?.trim(),
            top: box.top,
            right: box.right,
            bottom: box.bottom,
            left: box.left,
            width: box.width,
            height: box.height,
          };
        });

      for (const button of criticalButtons) {
        if (overlaps(aiButton, button)) {
          issues.push(`${contextName}: AI tutor button overlaps critical exam control "${button.label}"`);
        }
      }
    }

    return issues;
  }, { contextName: context });
}

async function runVerification() {
  await mkdir(outputDir, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const allIssues = [];

  for (const viewport of viewports) {
    const page = await browser.newPage({
      viewport: { width: viewport.width, height: viewport.height },
      isMobile: viewport.isMobile,
    });
    await page.addInitScript(() => {
      localStorage.removeItem('talkpik-theme-preferences');
    });
    const consoleIssues = [];

    page.on('console', (message) => {
      if (['error', 'warning'].includes(message.type())) {
        consoleIssues.push(`${viewport.name}: ${message.type()}: ${message.text()}`);
      }
    });
    page.on('pageerror', (error) => {
      consoleIssues.push(`${viewport.name}: pageerror: ${error.message}`);
    });

    for (const target of pages) {
      const context = `${viewport.name} ${target.path}`;
      await page.goto(`${baseUrl}${target.path}`, { waitUntil: 'networkidle' });
      await page.screenshot({
        path: path.join(outputDir, `${viewport.name}-${target.name}.png`),
        fullPage: false,
      });
      allIssues.push(...(await collectLayoutIssues(page, context)));
    }

    if (viewport.isMobile) {
      await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle' });
      await page.locator('.app-header button').first().click();
      await page.locator('.ant-drawer-open').waitFor();
      await page.waitForTimeout(500);
      const drawerBox = await page.locator('.ant-drawer-content-wrapper').first().boundingBox();
      if (!drawerBox || drawerBox.left < -1 || drawerBox.width < 260) {
        allIssues.push('mobile navigation drawer did not open to a usable width');
      }
    }

    await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle' });
    await page.getByLabel('화면 설정 열기').click();
    await page.getByRole('dialog', { name: /화면 설정/ }).waitFor();
    await page.getByLabel('화면 모드 선택').getByText('다크').click();
    await page.waitForFunction(() => document.documentElement.dataset.appearance === 'dark');
    await page.screenshot({
      path: path.join(outputDir, `${viewport.name}-settings-drawer-dark.png`),
      fullPage: false,
    });

    const themeState = await page.evaluate(() => ({
      theme: document.documentElement.dataset.theme,
      appearance: document.documentElement.dataset.appearance,
      appColorScheme: getComputedStyle(document.documentElement)
        .getPropertyValue('--app-color-scheme')
        .trim(),
      appBg: getComputedStyle(document.documentElement).getPropertyValue('--app-bg'),
    }));

    if (themeState.theme !== 'default') {
      allIssues.push(`${viewport.name}: default theme was not applied globally`);
    }
    if (themeState.appearance !== 'dark' || themeState.appColorScheme !== 'dark') {
      allIssues.push(`${viewport.name}: setting drawer did not apply dark mode`);
    }
    if (!themeState.appBg.includes('#101514')) {
      allIssues.push(`${viewport.name}: default dark theme CSS variables were not applied globally`);
    }

    allIssues.push(...consoleIssues);
    await page.close();
  }

  await browser.close();

  if (allIssues.length > 0) {
    console.error('UI verification failed:');
    for (const issue of allIssues) {
      console.error(`- ${issue}`);
    }
    process.exitCode = 1;
    return;
  }

  console.log(`UI verification passed. Screenshots saved to ${outputDir}`);
}

const vite = spawnVite();

try {
  await waitForServer();
  await runVerification();
} finally {
  if (vite) {
    if (process.platform === 'win32') {
      spawnSync('taskkill', ['/pid', String(vite.pid), '/t', '/f'], { stdio: 'ignore' });
    } else {
      vite.kill('SIGTERM');
    }
  }
}
