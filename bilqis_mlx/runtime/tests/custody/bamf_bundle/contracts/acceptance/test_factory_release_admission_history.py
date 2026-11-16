from bilqis_mlx.runtime.tests.custody.bamf_bundle.contracts.acceptance.factory_release_admission_binding_support import *

class FactoryReleaseAdmissionHistoryTests(FactoryReleaseAdmissionBindingSupport):
    def test_historical_parsed_binding_validates_exact_child(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()

        validate_parsed_factory_release_admission_binding(
            student,
            parsed,
            parsed.digest,
        )
        with self.assertRaises(BilqisError) as failure:
            validate_parsed_factory_release_admission_binding(
                student,
                parsed,
                "0" * 64,
            )
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_historical_validation_rejects_transition_tamper(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()
        proposal_sha256 = (
            "e" * 64
            if self.transition.proposal_sha256 != "e" * 64
            else "d" * 64
        )
        tampered = replace(
            student,
            transition={
                **dict(student.transition),
                "proposal_sha256": proposal_sha256,
            },
        )

        with self.assertRaises(BilqisError) as failure:
            validate_parsed_factory_release_admission_binding(
                tampered,
                parsed,
                parsed.digest,
            )
        self.assertEqual(
            failure.exception.context["reason"],
            "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
        )

    def test_historical_validation_rejects_binding_only_digest_tamper(self):
        student = self._historical_student(self.candidate)
        alternate_transition = (
            "0" * 64 if self.binding.transition_sha256 != "0" * 64 else "1" * 64
        )
        alternate_event = (
            "0" * 64 if self.binding.adoption_event_sha256 != "0" * 64 else "1" * 64
        )

        for label, parsed in (
            ("transition", self._parsed_with(transition_sha256=alternate_transition)),
            ("event", self._parsed_with(adoption_event_sha256=alternate_event)),
        ):
            with self.subTest(label=label), self.assertRaises(BilqisError) as failure:
                validate_parsed_factory_release_admission_binding(
                    student,
                    parsed,
                    parsed.digest,
                )
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
            )

    def test_historical_validation_rejects_event_and_event_id_tamper(self):
        student = self._historical_student(self.candidate)
        parsed = self._parsed()
        original = student.outbox[0]
        proposal_sha256 = (
            "e" * 64
            if original["proposal_sha256"] != "e" * 64
            else "d" * 64
        )
        tampered_event = {
            **original,
            "proposal_sha256": proposal_sha256,
        }
        alternate_event_id = (
            "0" * 64 if original["event_id"] != "0" * 64 else "1" * 64
        )
        tampered_event_id = {
            **original,
            "event_id": alternate_event_id,
        }

        for label, event in (
            ("provenance", tampered_event),
            ("event_id", tampered_event_id),
        ):
            with self.subTest(label=label), self.assertRaises(BilqisError) as failure:
                validate_parsed_factory_release_admission_binding(
                    replace(student, outbox=(event,)),
                    parsed,
                    parsed.digest,
                )
            self.assertEqual(
                failure.exception.context["reason"],
                "BAMF_FACTORY_RELEASE_ADMISSION_BINDING_DRIFT",
            )
