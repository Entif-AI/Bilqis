// Async paints preserve the operator's in-progress query and disclosure state.
export function replaceEvidenceMarkup(container, markup, { resetDraft = false, resetDetails = false, focusId = null } = {}) {
  const active = container.ownerDocument?.activeElement;
  const focused = active && container.contains?.(active) ? active : null;
  const oldFocusId = focused?.dataset?.testId;
  const caret = typeof focused?.selectionStart === "number" ? [focused.selectionStart, focused.selectionEnd] : null;
  const kind = container.querySelector('[data-test-id="evidence-query-kind"]')?.value;
  const value = container.querySelector('[data-test-id="evidence-query-value"]')?.value;
  const openIds = resetDetails ? [] : [...container.querySelectorAll("details[data-test-id][open]")].map((item) => item.dataset.testId);
  container.innerHTML = markup;
  if (!resetDraft) {
    for (const [id, draft] of [["kind", kind], ["value", value]]) {
      const field = container.querySelector(`[data-test-id="evidence-query-${id}"]`);
      if (field && draft !== undefined) field.value = draft;
    }
  }
  for (const id of openIds) {
    const details = container.querySelector(`[data-test-id="${id}"]`);
    if (details) details.open = true;
  }
  const targetId = focusId ?? oldFocusId;
  if (!targetId) return;
  let next = container.querySelector(`[data-test-id="${targetId}"]`)
    ?? container.querySelector('[data-test-id="evidence-results-heading"]');
  if (next?.disabled) next = container.querySelector('[data-test-id="evidence-results-heading"]');
  next?.focus({ preventScroll: !focusId });
  if (!focusId && caret && next?.setSelectionRange) next.setSelectionRange(...caret);
}
