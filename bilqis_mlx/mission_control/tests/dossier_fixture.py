"""Regenerate GUI05 synthetic pages through the actual typed CP03 catalog."""
from dataclasses import replace
import json
from pathlib import Path

from bilqis_mlx.mission_control import (
    CapabilitySnapshot, MissionControlQueryCatalog, QueryFamily, QueryMode,
    QueryRequest, RecordMeta, RunRef, CoverageState, AuthorityClass, ValueOrigin,
)
from bilqis_mlx.mission_control.contracts.dossier import CapabilityDossier, DossierEntry, DossierValue
from bilqis_mlx.mission_control.tests.samples import value


RUN_ID = "fixture:gui05"
SCHEMA = CapabilityDossier.SCHEMA


def metadata(record_id, generation, refs=()):
    run = RunRef(RUN_ID, "1" * 64, generation, str(generation) * 64,
                 "2" * 64, "3" * 64, "4" * 64, "5" * 64)
    return RecordMeta(record_id, run, 200, 100 + generation, 100 + generation,
                      CoverageState.COMPLETE, AuthorityClass.DERIVED,
                      ("source:logic-r2",), refs, ("receipt:fixture-gui05",))


def records():
    rows = []
    for generation in (1, 2, 3):
        for capability, name in (("B.AND", "Conjunction"), ("B.NOT", "Negation")):
            entries = []
            def entry(section, kind, label, facts, *, at=generation, related=None, ref=None):
                identifier = f"{capability}:{generation}:{len(entries)}"
                reference = ref or f"evidence:{identifier}"
                entries.append(DossierEntry(identifier, section, kind, label, at, 100 + at,
                    tuple(DossierValue(k, value(v, units=None, origin=
                        ValueOrigin.SOURCE_AUTHORITATIVE if section in ("sources", "dependencies")
                        else ValueOrigin.MEASURED)) for k, v in facts.items()),
                    (reference,), *(related or (None, None))))
            now = {1: 9, 2: 7, 3: 10}[generation]
            for cohort, score in (("fresh", now), ("protected", 11)):
                ref = f"evidence:{capability}:{cohort}:{generation}"
                rows.append(CapabilitySnapshot(metadata(ref, generation), capability,
                    "B", "MEASURED", value(score), value(12), value(12 - score)))
                entry("performance", cohort, f"{cohort.title()} cohort · exact results",
                      dict(cohort=f"cohort:{cohort}:{generation}", correct=score, total=12,
                           target_delta=now - 7, protected_delta=-1), ref=ref)
            entry("performance", "retained", "Candidate retained", dict(candidate_outcome="ACCEPTED", target_delta=3),
                  related=("episode", f"episode:retained-g{generation}"))
            entry("performance", "rejected", "Candidate rejected", dict(candidate_outcome="REJECTED", protected_delta=-3),
                  related=("episode", f"episode:rejected-g{generation}"))
            entry("teaching", "strategy", "Contrastive source lessons", dict(strategy="contrastive-01", visits=10,
                  success_rate="40%", no_gain_rate="40%", interference_rate="20%", fidelity="F2 observed",
                  lesson_family="logic:and:contrast"))
            entry("teaching", "no-gain", "No measurable target gain", dict(strategy="direct-02", visits=3, no_gain_rate="100%"))
            entry("teaching", "interference", "Destructive interference observed", dict(strategy="contrastive-01", visits=2,
                  interference_rate="100%"))
            entry("sources", "admitted", "Admitted source family", dict(family="typed:boolean", state="ADMITTED",
                  source_revision="source:r2", rubric_revision="rubric:r3"))
            entry("sources", "held", "Composition family held", dict(family="boolean:composition", state="HELD",
                  hold_reason="SOURCE_ORACLE_NOT_QUALIFIED", source_revision="source:r2", rubric_revision="rubric:r3"))
            entry("dependencies", "prerequisite", "Exact prerequisite", dict(relation="prerequisite"),
                  related=("capability", "B.NOT" if capability == "B.AND" else "B.AND"))
            entry("dependencies", "consumer", "Exact consumer", dict(relation="consumer"), related=("capability", "B.AND"))
            entry("dependencies", "semantic", "Related semantic frame", dict(semantic_id="sem:logic.and", frame_id="frame:binary"),
                  related=("semantic", "sem:logic.and"))
            for at, kind, label in ((1, "gain", "Gain recorded · 9 / 12"),
                (2, "regression", "Regression recorded · 7 / 12"), (3, "recovery", "Recovery recorded · 10 / 12")):
                if at <= generation:
                    entry("history", kind, label, dict(event=kind), at=at)
            entry("history", "plateau", "No-gain visit recorded", dict(event="plateau", candidate_outcome="REJECTED"))
            entry("history", "correction", "Source revision recorded", dict(event="source_revision", source_revision="source:r2"))
            refs = tuple(dict.fromkeys(ref for item in entries for ref in item.refs))
            rows.append(CapabilityDossier(metadata(f"dossier:{capability}:{generation}", generation, refs),
                capability, name, value(now), value(10 if generation == 3 else 9), value(12), value(12 - now), value("WATCH", units=None),
                value("ELIGIBLE", units=None), value("QUALIFIED", units=None),
                value("PARTIALLY_HELD", units=None, origin=ValueOrigin.SOURCE_AUTHORITATIVE), tuple(entries)))
    return rows


def key(q):
    return json.dumps([q.family.value, q.generation, q.schema_version, q.record_id,
                       q.reference, q.cursor, q.mode.value], separators=(",", ":"))


def generate():
    rows = records()
    catalog = MissionControlQueryCatalog(rows)
    pages = {}
    for mode in QueryMode:
        for generation in (1, 2, 3):
            requests = [QueryRequest(QueryFamily.CAPABILITY, mode, run_id=RUN_ID,
                                    generation=generation, schema_version=SCHEMA)]
            for row in rows:
                if row.meta.run.generation != generation:
                    continue
                requests.append(QueryRequest(QueryFamily.CAPABILITY, mode, run_id=RUN_ID,
                    generation=generation, record_id=row.meta.record_id))
                for ref in row.meta.evidence_refs:
                    requests.append(QueryRequest(QueryFamily.REFERENCE, mode, run_id=RUN_ID,
                        generation=generation, reference=ref))
            for request in requests:
                pages[key(request)] = catalog.encode_page(catalog.query(request))
    return pages


if __name__ == "__main__":
    target = Path("apps/mission-control/renderer/capability/fixture-data.mjs")
    target.write_text("// Generated by mission_control.tests.dossier_fixture; synthetic CP03 pages.\nexport default " + json.dumps(generate(), separators=(",", ":")) + ";\n")
