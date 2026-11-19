# Towards Evidence-Anchored Discoverability Assurance for Agent-Ready Knowledge Repositories

*A Methodological Perspective and Research Agenda*

Mariano Garralda-Barrio · Independent Researcher

[SSRN preprint](https://ssrn.com/abstract=7709359) · [BibTeX](citation.bib) · [Partial reference implementation](reference-implementation/)

## Contribution

A repository can contain sufficient evidence for a query while its hierarchy gives an agent too little guidance to find it. This paper proposes a method for checking whether a repository version preserves routes to sufficient source evidence under a declared navigation policy and resource budget.

- **Build.** Recursive Semantic Index Composition (RSIC) builds a hierarchy bottom-up, carrying evidence-linked cues into higher-level entries. RSIC serves as the reference builder. Existing indexes can also enter assurance if they expose compatible navigation, inspectable cues, and versioned evidence links.
- **Audit.** Navigate top-down against independently annotated evidence requirements. Record complete discovery separately from artifact conformance, navigation efficiency, and lifecycle cost.
- **Diagnose and repair.** Distinguish repository defects from failures attributable to the navigation policy or budget. Apply bounded, evidence-supported repairs to attributable repository defects.
- **Qualify.** Check invariants and replay regression queries before qualifying a repository version for the stated policy, query set, and budget.

The TLS 1.3 worked example shows how a specific deployment constraint can disappear from upper-level summaries even when it remains in the source. Preserving a discriminative cue helps the agent select the branch that leads to the evidence.

## Artifacts and status

This manuscript presents a methodology and a proposed evaluation protocol. The protocol tests the contribution of recursive composition and bounded repair, and treats transfer to indexes built by other methods as an empirical question.

- [Partial reference implementation and reproducible TLS 1.3 example](reference-implementation/)

## Citation

> Garralda-Barrio, Mariano (2026). *Towards Evidence-Anchored Discoverability Assurance for Agent-Ready Knowledge Repositories: A Methodological Perspective and Research Agenda*. SSRN preprint, November 15, 2026. [Available at SSRN](http://dx.doi.org/10.2139/ssrn.7709359).

Machine-readable citation metadata is available in [citation.bib](citation.bib).

## Related Research

- [Knowledge-Centric Information Systems](../knowledge-centric-information-systems/) introduces the broader architecture for operational knowledge.
- [Institutional Capability Lineages](../institutional-capability-lineages/) addresses evidence-governed evolution of institutional capabilities.
- [RAG Field Guide](../../field-guides/rag/) covers retrieval design and evaluation in RAG systems.
