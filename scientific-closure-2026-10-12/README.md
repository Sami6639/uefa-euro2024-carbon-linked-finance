# Scientific closure records — 12 October 2026

This additive record binds the final manuscript and supplementary information to the previously published calculations at commit `05d5f580bfe9a1b216fe900983c414abede0d484`. It does not change the mathematical code, results, data, or prior revision package.

## Contents

- `institutional_claim_register.json` / `.csv`: 36 primary-documentary claim records, source links, locators, accounting distinctions and explicit unknowns.
- `citation_claim_audit.json` / `.csv`: 33 matched references and source-specific claim-support/access limits.
- `citation_match_summary.json`: two-way citation matching and removal of the unnecessary Wang et al. (2024) dependency.
- `formal_consistency_register.json` / `.csv`: equation, hypothesis, boundary, unit and manuscript–supplement consistency results.
- `artifact_consistency_results.json`: 51 passing artifact checks and 121 passing source-bound table-cell checks. Prior numerical execution is reused, not represented as a fresh rerun.
- `document_identity.json`: SHA-256 identities and descriptive counts for the final, separately held documents: 21 manuscript pages, 6 supplement pages, 150 abstract words, 7,926 inclusive manuscript words excluding References, and 33 matched references.
- `evidence_closure_summary.json`: scope and remaining evidence limits.
- `manifest_sha256.csv`: SHA-256 checksums of these public records and the updated root README. The manifest excludes itself.

## Interpretation and limits

The contribution is an explicit analytical specialisation with bounded comparisons. Exhaustive theorem-by-theorem novelty exclusion is unverified and unclaimed. In particular, final full-text theorem-level comparisons for Cheung and Jewitt remain limited. Source-level support must be read with each record's stated access level; this is not universal full-text certification.

The records are AI-assisted analytical and artifact checks, not external human review, journal acceptance, a quality score or a guarantee. A complete dated institutional cash-flow case remains unavailable. The institutional overhead-cost denominator conflict is preserved explicitly rather than silently reconciled. Numerical diagnostics support consistency but do not replace analytical proof.

No manuscript or supplement full text, DOCX/PDF files, third-party full texts, private correspondence or personal records are included. Document names in JSON identify separately held artifacts and are not download links. All older repository files remain preserved, except for the additive pointer in the root README. This snapshot is identified by its immutable Git commit; no formal GitHub release, tag or DOI is asserted.

The existing [revision package](../revision-2026-10-12/README.md) remains the reproduction entry point. Paths in artifact checks are repository-root-relative unless they identify a separately held document or an internal DOCX component. Existing licensing and third-party-data restrictions continue to apply; this record grants no rights to the excluded full texts.
