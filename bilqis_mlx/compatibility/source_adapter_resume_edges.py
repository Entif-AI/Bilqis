"""Enumerable one-way provider edges accepted for historical BAMF resume."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceProviderResumeEdge:
    edge_id: str
    adapter_id: str
    admitted_implementation_sha256: str
    current_implementation_sha256: str
    rule: str


SUPPORTED_SOURCE_PROVIDER_RESUME_EDGES = (
    SourceProviderResumeEdge(
        "grade-a-1324082-to-current", "source.micro.predicates/v1",
        "f8e5aec9398538adc633deabe9c41c485e69a96044b9b86a5f1075ce6e201778",
        "7f05ec04d200d7394f32ed1811a3d9a47ce4cdb9267692bf558453e81e9fb04a",
        "grade-a-1324082"),
    SourceProviderResumeEdge(
        "grade-a-accepted-to-current", "source.micro.predicates/v1",
        "c451c3e6bf5ab538450c691d504230036b9a729ddfc67b53163c6a1f106d62a9",
        "7f05ec04d200d7394f32ed1811a3d9a47ce4cdb9267692bf558453e81e9fb04a",
        "cohort-bound"),
    SourceProviderResumeEdge(
        "boolean-identification-accepted-to-current",
        "source.micro.boolean-identification/v1",
        "6399dae052a289d46063df0e897e14f1392e2f1b99e90c2ae791fda9a8246743",
        "811ed2ad7708e6a7ce3a72fb20d92ea8fcc1df51aae45afc01e711fea07d18c6",
        "cohort-bound"),
    SourceProviderResumeEdge(
        "boolean-identification-pre-r15-to-current",
        "source.micro.boolean-identification/v1",
        "1404c511d7b5eab19025726d5c4c98073250cc0c75cf37b185344da92060edee",
        "811ed2ad7708e6a7ce3a72fb20d92ea8fcc1df51aae45afc01e711fea07d18c6",
        "cohort-bound"),
    SourceProviderResumeEdge(
        "numeric-accepted-to-current", "source.finite-numeric/v2",
        "2758cf678e9d2a45f3f5a1b5edd85d5ae513e54506c0d98853b9402b91572754",
        "621257de25895cc5cfcf0b9730c43fbe04260a3aa68732cfcc41a43988cd8141",
        "numeric-modular"),
    SourceProviderResumeEdge(
        "numeric-modular-to-current", "source.finite-numeric/v2",
        "a52f346478852775053f07a79342e5a9e9266bc64a2df6fe953d6a64881c8b7d",
        "621257de25895cc5cfcf0b9730c43fbe04260a3aa68732cfcc41a43988cd8141",
        "numeric-modular"),
    SourceProviderResumeEdge(
        "numeric-current-adr106-cohort-repair", "source.finite-numeric/v2",
        "621257de25895cc5cfcf0b9730c43fbe04260a3aa68732cfcc41a43988cd8141",
        "621257de25895cc5cfcf0b9730c43fbe04260a3aa68732cfcc41a43988cd8141",
        "numeric-adr106"),
)
