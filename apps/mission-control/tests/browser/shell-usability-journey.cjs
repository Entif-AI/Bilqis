async function shellUsabilityProof(page, { check, setDisplay, navigate, reconnect }) {
  await page.setViewportSize({ width: 1440, height: 960 });
  await setDisplay(page, "dark", "comfortable");
  const commandTrigger = page.locator('[data-test-id="shell-command-trigger"]');
  check(await commandTrigger.count() === 0, "permanent Command trigger survived");

  const rail = page.locator('[data-test-id="shell-rail"]');
  const railToggle = page.locator('[data-test-id="shell-rail-toggle"]');
  const expandedWidth = await rail.evaluate(node => node.getBoundingClientRect().width);
  await railToggle.click();
  const collapsedWidth = await rail.evaluate(node => node.getBoundingClientRect().width);
  check(collapsedWidth < expandedWidth, "collapsed rail does not reclaim horizontal space");
  const railCopy = (await rail.innerText()).toLowerCase();
  for (const expected of ["Curriculum", "Semantics", "Strategies", "Records"]) {
    check(railCopy.includes(expected.toLowerCase()), `collapsed rail lost ${expected} group label`);
  }
  await navigate(page, "memory");
  check(await page.locator('[data-test-id="nav-destination-memory"]').getAttribute("aria-current") === "page",
    "collapsed rail lost current-route state");
  check(await page.locator('[data-test-id="shell-main-content"]').evaluate(() =>
    document.querySelectorAll('[data-test-id="shell-navigation"] [aria-current="page"]').length === 1),
  "navigation exposes more than one current route");
  await page.reload({ waitUntil: "domcontentloaded" });
  await reconnect(page);
  check(await page.locator('[data-test-id="shell-main-content"]').evaluate(() =>
    document.documentElement.dataset.rail === "collapsed"),
  "rail collapse preference did not survive reload");

  await navigate(page, "school");
  await page.locator('[data-test-id="shell-view-host"]').evaluate((node) => {
    node.style.paddingBottom = "2200px";
  });
  await page.evaluate(() => window.scrollTo({ top: 900, left: 0, behavior: "auto" }));
  const beforeDisclosure = await page.evaluate(() => scrollY);
  check(beforeDisclosure > 0, "browser did not establish a non-zero shell scroll position");
  await page.evaluate(() => {
    const disclosure = document.querySelector('[data-test-id="shell-system-context-disclosure"]');
    disclosure.open = true;
    disclosure.dispatchEvent(new Event("toggle"));
  });
  check(await page.evaluate(() => scrollY) === beforeDisclosure,
    "same-view disclosure reset primary scroll");
  await page.evaluate(() =>
    document.querySelector('[data-test-id="nav-destination-memory"]').click());
  await page.waitForTimeout(20);
  check(await page.evaluate(() => scrollY) === 0,
    "different primary destination did not reset document scroll to top");

  await page.evaluate(() => window.scrollTo({ top: 0, left: 0, behavior: "auto" }));
  const system = page.locator('[data-test-id="shell-system-context-disclosure"]');
  const view = page.locator('[data-test-id="shell-view-settings-disclosure"]');
  await page.evaluate(() => {
    document.querySelector('[data-test-id="shell-system-context-disclosure"]').removeAttribute("open");
    document.querySelector('[data-test-id="shell-view-settings-disclosure"]').removeAttribute("open");
  });
  await page.locator('[data-test-id="shell-system-context-trigger"]').click();
  check(await system.evaluate(node => node.open), "System Context did not open");
  await page.locator('[data-test-id="shell-view-settings-trigger"]').click();
  check(await view.evaluate(node => node.open), "View did not open");
  check(!await system.evaluate(node => node.open), "System Context remained open with View");
  await page.locator('[data-test-id="shell-system-context-trigger"]').click();
  check(await system.evaluate(node => node.open), "System Context did not reopen");
  check(!await view.evaluate(node => node.open), "View remained open with System Context");

  const summaryGeometry = await page.locator('[data-test-id="shell-system-context-trigger"]').evaluate((node) => {
    const style = getComputedStyle(node);
    return {
      alignItems: style.alignItems,
      background: style.backgroundColor,
      canvas: getComputedStyle(document.body).backgroundColor,
      height: node.getBoundingClientRect().height,
    };
  });
  check(summaryGeometry.alignItems === "center", "context trigger text is not vertically centered");
  check(summaryGeometry.height >= 24, "context trigger target is smaller than 24px");
  check(summaryGeometry.background !== summaryGeometry.canvas,
    "context trigger background is indistinguishable from canvas");

  const help = page.locator('[data-test-id="shell-help-run-context"]');
  const helpTrigger = page.locator('[data-test-id="shell-help-run-context-trigger"]');
  const helpContent = page.locator('[data-test-id="shell-help-run-context-content"]');
  const helpSize = await helpTrigger.evaluate(node => {
    const rect = node.getBoundingClientRect();
    return { width: rect.width, height: rect.height };
  });
  check(helpSize.width >= 24 && helpSize.height >= 24, "context help target is smaller than 24px");
  await helpTrigger.focus();
  const focusCopy = await helpContent.innerText();
  check(await helpContent.evaluate(node => getComputedStyle(node).display !== "none"),
    "context help is not visible on keyboard focus");
  await page.keyboard.press("Escape");
  check(await helpContent.evaluate(node => getComputedStyle(node).display === "none"),
    "context help cannot be dismissed with Escape while focus remains");
  await page.locator('[data-test-id="shell-destination-title"]').focus();
  await page.mouse.move(0, 0);
  await help.hover();
  const hoverCopy = await helpContent.innerText();
  check(focusCopy === hoverCopy && focusCopy.length > 20,
    "context help hover and focus content differ");
  await helpContent.hover();
  check(await helpContent.evaluate(node => getComputedStyle(node).display !== "none"),
    "context help cannot be hovered without disappearing");
  await page.keyboard.press("Escape");
  check(await helpContent.evaluate(node => getComputedStyle(node).display === "none"),
    "hover-only context help cannot be dismissed with Escape");

  const navHelpTrigger = page.locator('[data-test-id="nav-help-curriculum-trigger"]');
  const navHelpContent = page.locator('[data-test-id="nav-help-curriculum-content"]');
  const currentSelector = '[data-test-id^="nav-destination-"][aria-current="page"]';
  const currentBeforeNavHelp = await page.locator(currentSelector).getAttribute("data-view");
  await navHelpTrigger.click();
  check(await page.locator(currentSelector).getAttribute("data-view") === currentBeforeNavHelp,
    "navigation help activated destination routing");
  await page.mouse.move(0, 0);
  await navHelpTrigger.hover();
  await navHelpContent.hover();
  await navHelpTrigger.focus();
  const navHelpGeometry = await navHelpContent.evaluate((node) => {
    if (getComputedStyle(node).display === "none") return { visible: false };
    const rect = node.getBoundingClientRect();
    const x = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2));
    const y = Math.max(0, Math.min(innerHeight - 1, rect.top + Math.min(rect.height / 2, 20)));
    const sample = document.elementFromPoint(x, y);
    return {
      visible: true,
      rect: { left: rect.left, top: rect.top, right: rect.right, bottom: rect.bottom },
      point: { x, y },
      sampleTestId: sample?.dataset?.testId ?? null,
      sampleTag: sample?.tagName ?? null,
      hit: Boolean(sample && (sample === node || node.contains(sample))),
    };
  });
  check(navHelpGeometry.hit, `navigation group help is clipped by the rail: ${JSON.stringify(navHelpGeometry)}`);

  await navigate(page, "resources");
  const temporal = page.locator('[data-test-id="resources-time-0"]');
  const temporalDetail = page.locator('[data-test-id="resources-time-0-detail"]');
  await temporal.waitFor();
  check(Boolean(await temporal.getAttribute("datetime")), "temporal primitive lacks semantic datetime");
  check(await temporalDetail.evaluate(node => getComputedStyle(node).display === "none"),
    "full temporal detail is visible before hover or keyboard focus");
  await temporal.focus();
  check(await temporalDetail.evaluate(node => getComputedStyle(node).display !== "none"),
    "full temporal detail is not visible on keyboard focus");
  await page.keyboard.press("Escape");
  check(await temporalDetail.evaluate(node => getComputedStyle(node).display === "none"),
    "focused temporal detail cannot be dismissed with Escape");
  await page.mouse.move(0, 0);
  await temporal.hover();
  await temporalDetail.hover();
  check(await temporalDetail.evaluate(node => getComputedStyle(node).display !== "none"),
    "temporal detail cannot be hovered without disappearing");
  await page.keyboard.press("Escape");
  check(await temporalDetail.evaluate(node => getComputedStyle(node).display === "none"),
    "hover-only temporal detail cannot be dismissed with Escape");

  await page.setViewportSize({ width: 390, height: 844 });
  check(await page.locator('[data-test-id="shell-brand"]').evaluate(node =>
    getComputedStyle(node.querySelector("strong")).display !== "none"),
  "persisted collapsed rail hides the brand in responsive mode");
  check(await railToggle.evaluate(node => getComputedStyle(node).display === "none"),
    "responsive rail toggle should not consume compact header space");
  await page.locator('[data-test-id="shell-system-context-trigger"]').click();
  const responsivePopover = await page.locator('[data-test-id="shell-system-context-popover"]').evaluate(node => {
    const rect = node.getBoundingClientRect();
    return { left: rect.left, right: rect.right, width: rect.width, viewport: innerWidth };
  });
  check(
    responsivePopover.left >= -1 && responsivePopover.right <= responsivePopover.viewport + 1,
    `responsive System Context popover escapes viewport: ${JSON.stringify(responsivePopover)}`,
  );
  await page.locator('[data-test-id="shell-system-context-trigger"]').click();
  await page.setViewportSize({ width: 1440, height: 960 });
  await railToggle.click();
  return true;
}

async function accessibilityTreeProof(page, { check, navigate }) {
  await navigate(page, "school");
  const session = await page.context().newCDPSession(page);
  await session.send("Accessibility.enable");
  const tree = await session.send("Accessibility.getFullAXTree");
  const roles = tree.nodes.map(node => node.role?.value).filter(Boolean);
  const names = tree.nodes.map(node => node.name?.value).filter(Boolean);
  for (const role of ["main", "navigation", "heading"]) {
    check(roles.includes(role), `accessibility tree missing ${role}`);
  }
  check(names.includes("School"), "accessibility tree missing School destination name");
  return {
    nodeCount: tree.nodes.length,
    roles: [...new Set(roles)].sort(),
    schoolNamePresent: true,
  };
}

async function expansionProof(page, { check, navigate }) {
  await navigate(page, "school");
  await page.evaluate(() => {
    const roots = [
      document.querySelector('[data-test-id="shell-rail"]'),
      document.querySelector('[data-test-id="shell-view-host"]'),
    ].filter(Boolean);
    for (const root of roots) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const texts = []; while (walker.nextNode()) texts.push(walker.currentNode);
      for (const node of texts) {
        const tag = node.parentElement?.tagName;
        if (!node.nodeValue.trim() || ["CODE", "PRE", "KBD"].includes(tag)) continue;
        node.nodeValue = `${node.nodeValue.trim()} · ${node.nodeValue.trim()}`;
      }
    }
    document.documentElement.dir = "rtl";
  });
  const overflow = await page.locator('[data-test-id="shell-main-content"]').evaluate(() =>
    document.documentElement.scrollWidth > innerWidth + 1);
  check(!overflow, "expanded RTL copy creates document-level overflow");
  return true;
}

module.exports = { accessibilityTreeProof, expansionProof, shellUsabilityProof };
