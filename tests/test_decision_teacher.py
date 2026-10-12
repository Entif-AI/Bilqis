import hashlib
import json
import unittest

from bilqis_alpha.kev_teacher import KevTeacher, validate_response


IDENTITY = {
    "models": [{
        "name": "kev-latest",
        "run": "jaredpalmer/kev-4b@6cfce5c2fa4b4bd64026336ab649c5ca78857d52",
        "backend": "mlx",
        "lora": 16,
        "device": "mps",
        "dtype": "bfloat16",
        "prefix_cache": {"hits": 0},
    }]
}


class FakeResponse:
    def __init__(self, value):
        self.value = value

    def read(self, limit):
        return json.dumps(self.value, separators=(",", ":")).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeOpener:
    def __init__(self, answer=None, models=None):
        self.answer = answer or {
            "answers": {"decision": {"type": "choice", "choice": "b", "confidence": 0.7,
                                       "probabilities": {"a": 0.3, "b": 0.7}}},
            "usage": {"total_tokens": 12},
        }
        self.models = list(models or [IDENTITY])
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        if request.full_url.endswith("/v1/models"):
            return FakeResponse(self.models.pop(0))
        return FakeResponse(self.answer)


class KevTeacherTests(unittest.TestCase):
    def teacher(self, answer=None):
        self.opener = FakeOpener(answer, models=[IDENTITY, IDENTITY, IDENTITY])
        return KevTeacher(opener=self.opener)

    def test_score_preserves_offered_order_and_retains_full_trace(self):
        teacher = self.teacher()
        result = teacher.score("state", "Choose", [
            {"candidate_id": "b", "description": "Second"},
            {"candidate_id": "a", "description": "First"},
        ], binding={"epoch": "02"})
        request = self.opener.requests[2][0]
        serialized = request.data.decode()
        self.assertEqual(serialized, '{"model":"kev-latest","state":"state","questions":{"decision":{"type":"choice","instructions":"Choose","criteria":{"b":"Second","a":"First"}}}}')
        self.assertEqual(result["serialized_request"], serialized)
        self.assertEqual(result["request_sha256"], hashlib.sha256(request.data).hexdigest())
        self.assertEqual(result["offered_candidate_ids"], ["b", "a"])
        self.assertEqual(result["choice"], "b")
        self.assertEqual(result["status"], "OK")
        self.assertEqual([entry["phase"] for entry in result["runtime_verifications"]], ["before", "after"])
        self.assertEqual(result["choice_calls"], 1)
        self.assertEqual(result["binding"], {"epoch": "02"})
        self.assertEqual(result["usage"], {"total_tokens": 12})

    def test_low_margin_is_explicit(self):
        teacher = self.teacher({"answers": {"decision": {"type": "choice", "choice": "a", "confidence": 0.51,
                                                            "probabilities": {"a": 0.51, "b": 0.49}}}})
        result = teacher.score("state", "Choose", [{"candidate_id": "a", "description": "A"},
                                                       {"candidate_id": "b", "description": "B"}])
        self.assertEqual(result["status"], "LOW_MARGIN")
        self.assertAlmostEqual(result["margin"], 0.02)

    def test_invalid_and_tampered_responses_are_errors(self):
        offered = ["a", "b"]
        bad = [
            {"answers": {"decision": {"type": "choice", "choice": "a", "confidence": 1.0,
                                         "probabilities": {"a": 1.0}}}},
            {"answers": {"decision": {"type": "choice", "choice": "z", "confidence": 0.7,
                                         "probabilities": {"a": 0.3, "b": 0.7}}}},
            {"answers": {"decision": {"type": "choice", "choice": "a", "confidence": 0.4,
                                         "probabilities": {"a": 0.4, "b": 0.6}}}},
        ]
        for response in bad:
            with self.assertRaises(ValueError):
                validate_response(response, offered)
            result = self.teacher(response).score("s", "q", [{"candidate_id": "a", "description": "A"},
                                                                 {"candidate_id": "b", "description": "B"}])
            self.assertEqual(result["status"], "ERROR")
            self.assertIn("error", result)

    def test_missing_or_invalid_probabilities_are_rejected(self):
        for probabilities in ({"a": True, "b": 0.0}, {"a": 0.2, "b": 0.2}):
            response = {"answers": {"decision": {"type": "choice", "choice": "a", "confidence": 1.0,
                                                     "probabilities": probabilities}}}
            with self.assertRaises(ValueError):
                validate_response(response, ["a", "b"])

    def test_answer_shape_is_exact(self):
        response = {"answers": {"decision": {"type": "choice", "choice": "a", "confidence": 1.0,
                                                 "probabilities": {"a": 0.5, "b": 0.5}, "gold": "a"}}}
        with self.assertRaisesRegex(ValueError, "KEV_RESPONSE_FIELDS"):
            validate_response(response, ["a", "b"])

    def test_nonlocal_endpoint_is_refused_before_connection(self):
        with self.assertRaisesRegex(ValueError, "LOCAL_ENDPOINT_ONLY"):
            KevTeacher("https://example.com", opener=FakeOpener())

    def test_runtime_swap_before_or_after_choice_is_explicit_error(self):
        swapped = {"models": [{**IDENTITY["models"][0], "run": "jaredpalmer/kev-4b@tampered"}]}
        opener = FakeOpener(models=[IDENTITY, IDENTITY, swapped])
        teacher = KevTeacher(opener=opener)
        result = teacher.score("state", "Choose", [{"candidate_id": "a", "description": "A"},
                                                      {"candidate_id": "b", "description": "B"}])
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["choice_calls"], 1)
        self.assertEqual([entry["phase"] for entry in result["runtime_verifications"]], ["before", "after"])
        self.assertIn("error", result["runtime_verifications"][-1])
        self.assertIsNone(result["runtime"])
        self.assertIn("KEV_RUNTIME_IDENTITY", result["error"]["message"])

    def test_runtime_failure_before_choice_prevents_choice_call(self):
        swapped = {"models": [{**IDENTITY["models"][0], "dtype": "float32"}]}
        opener = FakeOpener(models=[IDENTITY, swapped])
        teacher = KevTeacher(opener=opener)
        result = teacher.score("state", "Choose", [{"candidate_id": "a", "description": "A"},
                                                      {"candidate_id": "b", "description": "B"}])
        self.assertEqual(result["status"], "ERROR")
        self.assertEqual(result["choice_calls"], 0)
        self.assertEqual([entry["phase"] for entry in result["runtime_verifications"]], ["before"])
        self.assertIn("error", result["runtime_verifications"][0])


if __name__ == "__main__":
    unittest.main()
