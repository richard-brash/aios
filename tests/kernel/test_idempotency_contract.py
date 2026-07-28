"""Focused semantic identity and atomic runtime idempotency tests."""
from __future__ import annotations

import dataclasses
import unittest

from aios_kernel.runtime import semantic_runtime_command_fingerprint
from aios_protocol.identifiers import IntegrityReference, MessageId

from test_create_task_admission import command, engine


class RuntimeIdempotencyTests(unittest.TestCase):
    def test_equivalent_create_task_commands_have_equal_fingerprints(self):
        self.assertEqual(semantic_runtime_command_fingerprint(command()),
                         semantic_runtime_command_fingerprint(command()))

    def test_delivery_message_identity_is_nonsemantic(self):
        original=command()
        delivery=dataclasses.replace(
            original,submission=dataclasses.replace(
                original.submission,envelope=dataclasses.replace(
                    original.submission.envelope,message_id=MessageId("message-redelivery"))))
        self.assertEqual(semantic_runtime_command_fingerprint(original),
                         semantic_runtime_command_fingerprint(delivery))

    def test_create_task_fields_are_semantic(self):
        original=command()
        changed=(
            dataclasses.replace(original,title="changed"),
            dataclasses.replace(original,purpose="changed"),
            dataclasses.replace(original,proposed_task_id="task-2"),
            dataclasses.replace(original,initial_state=original.initial_state.ACTIVE),
            dataclasses.replace(original,submission=dataclasses.replace(
                original.submission,invocation_proof_reference=IntegrityReference("proof-changed"))),
        )
        fingerprint=semantic_runtime_command_fingerprint(original)
        self.assertTrue(all(semantic_runtime_command_fingerprint(item)!=fingerprint for item in changed))

    def test_exact_redelivery_is_atomic_and_allocates_nothing(self):
        runtime,store,ids,evaluator,_,_,cmd=engine()
        original=runtime.execute(cmd)
        before=(store.append_calls,store.builder_calls,len(ids.calls),evaluator.calls)
        duplicate=runtime.execute(cmd)
        self.assertIs(duplicate,original)
        self.assertEqual((store.append_calls,store.builder_calls,len(ids.calls),evaluator.calls),before)

    def test_conflicting_reuse_does_not_mutate_history(self):
        runtime,store,_,_,_,_,cmd=engine(); runtime.execute(cmd)
        history=store.read(cmd.submission.envelope.organization_id)
        changed=dataclasses.replace(cmd,title="competing")
        contender,*_=engine(cmd=changed,store=store)
        result=contender.execute(changed)
        self.assertEqual(result.reason_code.value,"IDEMPOTENCY.CONFLICT")
        self.assertEqual(store.read(cmd.submission.envelope.organization_id),history)


if __name__ == "__main__":
    unittest.main()
