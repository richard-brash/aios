from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


def specification(name: str) -> str:
    return (ROOT / "docs" / "specifications" / name).read_text(encoding="utf-8")


class RoleArchitectureAlignmentTests(unittest.TestCase):
    def test_role_creation_has_one_draft_initial_transition(self) -> None:
        lifecycles = specification("LIFECYCLES.md")
        self.assertIn("`[nonexistent] -> draft` is the sole legal initial transition", lifecycles)
        self.assertIn("MUST NOT transition directly to `active`", lifecycles)

    def test_founding_role_remains_a_distinct_genesis_case(self) -> None:
        lifecycles = specification("LIFECYCLES.md")
        self.assertIn("distinct reserved genesis establishment", lifecycles)
        self.assertIn("MUST NOT be recreated after genesis", lifecycles)

    def test_role_events_use_the_authoritative_organization_stream(self) -> None:
        event_model = specification("EVENT_MODEL.md")
        self.assertIn("including Role lifecycle Events", event_model)
        self.assertIn("one authoritative Organization stream", event_model)
        self.assertIn("per-Role Event stream MUST NOT", event_model)

    def test_organization_order_spans_contained_entities(self) -> None:
        protocol = specification("KERNEL_PROTOCOL.md")
        self.assertIn("consecutive Organization positions alongside Events for other contained entities", protocol)

    def test_entity_projections_are_derived_from_organization_history(self) -> None:
        protocol = specification("KERNEL_PROTOCOL.md")
        self.assertIn("MUST be reproducible from the authoritative Organization stream", protocol)
        self.assertIn("MUST NOT expose or imply a separate authoritative per-entity Event history", protocol)

    def test_entity_preconditions_do_not_replace_stream_concurrency(self) -> None:
        contract = specification("KERNEL_CONTRACT.md")
        self.assertIn("do not replace Organization-stream concurrency", contract)
        self.assertIn("no independent entity stream may override it", contract)

    def test_organization_is_the_only_domain_tenancy_boundary(self) -> None:
        entity_model = specification("ENTITY_MODEL.md")
        self.assertIn("Organization is the AIOS tenancy, isolation, governance, and Event-ordering boundary", entity_model)
        self.assertIn("no separate Tenant entity or `tenant_id`", entity_model)

    def test_conformance_catalog_contains_all_alignment_scenarios(self) -> None:
        conformance = specification("KERNEL_CONFORMANCE.md")
        for scenario_id in ("CMD-015", "LIF-013", "LIF-014", "LIF-015", "EVT-011", "EVT-012", "EVT-013", "EVT-014"):
            self.assertIn(f"| {scenario_id} |", conformance)
        self.assertIn("260 mandatory scenarios", conformance)


if __name__ == "__main__":
    unittest.main()
