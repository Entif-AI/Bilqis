const TEST_ID_PATTERN = /^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/;

export const TEST_ID_PREFIXES = Object.freeze([
  "foundation",
  "status",
  "surface",
  "control",
]);

export function testId(...segments) {
  const id = segments.filter((segment) => segment !== "" && segment !== null && segment !== undefined)
    .map((segment) => String(segment))
    .join("-");
  if (!TEST_ID_PATTERN.test(id)) throw new TypeError(`TEST_ID_INVALID:${id}`);
  return id;
}

export function testIdAttribute(...segments) {
  return `data-test-id="${testId(...segments)}"`;
}

export function collectTestIds(markup) {
  return [...String(markup).matchAll(/\bdata-test-id="([^"]+)"/g)].map((match) => match[1]);
}

export function duplicateTestIds(markup) {
  const seen = new Set();
  const duplicates = new Set();
  for (const id of collectTestIds(markup)) {
    if (seen.has(id)) duplicates.add(id);
    seen.add(id);
  }
  return [...duplicates].sort();
}

export function assertUniqueTestIds(markup) {
  const duplicates = duplicateTestIds(markup);
  if (duplicates.length) throw new TypeError(`TEST_ID_DUPLICATE:${duplicates.join(",")}`);
  return true;
}
