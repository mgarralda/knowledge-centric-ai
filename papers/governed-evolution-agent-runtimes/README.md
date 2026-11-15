# Governed Evolution of Agent Runtimes through Executable Operational Cognition

**Author**

Mariano Garralda-Barrio

[Paper (PDF)](paper.pdf) · [arXiv preprint](https://arxiv.org/abs/2605.27328) · [Reference implementation](https://github.com/mgarralda/governed-runtime) · [BibTeX](citation.bib)

---

## Contribution

This paper introduces a governance-oriented framework for the controlled evolution of agent runtimes through **Executable Operational Cognition**.

Rather than treating agent-generated artifacts as transient outputs, it formalizes their evolution into persistent runtime capabilities governed through explicit validation, lifecycle management, mutation, provenance, observability and rollback mechanisms. The paper proposes **HarnessMutation** as a governed adaptation mechanism and introduces a runtime model in which operational capabilities evolve under explicit governance constraints instead of unrestricted self-modification.

---

## Reference Implementation

[**governed-runtime**](https://github.com/mgarralda/governed-runtime) is the executable research companion to this paper. It implements a governance-aware runtime kernel on top of LangGraph and DeepAgents. The kernel gives agent-generated artifacts a path to become persistent capabilities that later executions can reuse. Validation and lifecycle transitions govern how those capabilities enter the runtime, while harness changes follow a separate proposal and promotion path.

| Concept in the paper | Where to inspect it in the implementation |
| --- | --- |
| Capability validation and lifecycle | `validate_generated_skill` checks generated skills. `CapabilityReview` records reviews, and `promote_skill_stage` handles lifecycle transitions. |
| Governed harness adaptation | `propose_harness_mutation` and `promote_harness_mutation` expose separate stages for proposing and promoting a harness change. |
| Persistent operational memory and introspection | Generated skills, runtime memory notes, and `trace_events.jsonl` retain operational history. `inspect_harness_state` exposes runtime state for inspection. |
| Multi-agent governance | Specialized subagents divide capability generation, validation, mutation governance, and task execution. |

Start with the [paper-to-code mapping](https://github.com/mgarralda/governed-runtime#mapping-to-implementation), then follow the named components and the inline `Implements:` comments in [`governed_agent_runtime.py`](https://github.com/mgarralda/governed-runtime/blob/main/governed_agent_runtime.py).

The repository is a research prototype for examining the proposed design. It approximates the paper's Knowledge-Grounded Runtime Graph through registries, reviews, and runtime memory artifacts. Use is governed by its [Academic Research License](https://github.com/mgarralda/governed-runtime/blob/main/LICENSE).

---

## Keywords

- Agent Runtimes
- Executable Operational Cognition
- Runtime Governance
- Multi-Agent Systems
- HarnessMutation
- Capability Lifecycle
- Runtime Evolution
- Agentic AI
- Runtime Architecture
- Operational Memory

---

## Artifacts

- 📄 [Paper (PDF)](paper.pdf)
- 📚 [BibTeX Citation](citation.bib)
- [Reference implementation and source code](https://github.com/mgarralda/governed-runtime)

---

## Publication

- 🌐 arXiv (Preprint): https://arxiv.org/abs/2605.27328

---

## Related Resources

### Research Papers

- [Towards Evidence-Anchored Discoverability Assurance for Agent-Ready Knowledge Repositories](../evidence-anchored-discoverability/)

- 📄 [Knowledge-Centric Information Systems](../knowledge-centric-information-systems/)
- 📄 [From Task-Guided Conversational Graphs to Goal-Oriented Dialogue Runtimes](../goal-oriented-dialogue-runtimes/)

### Engineering Resources

- 📘 [RAG Field Guide](../../field-guides/rag-field-guide/)
- 📄 [Vol. 01 – From Uncertainty to Confidence](../../whitepapers/vol-01-from-uncertainty-to-confidence/)
