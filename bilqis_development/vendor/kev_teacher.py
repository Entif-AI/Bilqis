"""Bounded, trace-preserving adapter for the operator-owned Kev service."""
from __future__ import annotations

import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from typing import Any


EXPECTED_RUN = "jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52"
MIN_MARGIN = 0.05
_MAX_RESPONSE_BYTES = 1_000_000
_TIMEOUT_SECONDS = 120
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_RUNTIME_BINDING_FIELDS = ("run", "backend", "lora", "device", "dtype")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: Any, **kwargs: Any) -> None:
        raise ValueError("LOCAL_SERVICE_REDIRECT_FORBIDDEN")


def _endpoint(endpoint: str) -> str:
    parsed = urllib.parse.urlparse(endpoint)
    if (parsed.scheme != "http" or parsed.hostname not in _LOOPBACK_HOSTS or parsed.path not in ("", "/")
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("LOCAL_ENDPOINT_ONLY")
    return endpoint.rstrip("/")


def _number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(label)
    return float(value)


def validate_runtime(value: Any) -> dict[str, Any]:
    """Validate and return the one native Kev runtime identity."""
    if not isinstance(value, dict) or set(value) != {"models"} or not isinstance(value["models"], list):
        raise ValueError("KEV_RUNTIME_RESPONSE")
    matches = [model for model in value["models"] if isinstance(model, dict) and model.get("name") == "kev-latest"]
    if len(matches) != 1:
        raise ValueError("KEV_RUNTIME_MODEL")
    model = matches[0]
    required = {"name", "run", "backend", "lora", "device", "dtype"}
    if not required <= set(model):
        raise ValueError("KEV_RUNTIME_FIELDS")
    if (model["run"] != EXPECTED_RUN or model["backend"] != "mlx" or model["lora"] != 16
            or model["device"] != "mps" or model["dtype"] != "bfloat16"):
        raise ValueError("KEV_RUNTIME_IDENTITY")
    return dict(model)


def _runtime_binding(identity: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(identity[field] for field in _RUNTIME_BINDING_FIELDS)


def validate_response(response: Any, offered_ids: list[str]) -> dict[str, Any]:
    """Validate the native choice response against exactly the offered panel."""
    if not isinstance(response, dict) or "answers" not in response or not isinstance(response["answers"], dict):
        raise ValueError("KEV_RESPONSE_ANSWERS")
    answers = response["answers"]
    if set(answers) != {"decision"} or not isinstance(answers["decision"], dict):
        raise ValueError("KEV_RESPONSE_DECISION")
    decision = answers["decision"]
    if set(decision) != {"type", "choice", "confidence", "probabilities"}:
        raise ValueError("KEV_RESPONSE_FIELDS")
    if decision["type"] != "choice" or decision["choice"] not in offered_ids:
        raise ValueError("KEV_RESPONSE_CHOICE")
    if type(decision["confidence"]) is not float:
        raise ValueError("KEV_RESPONSE_CONFIDENCE")
    confidence = _number(decision["confidence"], "KEV_RESPONSE_CONFIDENCE")
    probabilities = decision["probabilities"]
    if not isinstance(probabilities, dict) or set(probabilities) != set(offered_ids):
        raise ValueError("KEV_RESPONSE_PROBABILITIES")
    normalized = {candidate_id: _number(probabilities[candidate_id], "KEV_RESPONSE_PROBABILITIES")
                  for candidate_id in offered_ids}
    tolerance = len(offered_ids) * 0.00005 + 0.000001
    if abs(sum(normalized.values()) - 1) > tolerance:
        raise ValueError("KEV_RESPONSE_PROBABILITY_SUM")
    maximum = max(normalized.values())
    if normalized[decision["choice"]] != maximum:
        raise ValueError("KEV_RESPONSE_SELECTED_NOT_ARGMAX")
    return {"choice": decision["choice"], "confidence": confidence, "probabilities": normalized}


class KevTeacher:
    """A single-request Kev teacher that always retains the decision trace."""

    MIN_MARGIN = MIN_MARGIN

    def __init__(self, endpoint: str = "http://127.0.0.1:8008", *, opener: Any = None):
        self.endpoint = _endpoint(endpoint)
        self._opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
        self.identity = validate_runtime(self._json("/v1/models")[0])

    def _json(self, path: str, payload: dict[str, Any] | None = None) -> Any:
        body = None if payload is None else json.dumps(payload, separators=(",", ":"), ensure_ascii=True,
                                                          allow_nan=False, sort_keys=False).encode()
        request = urllib.request.Request(self.endpoint + path, data=body, headers={"Content-Type": "application/json"})
        with self._opener.open(request, timeout=_TIMEOUT_SECONDS) as response:
            raw = response.read(_MAX_RESPONSE_BYTES + 1)
        if len(raw) > _MAX_RESPONSE_BYTES:
            raise ValueError("LOCAL_RESPONSE_TOO_LARGE")
        return json.loads(raw), body

    def _verify_runtime(self, trace: dict[str, Any], phase: str) -> dict[str, Any]:
        observed, _ = self._json("/v1/models")
        try:
            identity = validate_runtime(observed)
        except Exception as exc:
            trace["runtime_verifications"].append({"phase": phase, "observed": observed,
                                                   "error": {"type": type(exc).__name__, "message": str(exc)}})
            raise
        trace["runtime_verifications"].append({"phase": phase, "identity": identity})
        return identity

    @staticmethod
    def _candidates(candidates: list[dict[str, str]]) -> tuple[list[str], dict[str, str]]:
        if not isinstance(candidates, list) or not 2 <= len(candidates) <= 16:
            raise ValueError("KEV_CANDIDATE_COUNT")
        offered_ids: list[str] = []
        criteria: dict[str, str] = {}
        for candidate in candidates:
            if not isinstance(candidate, dict) or set(candidate) != {"candidate_id", "description"}:
                raise ValueError("KEV_CANDIDATE_FIELDS")
            candidate_id, description = candidate["candidate_id"], candidate["description"]
            if not isinstance(candidate_id, str) or not candidate_id or not isinstance(description, str):
                raise ValueError("KEV_CANDIDATE_VALUE")
            if candidate_id in criteria:
                raise ValueError("KEV_CANDIDATE_IDENTITY")
            offered_ids.append(candidate_id)
            criteria[candidate_id] = description
        return offered_ids, criteria

    def score(self, state_text: str, question: str, candidates: list[dict[str, str]], binding: Any = None) -> dict[str, Any]:
        if not isinstance(state_text, str) or not isinstance(question, str):
            raise ValueError("KEV_STATE_QUESTION")
        offered_ids, criteria = self._candidates(candidates)
        payload = {"model": "kev-latest", "state": state_text, "questions": {"decision": {
            "type": "choice", "instructions": question, "criteria": criteria}}}
        serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=True, allow_nan=False, sort_keys=False)
        trace: dict[str, Any] = {
            "payload": payload,
            "serialized_request": serialized,
            "request_sha256": hashlib.sha256(serialized.encode()).hexdigest(),
            "offered_candidate_ids": offered_ids,
            "binding": binding,
            "runtime": None,
            "runtime_verifications": [],
            "choice_calls": 0,
        }
        started = time.perf_counter()
        try:
            before = self._verify_runtime(trace, "before")
            trace["runtime_before"] = before
            trace["runtime"] = before
            trace["choice_calls"] = 1
            response, body = self._json("/v1/systemone", payload)
            trace["response"] = response
            if isinstance(response, dict) and "usage" in response:
                trace["usage"] = response["usage"]
            after = self._verify_runtime(trace, "after")
            trace["runtime_after"] = after
            if _runtime_binding(before) != _runtime_binding(after):
                raise ValueError("KEV_RUNTIME_SWAP")
            trace["runtime"] = after
            self.identity = after
            if body != serialized.encode():
                raise ValueError("KEV_REQUEST_SERIALIZATION")
            decision = validate_response(response, offered_ids)
            ordered = decision["probabilities"]
            values = sorted(ordered.values(), reverse=True)
            margin = values[0] - values[1]
            trace.update({"response": response, "probabilities": ordered, "choice": decision["choice"],
                          "confidence": decision["confidence"], "margin": margin,
                          "wall_seconds": time.perf_counter() - started,
                          "status": "LOW_MARGIN" if margin < self.MIN_MARGIN else "OK"})
        except Exception as exc:
            if "runtime_after" not in trace:
                trace["runtime"] = None
            trace.update({"response": locals().get("response"), "wall_seconds": time.perf_counter() - started,
                          "status": "ERROR", "error": {"type": type(exc).__name__, "message": str(exc)}})
        return trace
