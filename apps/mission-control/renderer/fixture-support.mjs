import { fixtureQuery, FIXTURE_RUN } from "./capability/fixture.mjs";
import { createAtlasFixtureApi } from "./atlas/atlas-fixture.mjs";
import { CORRECTION_FIXTURE_SUPPORT } from "./corrections/corrections-fixture.mjs";
import { renderEpisodesView } from "./episodes/episode-view.mjs";
import { referenceHomeProjection } from "./home/home-fixture.mjs";
import { compareStableRefs } from "./interactions/compare.mjs";
import { renderLineageView } from "./lineage/lineage-view.mjs";
import { renderMemoryView } from "./memory/memory-view.mjs";
import { renderNeuralView } from "./neural/neural-view.mjs";
import { RESOURCE_FIXTURE_SUPPORT } from "./resources/resource-fixture-state.mjs";
import { renderSalienceView } from "./salience/salience-view.mjs";
import {
  activateSchoolDomain,
  invalidateSchoolDomainRequests,
} from "./school/school-domain-controller.mjs";
import { renderTeacherView } from "./teacher/teacher-view.mjs";

export const capability = Object.freeze({
  query: fixtureQuery,
  runId: FIXTURE_RUN,
  generation: 3,
});

export const atlas = Object.freeze({ api: createAtlasFixtureApi() });

export const currentViews = Object.freeze({
  renderEpisodesView,
  renderLineageView,
  renderMemoryView,
  renderNeuralView,
  renderSalienceView,
  renderTeacherView,
});

export const corrections = CORRECTION_FIXTURE_SUPPORT;

export const home = Object.freeze({ referenceProjection: referenceHomeProjection });
export const interactions = Object.freeze({ compareRefs: compareStableRefs });
export const resources = Object.freeze({ fixtureSupport: RESOURCE_FIXTURE_SUPPORT });
export const salience = Object.freeze({ renderSalienceView });
export const teacher = Object.freeze({ renderTeacherView });
export const school = Object.freeze({
  activateSchoolDomain,
  invalidateSchoolDomainRequests,
});
