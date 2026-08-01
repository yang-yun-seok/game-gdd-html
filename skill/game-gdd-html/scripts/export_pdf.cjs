#!/usr/bin/env node
"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

const DEFAULT_WIDTH = 1120;
const DEFAULT_MAX_WIDTH = 2400;
const DEFAULT_MAX_HEIGHT = 18000;

function parsePositive(value, name) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    throw new Error(`${name} must be a positive number`);
  }
  return Math.ceil(number);
}

function parseArgs(argv) {
  const options = {
    input: "",
    output: "",
    width: DEFAULT_WIDTH,
    maxWidth: DEFAULT_MAX_WIDTH,
    maxHeight: DEFAULT_MAX_HEIGHT,
    timeout: 30000,
    nodeModules: "",
    selfTest: false,
  };
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (value === "--self-test") options.selfTest = true;
    else if (value === "-o" || value === "--output") options.output = argv[++index] || "";
    else if (value === "--width-px") options.width = parsePositive(argv[++index], value);
    else if (value === "--max-width-px") options.maxWidth = parsePositive(argv[++index], value);
    else if (value === "--max-height-px") options.maxHeight = parsePositive(argv[++index], value);
    else if (value === "--timeout-ms") options.timeout = parsePositive(argv[++index], value);
    else if (value === "--node-modules") options.nodeModules = argv[++index] || "";
    else if (value.startsWith("-")) throw new Error(`unknown option: ${value}`);
    else if (!options.input) options.input = value;
    else throw new Error(`unexpected argument: ${value}`);
  }
  if (options.selfTest) return options;
  if (!options.input) throw new Error("provide an input HTML file");
  if (options.maxWidth < options.width) {
    throw new Error("--max-width-px must be greater than or equal to --width-px");
  }
  options.input = path.resolve(options.input);
  options.output = path.resolve(options.output || options.input.replace(/\.html?$/i, "") + ".pdf");
  return options;
}

function printCss(width) {
  return `@media print {
    @page { margin: 0 !important; }
    html, body { width: ${width}px !important; min-width: 0 !important; height: auto !important; overflow: visible !important; }
    body { margin: 0 !important; background: #fff !important; }
    .page-shell { width: ${width}px !important; margin: 0 !important; padding: 0 !important; }
    .document { width: 100% !important; max-width: none !important; border: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
    .hero { min-height: 0 !important; padding: 64px 56px !important; page-break-after: auto !important; break-after: auto !important; }
    .pillar-section, .gdd-section, .closing-section { padding: 48px 56px !important; page-break-before: auto !important; page-break-after: auto !important; break-before: auto !important; break-after: auto !important; }
    .visual-block, .info-card, .metric-card, .decision-card, .callout, .formula-block, table, tr { break-inside: auto !important; }
    .doc-footer { padding: 32px 56px !important; }
  }`;
}

function playwrightCandidates(extra) {
  return [
    extra,
    ...(process.env.NODE_PATH || "").split(path.delimiter),
    path.join(os.homedir(), ".cache", "codex-runtimes", "codex-primary-runtime", "dependencies", "node", "node_modules"),
  ].filter(Boolean);
}

function loadPlaywright(extra) {
  try {
    return require("playwright");
  } catch (_) {
    for (const directory of playwrightCandidates(extra)) {
      const candidate = path.join(directory, "playwright");
      if (fs.existsSync(candidate)) return require(candidate);
    }
  }
  throw new Error("Playwright was not found. Pass --node-modules or install playwright.");
}

function browserExecutables() {
  return [
    process.env.CHROME_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter((candidate) => candidate && fs.existsSync(candidate));
}

async function launchBrowser(chromium) {
  const attempts = [
    ...browserExecutables().map((executablePath) => ({ executablePath })),
    { channel: "chrome" },
    { channel: "msedge" },
    {},
  ];
  let lastError;
  for (const option of attempts) {
    try {
      return await chromium.launch({ headless: true, ...option });
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError;
}

async function settleDocument(page, timeout) {
  await page.evaluate(() => document.fonts?.ready);
  const generated = await page.locator('meta[name="generator"][content="game-gdd-html"]').count();
  if (generated) {
    await page.waitForFunction(
      () => {
        if (document.documentElement.dataset.gddReady === "true") return true;
        const diagrams = [...document.querySelectorAll(".mermaid")];
        const diagramsReady = diagrams.every((item) =>
          item.querySelector("svg") || item.parentElement?.querySelector(".render-error")
        );
        let chartSpecs = [];
        try {
          chartSpecs = JSON.parse(document.getElementById("gdd-chart-configs")?.textContent || "[]");
        } catch (_) {
          return false;
        }
        const chartsReady = chartSpecs.every((spec) => {
          const canvas = document.getElementById(spec.id);
          return window.Chart?.getChart?.(canvas) || canvas?.parentElement?.querySelector(".render-error");
        });
        return diagramsReady && chartsReady;
      },
      null,
      { timeout },
    );
    await page.evaluate(() => {
      if (!window.Chart?.instances) return;
      Object.values(window.Chart.instances).forEach((chart) => {
        chart.options.animation = false;
        chart.update("none");
      });
    });
  }
}

async function fitOnePage(page, options) {
  let width = options.width;
  let style;
  let height = 0;
  while (true) {
    if (style) await style.evaluate((element) => element.remove());
    await page.setViewportSize({ width, height: 900 });
    style = await page.addStyleTag({ content: printCss(width) });
    height = await page.evaluate(() => Math.ceil(Math.max(
      document.documentElement.scrollHeight,
      document.body.scrollHeight,
      document.querySelector(".document")?.getBoundingClientRect().height || 0,
    )));
    if (height <= options.maxHeight || width >= options.maxWidth) break;
    width = Math.min(
      options.maxWidth,
      Math.ceil(width * (height / options.maxHeight) * 1.08),
    );
  }
  if (height > options.maxHeight) {
    throw new Error(
      `content is ${height}px tall after widening to ${width}px; ` +
      "raise --max-width-px or --max-height-px",
    );
  }
  return { width, height: height + 2 };
}

function countPdfPages(buffer) {
  return (buffer.toString("latin1").match(/\/Type\s*\/Page\b/g) || []).length;
}

async function exportPdf(options) {
  if (!fs.existsSync(options.input)) throw new Error(`input not found: ${options.input}`);
  if (fs.existsSync(options.output)) {
    throw new Error(`output already exists: ${options.output}`);
  }
  fs.mkdirSync(path.dirname(options.output), { recursive: true });
  const { chromium } = loadPlaywright(options.nodeModules);
  const browser = await launchBrowser(chromium);
  try {
    const page = await browser.newPage({ viewport: { width: options.width, height: 900 } });
    await page.goto(pathToFileURL(options.input).href, { waitUntil: "load", timeout: options.timeout });
    await settleDocument(page, options.timeout);
    await page.emulateMedia({ media: "print" });
    const size = await fitOnePage(page, options);
    await page.addStyleTag({
      content: `@page { size: ${size.width}px ${size.height}px; margin: 0; }`,
    });
    await page.pdf({
      path: options.output,
      width: `${size.width}px`,
      height: `${size.height}px`,
      printBackground: true,
      preferCSSPageSize: true,
      margin: { top: "0", right: "0", bottom: "0", left: "0" },
    });
    const buffer = fs.readFileSync(options.output);
    const pages = countPdfPages(buffer);
    if (pages !== 1) throw new Error(`expected one PDF page, got ${pages}`);
    return { ...size, bytes: buffer.length, pages };
  } catch (error) {
    fs.rmSync(options.output, { force: true });
    throw error;
  } finally {
    await browser.close();
  }
}

function selfTest() {
  const parsed = parseArgs(["input.html", "-o", "out.pdf", "--width-px", "1200"]);
  assert.equal(parsed.width, 1200);
  assert.equal(path.extname(parsed.output), ".pdf");
  assert.match(printCss(1200), /width: 1200px/);
  assert.equal(countPdfPages(Buffer.from("/Type /Pages /Type /Page ", "latin1")), 1);
  console.log("[OK] One-page PDF exporter self-test passed.");
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.selfTest) return selfTest();
  const result = await exportPdf(options);
  console.log(`[OK] Exported ${options.output}`);
  console.log(`[INFO] One page · ${result.width}x${result.height}px · ${result.bytes} bytes`);
}

if (require.main === module) {
  main().catch((error) => {
    console.error(`[ERROR] ${error.message}`);
    process.exitCode = 2;
  });
}

module.exports = { countPdfPages, parseArgs, printCss };
