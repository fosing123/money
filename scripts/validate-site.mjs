import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import { resolve, sep } from "node:path";

const root = process.cwd();
const read = (path) => readFileSync(resolve(root, path), "utf8");
const html = read("index.html");
const app = read("app.js");
const sw = read("sw.js");
const manifest = JSON.parse(read("manifest.webmanifest"));

assert.match(html, /<!doctype html>/i, "index.html must declare HTML5");
assert.match(html, /<html lang="en">/i, "The document must declare its language");
assert.match(html, /<title>TIANA/i, "The page needs a useful document title");
assert.match(html, /name="description"/i, "The page needs a meta description");
assert.match(html, /rel="manifest"/i, "The installable manifest must be linked");
assert.match(html, /app\.css/, "The app stylesheet must be linked");
assert.match(html, /app\.js/, "The app JavaScript must be linked");

for (const [, ref] of html.matchAll(/\b(?:src|href)="([^"]+)"/g)) {
  if (/^(?:[a-z]+:|\/\/|#|data:)/i.test(ref)) continue;
  const relative = decodeURIComponent(ref.split(/[?#]/, 1)[0]).replace(/^\.\//, "");
  assert.ok(existsSync(resolve(root, relative)), `index.html references a missing local file: ${ref}`);
}

assert.equal(manifest.name, "TIANA", "Manifest name should match the app");
assert.equal(manifest.display, "standalone", "The app should be installable in standalone mode");
assert.ok(Array.isArray(manifest.icons) && manifest.icons.length > 0, "Manifest must provide an icon");
for (const icon of manifest.icons) {
  const iconPath = decodeURIComponent(new URL(icon.src, "https://student-money.invalid/").pathname).replace(/^\//, "");
  assert.ok(existsSync(resolve(root, iconPath)), `Manifest icon is missing: ${icon.src}`);
}

const shellRefs = new Set([...sw.matchAll(/["'](\.\/[^"'\x60]+)["']/g)].map((match) => match[1]));
assert.ok(shellRefs.has("./index.html"), "Offline shell must cache index.html");
assert.ok(shellRefs.has("./app.js"), "Offline shell must cache app.js");
assert.ok(shellRefs.has("./app.css"), "Offline shell must cache app.css");
for (const ref of shellRefs) {
  const relative = ref.replace(/^\.\//, "");
  const target = resolve(root, relative);
  assert.ok(target === root || target.startsWith(root + sep), `Service-worker path escapes the repository: ${ref}`);
  assert.ok(existsSync(target), `Service worker references a missing offline asset: ${ref}`);
}
assert.match(sw, /const CACHE = "tiana-shell-v\d+"/, "Cache version must be explicit");
assert.match(sw, /key\.startsWith\(CACHE_PREFIX\)/, "Cache cleanup must only affect this app's caches");

assert.match(app, /function exportBackup\(/, "Full JSON backup must be available");
assert.match(app, /function restoreBackupFile\(/, "JSON backup restore must be available");
assert.match(app, /student-money-backup/, "Backup format must be identifiable");
assert.match(app, /data-action="export-backup"/, "Settings must expose the backup action");
assert.match(app, /data-action="import-backup"/, "Settings must expose the restore action");

console.log(`Static smoke checks passed: ${shellRefs.size} service-worker shell paths, manifest, page links and backup controls.`);
