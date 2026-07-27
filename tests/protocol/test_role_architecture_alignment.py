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
        self.assertIn("MUST NOT be recreated or reactivated after genesis", lifecycles)

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
        self.assertIn("277 mandatory scenarios", conformance)

    def test_activate_role_transition_is_explicit_and_only_from_draft(self) -> None:
        lifecycles = specification("LIFECYCLES.md")
        self.assertIn("Draft --> Active: RoleActivated", lifecycles)
        self.assertIn("`draft -> active` is an **Authorized** transition", lifecycles)
        self.assertIn("already-active Role is rejected with `LIFECYCLE.INVALID_TRANSITION`", lifecycles)

    def test_activate_role_command_contract_is_complete(self) -> None:
        protocol = specification("KERNEL_PROTOCOL.md")
        for contract in (
            "`operation_type=ActivateRole`", "`operation_version=1.0`",
            "`payload_type=ActivateRolePayload`", "`role_id`",
            "`expected_entity_revision`", "`current_state=draft`",
            "`requested_state=active`", "`role.activate`",
        ):
            self.assertIn(contract, protocol)

    def test_role_activated_event_and_revision_contract_are_explicit(self) -> None:
        event_model = specification("EVENT_MODEL.md")
        protocol = specification("KERNEL_PROTOCOL.md")
        self.assertIn("`RoleActivated`", event_model)
        self.assertIn("revision `n + 1`", event_model)
        self.assertIn("`prior_lifecycle_state=draft`", protocol)
        self.assertIn("`lifecycle_state=active`", protocol)
        self.assertIn("resulting revision equals the positive prior revision plus exactly one", protocol)

    def test_activation_uses_organization_concurrency_and_existing_idempotency(self) -> None:
        protocol = specification("KERNEL_PROTOCOL.md")
        self.assertIn("expected Organization stream position remains the authoritative append precondition", protocol)
        self.assertIn("returns the original disposition, identifiers, positions, and evaluation time", protocol)
        self.assertIn("A new Command for an already-active Role is not exact redelivery", protocol)

    def test_activation_replay_is_effect_free_and_rejects_corruption(self) -> None:
        protocol = specification("KERNEL_PROTOCOL.md")
        self.assertIn("When folding a valid `RoleActivated` sequence, replay MUST locate the Role", protocol)
        self.assertIn("`CommandAccepted(ActivateRole v1) -> RoleActivated -> AuditLinked`", protocol)
        self.assertIn("neither domain Event is self-authorizing", protocol)
        self.assertIn("immutable authenticated-admission evidence snapshot", protocol)
        self.assertIn("complete canonical Organization history, not a filtered Role-only history", protocol)
        self.assertIn("accepted CreateTask transactions", protocol)
        self.assertIn("attributable rejection transactions", protocol)
        self.assertIn("without returning a partially advanced authoritative projection", protocol)
        self.assertIn("Replay performs no governance, Command handling, allocation, clock access, append, persistence mutation, or external effect", protocol)

    def test_activation_conformance_scenarios_are_complete(self) -> None:
        conformance = specification("KERNEL_CONFORMANCE.md")
        for number in range(16,33):
            self.assertIn(f"| LIF-{number:03d} |", conformance)
        self.assertIn("277 mandatory scenarios", conformance)


if __name__ == "__main__":
    unittest.main()
