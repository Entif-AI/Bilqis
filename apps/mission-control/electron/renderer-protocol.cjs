"use strict";

const path = require("node:path");
const { pathToFileURL } = require("node:url");

const { RENDERER_HOST, RENDERER_SCHEME } = require("./renderer-location.cjs");

const RENDERER_ASSETS = Object.freeze(new Map([
  ["/atlas/atlas-controller.mjs", "atlas/atlas-controller.mjs"],
  ["/atlas/semantic-atlas.css", "atlas/semantic-atlas.css"],
  ["/atlas/semantic-atlas.mjs", "atlas/semantic-atlas.mjs"],
  ["/capability/app.mjs", "capability/app.mjs"],
  ["/capability/controller.mjs", "capability/controller.mjs"],
  ["/capability/dossier.css", "capability/dossier.css"],
  ["/capability/fixture-data.mjs", "capability/fixture-data.mjs"],
  ["/capability/fixture.mjs", "capability/fixture.mjs"],
  ["/capability/model.mjs", "capability/model.mjs"],
  ["/capability/view.mjs", "capability/view.mjs"],
  ["/component-catalog.mjs", "component-catalog.mjs"],
  ["/components.css", "components.css"],
  ["/corrections/corrections-fixture.mjs", "corrections/corrections-fixture.mjs"],
  ["/corrections/corrections-model.mjs", "corrections/corrections-model.mjs"],
  ["/corrections/corrections-view.mjs", "corrections/corrections-view.mjs"],
  ["/corrections/corrections.css", "corrections/corrections.css"],
  ["/foundation/accessibility.mjs", "foundation/accessibility.mjs"],
  ["/foundation/bootstrap-controller.mjs", "foundation/bootstrap-controller.mjs"],
  ["/foundation/current-view.mjs", "foundation/current-view.mjs"],
  ["/foundation/defensive-state.mjs", "foundation/defensive-state.mjs"],
  ["/foundation/domain-controller.mjs", "foundation/domain-controller.mjs"],
  ["/deep-link.mjs", "deep-link.mjs"],
  ["/episodes/episode-fixture.mjs", "episodes/episode-fixture.mjs"],
  ["/episodes/episode-model.mjs", "episodes/episode-model.mjs"],
  ["/episodes/episode-view.mjs", "episodes/episode-view.mjs"],
  ["/episodes/episodes.css", "episodes/episodes.css"],
  ["/frame-explorer.css", "frame-explorer.css"],
  ["/frames/frame-contract.mjs", "frames/frame-contract.mjs"],
  ["/frames/frame-explorer.mjs", "frames/frame-explorer.mjs"],
  ["/frames/frame-model.mjs", "frames/frame-model.mjs"],
  ["/frames/frame-shell.mjs", "frames/frame-shell.mjs"],
  ["/evidence/evidence-view.mjs", "evidence/evidence-view.mjs"],
  ["/evidence/evidence-query.mjs", "evidence/evidence-query.mjs"],
  ["/evidence/evidence-markup.mjs", "evidence/evidence-markup.mjs"],
  ["/evidence/evidence.css", "evidence/evidence.css"],
  ["/index.html", "index.html"],
  ["/lineage/lineage-fixture.mjs", "lineage/lineage-fixture.mjs"],
  ["/lineage/lineage-model.mjs", "lineage/lineage-model.mjs"],
  ["/lineage/lineage-view.mjs", "lineage/lineage-view.mjs"],
  ["/lineage/lineage.css", "lineage/lineage.css"],
  ["/memory/memory-fixture.mjs", "memory/memory-fixture.mjs"],
  ["/memory/memory-model.mjs", "memory/memory-model.mjs"],
  ["/memory/memory-view.mjs", "memory/memory-view.mjs"],
  ["/memory/memory.css", "memory/memory.css"],
  ["/operate/operate-controller.mjs", "operate/operate-controller.mjs"],
  ["/operate/operate-model.mjs", "operate/operate-model.mjs"],
  ["/operate/operate-view.mjs", "operate/operate-view.mjs"],
  ["/operate/operate.css", "operate/operate.css"],
  ["/neural/neural-fixture.mjs", "neural/neural-fixture.mjs"],
  ["/neural/neural-model.mjs", "neural/neural-model.mjs"],
  ["/neural/neural-view.mjs", "neural/neural-view.mjs"],
  ["/neural/neural.css", "neural/neural.css"],
  ["/foundation/renderer-ui.mjs", "foundation/renderer-ui.mjs"],
  ["/foundation/static-interactions.mjs", "foundation/static-interactions.mjs"],
  ["/home/home-controller.mjs", "home/home-controller.mjs"],
  ["/home/home-model.mjs", "home/home-model.mjs"],
  ["/home/home-view.mjs", "home/home-view.mjs"],
  ["/home/home.css", "home/home.css"],
  ["/interactions/app-uri.mjs", "interactions/app-uri.mjs"],
  ["/interactions/compare.mjs", "interactions/compare.mjs"],
  ["/interactions/controller.mjs", "interactions/controller.mjs"],
  ["/interactions/dom-ref.mjs", "interactions/dom-ref.mjs"],
  ["/interactions/interactions.css", "interactions/interactions.css"],
  ["/interactions/model.mjs", "interactions/model.mjs"],
  ["/interactions/operator-metadata.mjs", "interactions/operator-metadata.mjs"],
  ["/interactions/view.mjs", "interactions/view.mjs"],
  ["/renderer.mjs", "renderer.mjs"],
  ["/resources/resource-controller.mjs", "resources/resource-controller.mjs"],
  ["/resources/resource-fixture.mjs", "resources/resource-fixture.mjs"],
  ["/resources/resource-model.mjs", "resources/resource-model.mjs"],
  ["/resources/resource-view.mjs", "resources/resource-view.mjs"],
  ["/resources/resources.css", "resources/resources.css"],
  ["/school/school-fixture.mjs", "school/school-fixture.mjs"],
  ["/school/school-model.mjs", "school/school-model.mjs"],
  ["/school/school-view.mjs", "school/school-view.mjs"],
  ["/school/school.css", "school/school.css"],
  ["/school/curriculum-atlas-fixture.mjs", "school/curriculum-atlas-fixture.mjs"],
  ["/school/curriculum-atlas-markup.mjs", "school/curriculum-atlas-markup.mjs"],
  ["/school/curriculum-atlas-model.mjs", "school/curriculum-atlas-model.mjs"],
  ["/school/curriculum-atlas-view.mjs", "school/curriculum-atlas-view.mjs"],
  ["/school/curriculum-atlas.css", "school/curriculum-atlas.css"],
  ["/school/school-domain-controller.mjs", "school/school-domain-controller.mjs"],
  ["/salience/salience-fixture.mjs", "salience/salience-fixture.mjs"],
  ["/salience/salience-events-fixture.mjs", "salience/salience-events-fixture.mjs"],
  ["/salience/salience-model.mjs", "salience/salience-model.mjs"],
  ["/salience/salience-view.mjs", "salience/salience-view.mjs"],
  ["/salience/salience.css", "salience/salience.css"],
  ["/settings.mjs", "settings.mjs"],
  ["/shell-state.mjs", "shell-state.mjs"],
  ["/shell.css", "shell.css"],
  ["/teacher/teacher-fixture.mjs", "teacher/teacher-fixture.mjs"],
  ["/teacher/teacher-model.mjs", "teacher/teacher-model.mjs"],
  ["/teacher/teacher-view.mjs", "teacher/teacher-view.mjs"],
  ["/teacher/teacher.css", "teacher/teacher.css"],
  ["/visual-fixtures.mjs", "visual-fixtures.mjs"],
  ["/visual-language.mjs", "visual-language.mjs"],
  ["/visual-tokens.css", "visual-tokens.css"],
]));

function assetPathForRendererRequest(requestUrl, assetRoot) {
  if (typeof assetRoot !== "string" || assetRoot.length === 0 || !path.isAbsolute(assetRoot)) {
    throw new TypeError("BAMF_GUI20_RENDERER_ASSET_ROOT_REQUIRED");
  }
  let request;
  try {
    request = new URL(requestUrl);
  } catch (_error) {
    return null;
  }
  if (request.protocol !== `${RENDERER_SCHEME}:` || request.hostname !== RENDERER_HOST ||
      request.username || request.password || request.port || request.search) {
    return null;
  }
  const relative = RENDERER_ASSETS.get(request.pathname);
  return relative ? path.join(assetRoot, relative) : null;
}

function registerMissionControlProtocol({ protocol, net, assetRoot }) {
  if (!protocol || typeof protocol.handle !== "function") {
    throw new TypeError("BAMF_GUI20_PROTOCOL_REQUIRED");
  }
  if (!net || typeof net.fetch !== "function") {
    throw new TypeError("BAMF_GUI20_NET_REQUIRED");
  }
  protocol.handle(RENDERER_SCHEME, (request) => {
    const asset = assetPathForRendererRequest(request.url, assetRoot);
    if (asset === null) {
      return new Response("Not found", {
        status: 404,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
    return net.fetch(pathToFileURL(asset).href);
  });
}

module.exports = {
  RENDERER_ASSETS,
  assetPathForRendererRequest,
  registerMissionControlProtocol,
};
