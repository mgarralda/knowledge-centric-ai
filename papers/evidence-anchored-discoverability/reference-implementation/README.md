# Evidence-Anchored Discoverability Assurance

**Status:** Partial reference implementation with a deterministic worked
example. Companion to [Towards Evidence-Anchored Discoverability Assurance
for Agent-Ready Knowledge Repositories](../) ([SSRN preprint](https://ssrn.com/abstract=7709359), [BibTeX](../citation.bib)).

## Run the worked example

Requires Python 3.10 or later. The example uses the standard library. From
this directory, run:

```bash
python demo_tls.py
python -m unittest -v
```

The fixture adapts §4.4. Service A negotiates TLS 1.3 only with a feature flag
enabled, while Relay B supports TLS 1.2 only. Evidence unit `E-17` points to
the passage and `E-17-context` identifies the required flag definition. The
initial Operations entry omits the compatibility cue. The child link to
`transport_compatibility.md` is already present.

| Run | Expected result |
| --- | --- |
| Paper example | The gate query initially follows Security. A one-entry cue edit redirects it through Operations to the source. Qualification passes and the held-out paraphrase reaches both evidence units. |
| Regression control | An intentionally overbroad edit recovers the TLS evidence but removes a previously successful Security route. The regression gate rejects it, then accepts the minimal cue edit. |
| Budget control | The index already contains the cue. Two reads cannot reach the source. One more read restores discovery on the same index. The audit records budget insufficiency and leaves the index intact. |
| Mixed control | The cue is missing and the budget allows only two reads. Adding the cue alone and increasing the budget alone both fail. The combined replay reaches the evidence. The audit reports a mixed failure without editing the index. |

The diagnostic trace records the intervention, snapshot, policy, budget,
route and evidence reached. The repair-stage before/after traces remain
available alongside the gate and test traces. A replay with a larger
budget is diagnostic only. Qualification uses the original declared budget.

## Traceability and coverage

| Manuscript | Code | Scope |
| --- | --- | --- |
| §4.2–4.4, artifact contract and TLS example | [`contracts.py`](contracts.py), [`demo_tls.py`](demo_tls.py) | Versioned source locators, context links, evidence-backed cues and fixture-level reference checks. |
| §5.1, Algorithm 1 | [`rsic.py`](rsic.py), [construction notes](rsic.md) | Bottom-up traversal and typed child descriptors. The fixture supplies extraction and composition, including the seeded omission. |
| §5.2, Algorithm 2 | [`assurance.py`](assurance.py), [assurance notes](assurance.md) | Bounded candidate loop, artifact checks, regression gates and qualification. The fixture implements lexical navigation, cue-omission attribution, and a root-entry repair. General semantic diagnosis and repair are adapter responsibilities. |
| §2, Eqs. 1–2, and §7.4 | [`metrics.py`](metrics.py), [notation mapping](metrics.md) | Complete discovery, partial evidence coverage, unsupported returns and regression. Traces retain cost fields. The example measures deterministic node reads and uses zero for other dimensions. |
| §6, incremental maintenance | [`contracts.py`](contracts.py) | Typed dependency records. Incremental propagation remains proposed. |
| §7, experimental protocol | [`test_demo_tls.py`](test_demo_tls.py) | The tests verify the worked example and controls. Benchmark ablations, cross-builder transfer and hypothesis testing require a separate evaluation. |

RSIC is the reference constructor. Assurance accepts a
`RepositorySnapshot` through the shared artifact contract and can likewise
receive a compatible index from another builder. The fixture models index
entries in memory. Its conformance checks enforce immediate-child links,
root reachability of required evidence, context resolution, and exact
cue-to-source mappings for the fixed synthetic corpus.

## Evaluation boundary

The navigator sees question text and a budget. Scoring uses independently
specified sufficient evidence sets `G(q)`, supplied as fixture annotations.
Node counts are enforced by the fixture navigator. The orchestrator rejects
reported usage beyond any declared budget dimension.

Only repair queries (`Qr`) drive diagnosis and candidate edits. The gate
(`Qg`) opens after repair and the test set (`Qt`) opens after qualification.
IDs are unique and text cannot repeat across splits after case and whitespace
normalization. This checks exact duplicates. Semantic overlap and provenance
require benchmark curation. The fixture uses deterministic evidence matching.
Its navigator retrieves material for inspection, so an inspected passage
does not count toward unsupported returns on a negative query.
Exploratory LLM-as-a-judge assessment in §7 is outside this demonstrator.

## License

The Python code is available under the [MIT License](LICENSE).
