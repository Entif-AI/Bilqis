"use strict";

const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const { RENDERER_ENTRY_URL } = require("../renderer-location.cjs");
const {
  RENDERER_ASSETS,
  assetPathForRendererRequest,
  registerMissionControlProtocol,
} = require("../renderer-protocol.cjs");

test("renderer protocol resolves only the checked-in Mission Control asset allowlist", () => {
  const root = "/Applications/Bilqis/MissionControl/renderer";
  assert.equal(
    assetPathForRendererRequest(RENDERER_ENTRY_URL, root),
    `${root}/index.html`,
  );
  assert.equal(
    assetPathForRendererRequest("bamf-mc://app/renderer.mjs", root),
    `${root}/renderer.mjs`,
  );
  assert.deepEqual([...RENDERER_ASSETS.keys()].sort(), [
    "/atlas/atlas-controller.mjs",
    "/atlas/semantic-atlas.css",
    "/atlas/semantic-atlas.mjs",
    "/capability/app.mjs",
    "/capability/controller.mjs",
    "/capability/dossier.css",
    "/capability/fixture-data.mjs",
    "/capability/fixture.mjs",
    "/capability/model.mjs",
    "/capability/view.mjs",
    "/foundation/accessibility.mjs",
    "/foundation/bootstrap-controller.mjs",
    "/foundation/current-view.mjs",
    "/foundation/i18n-home.mjs",
    "/foundation/i18n.mjs",
    "/foundation/i18n-learning.mjs",
    "/foundation/i18n-school.mjs",
    "/foundation/i18n-shell.mjs",
    "/foundation/i18n-teacher.mjs",
    "/foundation/primitives.mjs",
    "/component-catalog.mjs",
    "/components.css",
    "/corrections/corrections-fixture.mjs",
    "/corrections/corrections-model.mjs",
    "/corrections/corrections-messages.mjs",
    "/corrections/corrections-view.mjs",
    "/corrections/corrections.css",
    "/deep-link.mjs",
    "/foundation/defensive-state.mjs",
    "/foundation/domain-controller.mjs",
    "/foundation/i18n-atlas.mjs",
    "/episodes/episode-fixture.mjs",
    "/episodes/episode-model.mjs",
    "/episodes/episode-proof-view.mjs",
    "/episodes/episode-replay-view.mjs",
    "/episodes/episode-summary-view.mjs",
    "/episodes/episode-view.mjs",
    "/episodes/episode-view-shared.mjs",
    "/episodes/episodes.css",
    "/frame-explorer.css",
    "/frames/frame-contract.mjs",
    "/frames/frame-explorer.mjs",
    "/frames/frame-model.mjs",
    "/frames/frame-shell.mjs",
    "/evidence/evidence-messages.mjs",
    "/evidence/evidence-paint.mjs",
    "/evidence/evidence-record.mjs",
    "/evidence/evidence-view.mjs",
    "/evidence/evidence-query.mjs",
    "/evidence/evidence-markup.mjs",
    "/evidence/evidence.css",
    "/index.html",
    "/interactions/app-uri.mjs",
    "/interactions/compare.mjs",
    "/interactions/controller.mjs",
    "/interactions/dom-ref.mjs",
    "/interactions/interactions.css",
    "/interactions/model.mjs",
    "/interactions/operator-metadata.mjs",
    "/interactions/view.mjs",
    "/lineage/lineage-fixture.mjs",
    "/lineage/lineage-model.mjs",
    "/lineage/lineage-view.mjs",
    "/lineage/lineage.css",
    "/memory/memory-fixture.mjs",
    "/memory/memory-model.mjs",
    "/memory/memory-view.mjs",
    "/memory/memory.css",
    "/operate/operate-controller.mjs",
    "/operate/operate-model.mjs",
    "/operate/operate-view.mjs",
    "/operate/operate.css",
    "/neural/neural-fixture.mjs",
    "/neural/neural-model.mjs",
    "/neural/neural-view.mjs",
    "/neural/neural.css",
    "/foundation/renderer-ui.mjs",
    "/foundation/static-interactions.mjs",
    "/foundation/test-hooks.mjs",
    "/home/home-controller.mjs",
    "/home/home-model.mjs",
    "/home/home-view.mjs",
    "/home/home.css",
    "/renderer.mjs",
    "/resources/resource-controller.mjs",
    "/resources/resource-fixture.mjs",
    "/resources/resource-model.mjs",
    "/resources/resource-view.mjs",
    "/resources/resource-format.mjs",
    "/resources/resource-messages.mjs",
    "/resources/resources.css",
    "/school/school-fixture.mjs",
    "/school/school-model.mjs",
    "/school/school-view.mjs",
    "/school/school.css",
    "/school/curriculum-atlas-fixture.mjs",
    "/school/curriculum-atlas-markup.mjs",
    "/school/curriculum-atlas-model.mjs",
    "/school/curriculum-atlas-view.mjs",
    "/school/curriculum-atlas.css",
    "/school/school-domain-controller.mjs",
    "/salience/salience-fixture.mjs",
    "/salience/salience-events-fixture.mjs",
    "/salience/salience-aggregation-view.mjs",
    "/salience/salience-messages.mjs",
    "/salience/salience-model.mjs",
    "/salience/salience-observation-view.mjs",
    "/salience/salience-routing-view.mjs",
    "/salience/salience-view.mjs",
    "/salience/salience-view-shared.mjs",
    "/salience/salience.css",
    "/settings.mjs",
    "/shell-state.mjs",
    "/shell.css",
    "/teacher/teacher-fixture.mjs",
    "/teacher/teacher-comparison-view.mjs",
    "/teacher/teacher-fidelity-view.mjs",
    "/teacher/teacher-model.mjs",
    "/teacher/teacher-roster-view.mjs",
    "/teacher/teacher-view.mjs",
    "/teacher/teacher-view-shared.mjs",
    "/teacher/teacher-comparison.css",
    "/teacher/teacher-core.css",
    "/teacher/teacher-detail.css",
    "/teacher/teacher.css",
    "/visual-fixtures.mjs",
    "/visual-language.mjs",
    "/visual-tokens.css",
  ].sort());
});

test("renderer protocol refuses traversal, query aliases and untrusted origins", () => {
  const root = "/Applications/Bilqis/MissionControl/renderer";
  for (const requestUrl of [
    "bamf-mc://app/../main.cjs",
    "bamf-mc://app/%2e%2e/main.cjs",
    "bamf-mc://app/index.html?file=../../main.cjs",
    "bamf-mc://other/index.html",
    "file:///etc/passwd",
    "https://evil.example/index.html",
  ]) {
    assert.equal(assetPathForRendererRequest(requestUrl, root), null, requestUrl);
  }
  assert.throws(
    () => assetPathForRendererRequest(RENDERER_ENTRY_URL, "relative/renderer"),
    /BAMF_GUI20_RENDERER_ASSET_ROOT_REQUIRED/,
  );
});

test("protocol handler never asks net.fetch for a non-allowlisted local file", async () => {
  let handler;
  const fetched = [];
  registerMissionControlProtocol({
    protocol: {
      handle(scheme, next) {
        assert.equal(scheme, "bamf-mc");
        handler = next;
      },
    },
    net: {
      fetch(url) {
        fetched.push(url);
        return Promise.resolve(new Response("ok"));
      },
    },
    assetRoot: "/Applications/Bilqis/MissionControl/renderer",
  });

  const allowed = await handler({ url: RENDERER_ENTRY_URL });
  assert.equal(await allowed.text(), "ok");
  assert.match(fetched[0], /^file:\/\/\/Applications\/Bilqis\/MissionControl\/renderer\/index\.html$/);

  const denied = await handler({ url: "bamf-mc://app/../main.cjs" });
  assert.equal(denied.status, 404);
  assert.equal(fetched.length, 1);
});

test("packaged renderer assets include every local HTML and JavaScript dependency", () => {
  const root = path.resolve(__dirname, "../../renderer");
  for (const asset of RENDERER_ASSETS.values()) {
    const source = fs.readFileSync(path.join(root, asset), "utf8");
    const dependencies = asset.endsWith(".html")
      ? [...source.matchAll(/(?:src|href)="\.\/([^"#]+)"/g)].map(match => match[1])
      : asset.endsWith(".mjs") ? [...source.matchAll(/(?:from\s+|import\s*)["'](\.\.?\/[^"']+)["']/g)].map(match => match[1]) : [];
    for (const dependency of dependencies) {
      const resolved = path.posix.normalize(path.posix.join(path.posix.dirname(asset), dependency));
      assert.ok(RENDERER_ASSETS.has(`/${resolved}`), `${asset} requires ${dependency}`);
    }
  }
  assert.equal(assetPathForRendererRequest("bamf-mc://app/fixtures/frame-inspections-v1.json", root), null);
});
