const QUERY_SCHEMA = "bilqis.bamf.control-plane.query/v1";

export const LEARNING_EPISODE_SCHEMA =
  "bilqis.bamf.mission-control.learning-episode/v1";
export const CANDIDATE_DECISION_SCHEMA =
  "bilqis.bamf.mission-control.candidate-decision/v1";

export function buildLearningQuery(context, recordId = null) {
  const historical = context?.mode === "HISTORICAL";
  return {
    schema: QUERY_SCHEMA,
    family: "episode",
    mode: historical ? "historical" : "current",
    run_id: context?.runId ?? null,
    record_id: recordId,
    schema_version: null,
    generation: context?.generation ?? null,
    frontier_id: null,
    as_of: null,
    reference: null,
    cursor: null,
    limit: 32,
  };
}

export function recordId(record) {
  return record?.meta?.record_id ?? "";
}

export function recordKind(record) {
  if (record?.schema_version === LEARNING_EPISODE_SCHEMA) return "episode";
  if (record?.schema_version === CANDIDATE_DECISION_SCHEMA) return "candidate";
  return "evidence";
}

export function recordLabel(record, unknown = "Unknown") {
  const identity = record?.episode_id ?? record?.candidate_id ?? recordId(record);
  return (record?.capability_id ?? unknown) + " · " + identity;
}

export function assertLearningPage(value) {
  if (value?.accepted === true) return value;
  throw new Error(value?.reason ?? "LEARNING_QUERY_REJECTED");
}
