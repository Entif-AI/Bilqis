async (page) => {
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };

  await page.evaluate(() => {
    window.bamfMissionControl.connect = async () => ({state: "healthy"});
  });
  await page.locator('[data-test-id="foundation-reconnect"]').click();
  await page.getByTitle("Inspect exact capability B.AND").waitFor();

  await page.getByTitle("Inspect exact capability B.AND").click();
  await page.locator("#compare-left").click();
  await page.getByTitle("Inspect exact capability B.NOT").click();
  await page.locator("#compare-right").click();
  await page.getByText("WAS/TOP/NOW/ALL", {exact: true}).waitFor();
  await page.getByText("No winner is synthesized.", {exact: false}).waitFor();

  await page.getByTitle("Inspect exact capability B.AND").hover();
  const highlighted = await page.evaluate(() => Array.from(
    document.querySelectorAll("[data-global-highlight]"),
  ).map((element) => [
    element.dataset.objectKind,
    element.dataset.objectId,
    element.dataset.globalHighlight,
  ]).filter((value, index, all) =>
    all.findIndex((candidate) => candidate.join("\u0000") === value.join("\u0000")) === index));
  check(JSON.stringify(highlighted.sort()) === JSON.stringify([
    ["capability", "B.AND", "selected"],
    ["capability", "B.IFF", "related"],
    ["capability", "B.NOT", "related"],
    ["capability", "B.OR", "related"],
  ].sort()), "only declared capability relations cross-highlight");

  await page.locator("#pin-selection").click();
  await page.locator('[data-investigation-panel="pins"]').click();
  await page.getByText("Open exact pin", {exact: true}).waitFor();

  await page.locator("#annotate-selection").click();
  await page.locator('[data-annotation-form] textarea').fill("GUI18 browser journey note.");
  await page.getByRole("button", {name: "Save non-authoritative note"}).click();
  await page.getByText("OPERATOR NOTE · NON-AUTHORITATIVE", {exact: true}).waitFor();

  const generation = page.locator('[data-time-lens-form] input[name="generation"]');
  await generation.evaluate((input) => {
    const setter = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype, "value",
    ).set;
    setter.call(input, "44238");
    input.dispatchEvent(new Event("input", {bubbles: true}));
  });
  await generation.press("Enter");
  await page.getByRole("heading", {name: "UNAVAILABLE", exact: true}).waitFor();
  check(page.url().includes("generation=44238") && page.url().includes("mode=HISTORICAL"),
    "School preserves the exact historical lens while unavailable");

  await page.locator('[data-test-id="nav-destination-memory"]').click();
  await page.getByText("motif-read:fixture:g44238:s0", {exact: false}).waitFor();
  check(page.url().includes("generation=44238") && page.url().includes("mode=HISTORICAL"),
    "Memory uses the same historical lens");
  await page.getByRole("button", {name: "Use verified current", exact: true}).click();
  await page.getByText("Generation 7", {exact: false}).first().waitFor();
  check(page.url().includes("generation=7") && page.url().includes("mode=LIVE"),
    "verified current restores exact current route");

  await page.locator('[data-test-id="nav-destination-learning"]').click();
  await page.getByRole("button", {
    name: "Inspect candidate · candidate:fixture:retained-44239",
  }).click();
  await page.locator("#compare-left").click();
  await page.getByRole("button", {
    name: /C.NUMBER · REJECTED · PROTECTED_CAPABILITY_REGRESSION/,
  }).click();
  await page.getByRole("button", {
    name: "Inspect candidate · candidate:fixture:interference-reject",
  }).click();
  await page.locator("#compare-right").click();
  await page.getByText("Target committed", {exact: true}).waitFor();
  const candidateTable = await page.locator(".investigation-table").innerText();
  check(candidateTable.includes("12/12") && candidateTable.includes("8/12"),
    "candidate compare keeps committed target values distinct");
  check(candidateTable.includes("Protected committed") &&
    candidateTable.includes("48/48"), "candidate compare keeps protected committed evidence");

  await page.locator('[data-test-id="nav-destination-lineage"]').click();
  await page.getByRole("button", {name: /Generation 44238 Retained candidate progression/}).click();
  await page.locator("#compare-left").click();
  await page.keyboard.press("Escape");
  await page.getByRole("button", {name: /Generation 44240 Explicit recovery fork/}).click();
  await page.locator("#compare-right").click();
  await page.getByText("Topology digest/version", {exact: true}).waitFor();
  const generationTable = await page.locator(".investigation-table").innerText();
  check(generationTable.includes("BAMF-V1") && generationTable.includes("BAMF-V2"),
    "generation compare exposes exact topology difference");
  check(generationTable.includes("recovered accepted checkpoint"),
    "generation compare preserves recovery disposition");

  const noPageOverflow = await page.evaluate(() =>
    document.documentElement.scrollWidth <= innerWidth);
  const tableScrollable = await page.evaluate(() => {
    const wrap = document.querySelector(".investigation-table-wrap");
    return Boolean(wrap && wrap.scrollWidth > wrap.clientWidth);
  });
  check(noPageOverflow, "investigation layout has no page-level horizontal overflow");
  check(tableScrollable, "wide compare table scrolls inside its bounded container");

  return "GUI18_BROWSER_JOURNEY_PASS";
}
