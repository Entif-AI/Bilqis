import { LEARNING_MESSAGES } from "./messages/learning.mjs";
import { ATLAS_MESSAGES } from "./messages/atlas.mjs";
import { HOME_MESSAGES } from "./messages/home.mjs";
import { INVESTIGATION_MESSAGES } from "./messages/investigation.mjs";
import { SHELL_MESSAGES } from "./messages/shell.mjs";
import { MODEL_MESSAGES } from "./messages/model.mjs";
import { MEMORY_MESSAGES } from "../memory/memory-messages.mjs";
import { SCHOOL_MESSAGES } from "./messages/school.mjs";
import { TEACHER_MESSAGES } from "./messages/teacher.mjs";

const EN_US = Object.freeze({
  "foundation.catalog.eyebrow": "GUI02 · reusable system",
  "foundation.catalog.title": "Scientific visual language",
  "foundation.catalog.summary": "Color reinforces meaning; shape, text, border and structure carry it first.",
  "foundation.catalog.status.title": "Semantic status grammar",
  "foundation.catalog.evidence.title": "Evidence and authority",
  "foundation.catalog.defensive.title": "Defensive state surfaces",
  "foundation.catalog.provenance.title": "Provenance, identity and alerting",
  "foundation.catalog.fixtures.title": "Visual-regression fixture states",
  "foundation.catalog.historical.label": "HISTORICAL / AS-OF",
  "foundation.catalog.historical.detail": "Inspection only · generation {generation} · not live learner state",
  "foundation.catalog.metric.retainedAccuracy": "Retained accuracy",
  "foundation.catalog.metric.generationComparison": "Generation comparison",
  "foundation.catalog.metric.sourceAuthority": "S · source",
  "foundation.catalog.metric.derivedAuthority": "D · derived",
  "foundation.catalog.metric.sameRubric": "{from} → {to} · same rubric",
  "foundation.catalog.metric.trend": "Trend rose from {from} to {to} percent",
  "foundation.catalog.provenance.learnedProjection": "D · learned projection",
  "foundation.catalog.identity.runGeneration": "RUN {runId} / GEN {generation}",
  "foundation.catalog.evidence.verifiedChain": "Verified source chain",
  "foundation.catalog.evidence.explanation": "Expandable evidence preserves exact identity and provenance without turning every table row into a wall of metadata.",
  "foundation.catalog.alert.attention": "Attention",
  "foundation.catalog.alert.diskReserve": "Disk reserve is approaching the configured boundary.",
  "foundation.catalog.legend.label": "Graph legend",
  "foundation.catalog.legend.source": "Source authority",
  "foundation.catalog.legend.derived": "Derived relation",
  "foundation.catalog.legend.held": "Held edge",
  "foundation.status.healthy": "Healthy",
  "foundation.status.attention": "Attention",
  "foundation.status.invalid": "Invalid evidence / custody",
  "foundation.status.held": "Held",
  "foundation.status.unavailable": "Unavailable",
  "foundation.status.denied": "Denied",
  "foundation.status.unknown": "Unknown",
  "foundation.status.stale": "Stale",
  "foundation.status.partial": "Partial",
  "foundation.status.proposed": "Proposed",
  "foundation.status.accepted": "Accepted",
  "foundation.status.attempted": "Attempted",
  "foundation.status.reconciled": "Reconciled",
  "foundation.status.live": "LIVE",
  "foundation.status.historical": "HISTORICAL / AS-OF",
  "foundation.evidence.measured": "Measured",
  "foundation.evidence.inferred": "Estimated / inferred",
  "foundation.authority.source": "Source-authoritative",
  "foundation.authority.derived": "Learned / derived",
  "foundation.defensive.live.label": "Live service",
  "foundation.defensive.live.description": "Current control-plane context is live and mutation may be offered through the accepted command contract.",
  "foundation.defensive.loading.label": "Loading",
  "foundation.defensive.loading.description": "Establishing the local control-plane session and requesting a verified snapshot.",
  "foundation.defensive.progressive.label": "Progressive data",
  "foundation.defensive.progressive.description": "Verified data is arriving incrementally. Missing fields remain explicitly incomplete.",
  "foundation.defensive.empty.label": "Empty",
  "foundation.defensive.empty.description": "The verified scope contains no records. Empty is not unavailable or denied.",
  "foundation.defensive.stale.label": "Stale",
  "foundation.defensive.stale.description": "The last verified context is retained for inspection but is not current enough for mutation.",
  "foundation.defensive.partial.label": "Partial",
  "foundation.defensive.partial.description": "Only part of the requested evidence is available. Missing evidence remains explicit.",
  "foundation.defensive.offline.label": "Offline",
  "foundation.defensive.offline.description": "The local service is disconnected. Verified cached or previously received evidence is inspection-only.",
  "foundation.defensive.denied.label": "Denied",
  "foundation.defensive.denied.description": "The current session is not authorized for this surface. No mutation is offered.",
  "foundation.defensive.revoked.label": "Revoked",
  "foundation.defensive.revoked.description": "Previously available authority was revoked. Existing evidence may be inspected, but no action may proceed.",
  "foundation.defensive.unavailable.label": "Unavailable",
  "foundation.defensive.unavailable.description": "The requested service or evidence surface is not available. This is distinct from an empty result.",
  "foundation.defensive.incompatibleVersion.label": "Incompatible version",
  "foundation.defensive.incompatibleVersion.description": "The renderer and local service cannot establish a compatible contract. Inspection is limited to verified prior evidence.",
  "foundation.defensive.timeout.label": "Timeout",
  "foundation.defensive.timeout.description": "The request did not complete in time. Existing verified context is preserved without claiming a terminal outcome.",
  "foundation.defensive.duplicateAction.label": "Duplicate action",
  "foundation.defensive.duplicateAction.description": "The command identity already exists. Read the existing operation receipt instead of repeating the effect.",
  "foundation.defensive.sessionRestarting.label": "Session restarting",
  "foundation.defensive.sessionRestarting.description": "The renderer session is being re-established. Current investigation context is preserved where safe.",
  "foundation.defensive.serviceRestarting.label": "Service restarting",
  "foundation.defensive.serviceRestarting.description": "The local control-plane service is restarting. Learner failure is not inferred from this UI condition.",
  "foundation.defensive.historicalUnavailable.label": "Historical reconstruction unavailable",
  "foundation.defensive.historicalUnavailable.description": "The requested historical state cannot be reconstructed from retained evidence.",
  "foundation.defensive.malformedPayload.label": "Malformed payload",
  "foundation.defensive.malformedPayload.description": "A payload failed the accepted Mission Control contract and was not rendered as trusted evidence.",
  "foundation.defensive.unsupportedPayload.label": "Unsupported payload",
  "foundation.defensive.unsupportedPayload.description": "The payload version or record type is not supported by this renderer.",
  "foundation.defensive.outcomeUnknown.label": "Outcome unknown",
  "foundation.defensive.outcomeUnknown.description": "A consequential operation may have executed, but its postcondition has not been proven. No automatic retry is offered.",
  "foundation.defensive.unknown.label": "State unknown",
  "foundation.defensive.unknown.description": "The renderer cannot yet classify the current service posture. Mutation remains unavailable.",
  "foundation.defensive.snapshot.cached": "Cached verified snapshot · inspection only",
  "foundation.defensive.snapshot.last": "Last verified snapshot · inspection only",
  "foundation.defensive.snapshot.current": "Current verified snapshot",
  "foundation.defensive.snapshot.none": "No verified snapshot available",
  "foundation.defensive.mutation.available": "Operator mutation contract available",
  "foundation.defensive.mutation.unavailable": "Mutation unavailable",
  "foundation.defensive.reconnect": "Reconnect",
  "foundation.bootstrap.connecting.label": "Connecting to Mission Control",
  "foundation.bootstrap.connecting.description": "Opening the local CP01 session and checking learner custody.",
  "foundation.bootstrap.discovering.label": "Control plane connected",
  "foundation.bootstrap.discovering.description": "CP01 is reachable. Discovering the accepted learner and Mission Control projection.",
  "foundation.bootstrap.telemetryPending.label": "Learner ready · telemetry starting",
  "foundation.bootstrap.telemetryPending.description": "The accepted learner is healthy, but Mission Control has not received its first operator projection yet. No fixture data is substituted.",
  "foundation.bootstrap.learnerUnavailable.label": "Control plane connected · learner unavailable",
  "foundation.bootstrap.learnerUnavailable.description": "CP01 is reachable, but the configured target does not currently expose an accepted learner.",
  "foundation.bootstrap.failed.label": "Mission Control bootstrap failed",
  "foundation.bootstrap.failed.description": "The local control-plane session or telemetry projection could not be established.",
  "foundation.bootstrap.starting.label": "Mission Control starting",
  "foundation.bootstrap.starting.description": "Establishing the local operator view.",
  "foundation.bootstrap.run": "Run {runId}",
  "foundation.bootstrap.generation": "generation {generation}",
  "foundation.bootstrap.detail": "Detail: {detail}",
  "foundation.bootstrap.noError": "No error reported",
  "foundation.bootstrap.announce.telemetryPending": "Learner connected. Waiting for Mission Control telemetry projection.",
  "foundation.bootstrap.announce.learnerUnavailable": "Control plane connected, but no accepted learner is ready.",
  "foundation.bootstrap.announce.noSnapshot": "{state}. No verified snapshot is available.",
  "foundation.bootstrap.announce.inspection": "{state}. Inspection-only evidence is shown.",
  "foundation.bootstrap.announce.live": "{state}. Live context established.",
  "foundation.fixture.live": "Live healthy",
  "foundation.fixture.unknown": "Freshness unknown",
  "foundation.fixture.historical": "Historical / as-of",
  "foundation.fixture.stale": "Stale connection",
  "foundation.fixture.denied": "Denied operation",
  "foundation.fixture.invalidEvidence": "Invalid evidence",
  ...ATLAS_MESSAGES,
  ...INVESTIGATION_MESSAGES,
  ...SHELL_MESSAGES,
  ...LEARNING_MESSAGES,
  ...HOME_MESSAGES,
  ...MODEL_MESSAGES,
  ...MEMORY_MESSAGES,
  ...SCHOOL_MESSAGES,
  ...TEACHER_MESSAGES,
});

export const DEFAULT_LOCALE = "en-US";
export const FOUNDATION_MESSAGES = Object.freeze({ [DEFAULT_LOCALE]: EN_US });

export function formatMessage(template, parameters = {}) {
  return String(template).replace(/\{([A-Za-z][A-Za-z0-9_]*)\}/g, (_match, name) => {
    if (!Object.hasOwn(parameters, name)) throw new TypeError(`I18N_PARAMETER_MISSING:${name}`);
    const value = parameters[name];
    if (value === null || value === undefined) throw new TypeError(`I18N_PARAMETER_INVALID:${name}`);
    return String(value);
  });
}

export function createTranslator({ locale = DEFAULT_LOCALE, messages = FOUNDATION_MESSAGES } = {}) {
  const catalog = messages[locale];
  if (!catalog) throw new RangeError(`I18N_LOCALE_UNSUPPORTED:${locale}`);
  return (key, parameters = {}) => {
    const template = catalog[key];
    if (template === undefined) throw new RangeError(`I18N_KEY_UNKNOWN:${key}`);
    return formatMessage(template, parameters);
  };
}

export const t = createTranslator();
