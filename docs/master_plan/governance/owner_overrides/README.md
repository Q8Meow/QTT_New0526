# QTT Owner Override Receipts

This directory is the static placeholder for future deterministic owner override receipts.

PR #59 only creates the schema, fixture, policy, validator, and report foundation. It does not create real runtime receipts, live receipts, order receipts, cash receipts, source acceptance artifacts, connector binding artifacts, SHA authority, AtomicRows bundle files, or profit evidence.

Future owner dashboard or QTT agent request flows must write validator-visible owner override receipts that conform to `schemas/governance/qtt_owner_override_receipt.schema.json`. QTT agents, Codex, ChatGPT, validators, gates, and generated reports may request or record owner decisions, but they may not approve for the owner.
