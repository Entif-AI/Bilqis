export async function capabilityJourney(page) {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const hook = (id) => page.locator(`[data-test-id="${id}"]`);

  await hook("capability-name").waitFor();
  check((await hook("capability-name").innerText()) === "Conjunction", "exact capability identity");
  check(await page.locator('[data-test-id^="capability-section-"]').count() >= 5, "dossier sections");
  check(await hook("capability-entry-history-1").count() === 1, "regression preserved");
  check(await hook("capability-entry-history-2").count() === 1, "recovery preserved");
  check(await hook("capability-entry-performance-2").count() === 1, "retained distinct");
  check(await hook("capability-entry-performance-3").count() === 1, "rejected distinct");
  check(await hook("capability-entry-teaching-1").count() === 1, "no gain distinct");
  check(await hook("capability-entry-teaching-2").count() === 1, "interference distinct");
  check((await hook("capability-metric-now").innerText()).includes("10/12"), "NOW keeps denominator");
  check((await hook("capability-heading").innerText()).includes("Current capability posture"), "affirmative dossier summary visible");
  check(await hook("capability-help-identity").count() === 1, "identity help present");
  check(await hook("capability-help-metrics").count() === 1, "metrics help present");
  check(await hook("capability-help-history").count() === 1, "chronology help present");

  await hook("capability-entry-performance-0-evidence-toggle").click();
  await hook("capability-evidence-ref-performance-0-0").click();
  await hook("capability-evidence-inspect-0").click();
  await hook("capability-evidence-record-0").waitFor();
  check((await hook("capability-evidence-detail").innerText()).includes("evidence:B.AND:fresh:3"), "exact evidence");
  await hook("capability-evidence-open").click();
  check(await page.evaluate(() => window.__openedEvidence?.id === "evidence:B.AND:fresh:3"), "full Evidence route preserves exact record");

  await hook("capability-lens-generation").fill("1");
  await hook("capability-lens-submit").click();
  await hook("capability-name").waitFor();
  check((await hook("capability-name").innerText()) === "Conjunction", "identity survives time lens");
  check(await hook("capability-entry-history-1").count() === 1, "G1 second history entry remains literal");
  check((await hook("capability-entry-history-1").innerText()).includes("No-gain"), "no future regression at G1");

  await hook("capability-entry-dependencies-0-evidence-toggle").click();
  await hook("capability-related-dependencies-0").click();
  await hook("capability-name").waitFor();
  check((await hook("capability-name").innerText()) === "Negation", "related capability opens exact owner");
  check(
    await hook("capability-lens-capability").inputValue() === "B.NOT" &&
      await hook("capability-lens-generation").inputValue() === "1",
    "exact dependent lens",
  );

  await page.evaluate(() => {
    document.documentElement.dataset.theme = "light";
    document.documentElement.dataset.density = "compact";
  });
  await page.setViewportSize({ width: 800, height: 900 });
  check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), "narrow viewport no overflow");
  await hook("capability-section-nav-sources").focus();
  await page.keyboard.press("Enter");
  check(await page.evaluate(() => document.activeElement?.dataset?.testId === "capability-section-sources"), "keyboard section focus");

  return "CAPABILITY_BROWSER_JOURNEY_PASS";
}

export default capabilityJourney;
