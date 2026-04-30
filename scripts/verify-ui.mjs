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

function hasGlassSurface(surface) {
  if (!surface) return false;
  return (
    surface.bg === 'rgba(0, 0, 0, 0)' &&
    surface.blur?.includes('blur(20px)') &&
    surface.shadow &&
    surface.shadow !== 'none'
  );
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

async function verifyLiquidGlassOverlays(browser, issues) {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 720 },
  });

  await page.addInitScript(() => {
    localStorage.setItem(
      'talkpik-theme-preferences',
      JSON.stringify({
        state: { themeName: 'liquidGlass', appearance: 'light' },
        version: 0,
      }),
    );
  });

  const slowTransitions = `
    *, *::before, *::after {
      transition-duration: 1400ms !important;
      animation-duration: 1400ms !important;
      animation-delay: 0ms !important;
    }
  `;

  await page.goto(`${baseUrl}/`, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: slowTransitions });
  await page.waitForTimeout(200);

  await page.locator('.app-header > .ant-space:last-child .ant-btn').first().click();
  await page.waitForTimeout(80);
  await page.screenshot({
    path: path.join(outputDir, 'desktop-liquid-glass-drawer-early.png'),
    fullPage: false,
  });

  const drawerEarly = await page.evaluate(() => {
    const wrapper = document.querySelector('.app-drawer.ant-drawer-open .ant-drawer-content-wrapper');
    if (!wrapper) return null;
    return {
      bg: getComputedStyle(wrapper).backgroundColor,
      blur: getComputedStyle(wrapper, '::before').backdropFilter,
      opacity: getComputedStyle(wrapper).opacity,
      shadow: getComputedStyle(wrapper).boxShadow,
      transform: getComputedStyle(wrapper).transform,
    };
  });

  if (!hasGlassSurface(drawerEarly)) {
    issues.push('liquidGlass: settings drawer does not have the glass surface on the first visible frame');
  }
  if (drawerEarly?.opacity !== '1') {
    issues.push('liquidGlass: settings drawer fades the glass layer on the first visible frame');
  }

  await page.goto(`${baseUrl}/writing/53`, { waitUntil: 'networkidle' });
  await page.addStyleTag({ content: slowTransitions });
  await page.locator('textarea').fill('가'.repeat(140));
  await page.locator('main .ant-card button.ant-btn-primary:not([disabled])').first().click();
  await page.waitForFunction(() =>
    Array.from(document.querySelectorAll('.app-modal')).some((node) => {
      const modal = node.querySelector('.ant-modal');
      if (!modal) return false;
      const box = modal.getBoundingClientRect();
      return getComputedStyle(node).display !== 'none' && box.width > 0 && box.height > 0;
    }),
  );
  await page.waitForTimeout(80);
  await page.screenshot({
    path: path.join(outputDir, 'desktop-liquid-glass-modal-early.png'),
    fullPage: false,
  });

  const modalEarly = await page.evaluate(() => {
    const wrap = Array.from(document.querySelectorAll('.app-modal')).find((node) => {
      const modal = node.querySelector('.ant-modal');
      if (!modal) return false;
      const box = modal.getBoundingClientRect();
      return getComputedStyle(node).display !== 'none' && box.width > 0 && box.height > 0;
    });
    const surface = wrap?.querySelector('.ant-modal-content');
    const modal = wrap?.querySelector('.ant-modal');
    if (!surface || !modal) return null;
    return {
      bg: getComputedStyle(surface).backgroundColor,
      blur: getComputedStyle(surface, '::before').backdropFilter,
      shadow: getComputedStyle(surface).boxShadow,
      transform: getComputedStyle(modal).transform,
    };
  });

  if (!hasGlassSurface(modalEarly)) {
    issues.push('liquidGlass: submit modal does not have the glass surface on the first visible frame');
  }

  await page.close();
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
    await page.locator('.app-header > .ant-space:last-child .ant-btn').first().click();
    await page.locator('.ant-drawer-open').waitFor();
    await page.evaluate(() => {
      const visibleWrapper = Array.from(document.querySelectorAll('.ant-drawer-content-wrapper')).find(
        (node) => getComputedStyle(node).display !== 'none',
      );
      const appearanceSegmented = visibleWrapper?.querySelectorAll('.ant-segmented')[1];
      const darkItem = appearanceSegmented?.querySelectorAll('.ant-segmented-item')[1];
      if (!(darkItem instanceof HTMLElement)) {
        throw new Error('settings drawer appearance control is not visible');
      }
      darkItem.click();
    });
    await page.waitForFunction(() => document.documentElement.dataset.appearance === 'dark');
    await page.screenshot({
      path: path.join(outputDir, `${viewport.name}-settings-drawer-dark.png`),
      fullPage: false,
    });

    const themeState = await page.evaluate(() => ({
      theme: document.documentElement.dataset.theme,
      appearance: document.documentElement.dataset.appearance,
      colorScheme: document.documentElement.style.colorScheme,
      bodyBackground: getComputedStyle(document.body).backgroundColor,
    }));

    if (themeState.theme !== 'default') {
      allIssues.push(`${viewport.name}: default theme was not applied globally`);
    }
    if (themeState.appearance !== 'dark' || themeState.colorScheme !== 'dark') {
      allIssues.push(`${viewport.name}: setting drawer did not apply dark mode`);
    }
    if (!themeState.bodyBackground || themeState.bodyBackground === 'rgba(0, 0, 0, 0)') {
      allIssues.push(`${viewport.name}: default dark mode did not paint the body background`);
    }

    allIssues.push(...consoleIssues);
    await page.close();
  }

  await verifyLiquidGlassOverlays(browser, allIssues);

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
