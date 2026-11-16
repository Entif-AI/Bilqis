async (page) => {
  const check = (condition, message) => {
    if (!condition) throw new Error(message);
  };

  await page.evaluate(() => {
    window.bamfMissionControl.connect = async () => ({state: "healthy"});
  });
  await page.locator('[data-test-id="foundation-reconnect"]').click();
  const andCapability = page.locator('[data-test-id="school-matrix-capability-b-and"]');
  const notCapability = page.locator('[data-test-id="school-matrix-capability-b-not"]');
  await andCapability.waitFor();

  await andCapability.click();
  await page.locator('[data-test-id="investigation-inspector-compare-left"]').click();
  await notCapability.click();
  await page.locator('[data-test-id="investigation-inspector-compare-right"]').click();
  await page.locator('[data-test-id="investigation-compare-table"]').waitFor();

  await andCapability.hover();
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

  await page.locator('[data-test-id="investigation-inspector-pin"]').click();
  await page.locator('[data-test-id="investigation-open-pins"]').click();
  await page.locator('[data-test-id="investigation-pin-open-0"]').waitFor();

  await page.locator('[data-test-id="investigation-inspector-note"]').click();
  await page.locator('[data-test-id="investigation-note-body"]').fill("GUI18 browser journey note.");
  await page.locator('[data-test-id="investigation-note-save"]').click();
  await page.locator('[data-test-id="investigation-note-0"]').waitFor();

  await page.locator('[data-test-id="investigation-time-toggle"]').click();
  const generation = page.locator('[data-test-id="investigation-time-generation"]');
  await generation.evaluate((input) => {
    const setter = Object.getOwnPropertyDescriptor(
      HTMLInputElement.prototype, "value",
    ).set;
    setter.call(input, "44238");
    input.dispatchEvent(new Event("input", {bubbles: true}));
  });
  await generation.press("Enter");
  await page.locator('[data-test-id="school-historical-unavailable"]').waitFor();
  check(page.url().includes("generation=44238") && page.url().includes("mode=HISTORICAL"),
    "School preserves the exact historical lens while unavailable");

  await page.locator('[data-test-id="nav-destination-memory"]').click();
  const memoryWorkspace = page.locator('[data-test-id="memory-workspace"]');
  await memoryWorkspace.waitFor();
  check((await memoryWorkspace.innerText()).includes("motif-read:fixture:g44238:s0"),
    "Memory renders the exact historical motif identity");
  check(page.url().includes("generation=44238") && page.url().includes("mode=HISTORICAL"),
    "Memory uses the same historical lens");
  if (!await page.locator('[data-test-id="investigation-time-lens"]').evaluate((element) => element.hasAttribute("open"))) {
    await page.locator('[data-test-id="investigation-time-toggle"]').click();
  }
  await page.locator('[data-test-id="investigation-time-current"]').click();
  const generationSummary = page.locator('[data-test-id="shell-generation-summary"]');
  await generationSummary.waitFor();
  check((await generationSummary.innerText()).includes("7"),
    "verified current restores generation 7 in shell context");
  check(page.url().includes("generation=7") && page.url().includes("mode=LIVE"),
    "verified current restores exact current route");

  await page.locator('[data-test-id="nav-destination-learning"]').click();
  await page.locator('[data-test-id="learning-candidate-inspect"]').click();
  await page.locator('[data-test-id="investigation-inspector-compare-left"]').click();
  await page.locator('[data-test-id="learning-episode-selector"]').selectOption(
    "episode-record:fixture:interference-reject",
  );
  await page.locator('[data-test-id="learning-candidate-inspect"]').click();
  await page.locator('[data-test-id="investigation-inspector-compare-right"]').click();
  await page.locator('[data-test-id="investigation-compare-row-target-committed"]').waitFor();
  const candidateTable = await page.locator('[data-test-id="investigation-compare-table"]').innerText();
  check(candidateTable.includes("12/12") && candidateTable.includes("8/12"),
    "candidate compare keeps committed target values distinct");
  check(candidateTable.includes("Protected committed") &&
    candidateTable.includes("48/48"), "candidate compare keeps protected committed evidence");

  await page.locator('[data-test-id="nav-destination-lineage"]').click();
  await page.locator('[data-test-id="lineage-graph-generation-44238"]').click();
  await page.locator('[data-test-id="investigation-inspector-compare-left"]').click();
  await page.keyboard.press("Escape");
  await page.locator('[data-test-id="lineage-graph-generation-44240"]').click();
  await page.locator('[data-test-id="investigation-inspector-compare-right"]').click();
  await page.locator('[data-test-id="investigation-compare-row-topology-digest-version"]').waitFor();
  const generationTable = await page.locator('[data-test-id="investigation-compare-table"]').innerText();
  check(generationTable.includes("BAMF-V1") && generationTable.includes("BAMF-V2"),
    "generation compare exposes exact topology difference");
  check(generationTable.includes("recovered accepted checkpoint"),
    "generation compare preserves recovery disposition");

  const noPageOverflow = await page.evaluate(() =>
    document.documentElement.scrollWidth <= innerWidth);
  const tableScrollable = await page.evaluate(() => {
    const wrap = document.querySelector('[data-test-id="investigation-compare-table-wrap"]');
    return Boolean(wrap && wrap.scrollWidth > wrap.clientWidth);
  });
  check(noPageOverflow, "investigation layout has no page-level horizontal overflow");
  check(tableScrollable, "wide compare table scrolls inside its bounded container");

  return "GUI18_BROWSER_JOURNEY_PASS";
}
