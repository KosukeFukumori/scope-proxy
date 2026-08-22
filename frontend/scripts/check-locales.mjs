// Verify that every locale file under src/i18n/locales/ has the exact same set of
// (nested) keys. Prevents shipping a UI string added to only one locale file.
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const localesDir = path.join(__dirname, "..", "src", "i18n", "locales");
const localeFiles = ["ja.json", "en.json", "zh.json"];

/**
 * Recursively flatten a nested object into a sorted list of dot-joined key paths.
 * @param {Record<string, unknown>} obj
 * @param {string} prefix
 * @returns {string[]}
 */
function flattenKeys(obj, prefix = "") {
  const keys = [];
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    if (value !== null && typeof value === "object" && !Array.isArray(value)) {
      keys.push(...flattenKeys(value, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

const keySetsByLocale = new Map();
for (const fileName of localeFiles) {
  const filePath = path.join(localesDir, fileName);
  const raw = readFileSync(filePath, "utf-8");
  const parsed = JSON.parse(raw);
  keySetsByLocale.set(fileName, new Set(flattenKeys(parsed)));
}

const [baseFileName, ...otherFileNames] = localeFiles;
const baseKeys = keySetsByLocale.get(baseFileName);

let hasMismatch = false;
for (const fileName of otherFileNames) {
  const keys = keySetsByLocale.get(fileName);

  const missingInThis = [...baseKeys].filter((key) => !keys.has(key));
  const extraInThis = [...keys].filter((key) => !baseKeys.has(key));

  if (missingInThis.length > 0) {
    hasMismatch = true;
    console.error(`[check-locales] ${fileName} is missing keys present in ${baseFileName}:`);
    for (const key of missingInThis) console.error(`  - ${key}`);
  }
  if (extraInThis.length > 0) {
    hasMismatch = true;
    console.error(`[check-locales] ${fileName} has extra keys not present in ${baseFileName}:`);
    for (const key of extraInThis) console.error(`  - ${key}`);
  }
}

if (hasMismatch) {
  console.error("\n[check-locales] Locale key sets do not match. Fix the differences above.");
  process.exit(1);
}

console.log(`[check-locales] OK: ${localeFiles.join(", ")} all have matching keys (${baseKeys.size} keys).`);
