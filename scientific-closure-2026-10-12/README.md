# Scientific closure records — 12 October 2026

This record binds the final manuscript and supplementary information to the previously published calculations at commit `05d5f580bfe9a1b216fe900983c414abede0d484`. It does not change the mathematical code, results, data, or prior revision package.

## Contents

- `institutional_claim_register.json` / `.csv`: 36 primary-documentary claim records, source links, locators, accounting distinctions and explicit unknowns.
- `citation_claim_audit.json` / `.csv`: 33 matched references and source-specific claim-support/access limits.
- `citation_match_summary.json`: two-way citation matching and removal of the unnecessary Wang et al. (2024) dependency.
- `formal_consistency_register.json` / `.csv`: equation, hypothesis, boundary, unit and manuscript–supplement consistency results.
- `artifact_consistency_results.json`: 51 passing historical artifact checks and 121 passing source-bound table-cell checks, explicitly bound to the earlier document identities. Prior numerical execution is reused, not represented as a fresh rerun.
- `document_identity.json`: SHA-256 identities and descriptive counts for the final, separately held documents: 21 manuscript pages, 6 supplement pages, 150 abstract words, 7,935 inclusive manuscript words excluding References, and 33 matched references.
- `evidence_closure_summary.json`: scope and remaining evidence limits.
- `manifest_sha256.csv`: SHA-256 checksums of these public records and the updated root README. The manifest excludes itself.

## Final document update

The final Lo (2017) publisher theorem comparison has been incorporated into the separately held Word documents. The citation record distinguishes a single inequality that may be slack or binding from externally required exact spending, and retains the independent payment-span condition. Numerical calculations, scenarios, tables and figures are unchanged.

`document_revalidation.json` binds the new document identities to 29 passing delta checks and the unchanged 30-entry formal register. The manuscript retains 178 native math objects; the supplement retains its 10 prior objects and adds 8 semantically equivalent native inline objects. The other 32 citation evidence records and all 36 institutional records are reused rather than presented as newly retrieved evidence. The earlier exact document snapshot remains available at commit `8e65649cf9870075a51fe3271111e5acf503bb96`.

## Interpretation and limits

The contribution is an explicit analytical specialisation with bounded comparisons. Exhaustive theorem-by-theorem novelty exclusion is unverified and unclaimed. In particular, final full-text theorem-level comparisons for Cheung and Jewitt remain limited. Source-level support must be read with each record's stated access level; this is not universal full-text certification.

The records are AI-assisted analytical and artifact checks, not external human review, journal acceptance, a quality score or a guarantee. A complete dated institutional cash-flow case remains unavailable. The institutional overhead-cost denominator conflict is preserved explicitly rather than silently reconciled. Numerical diagnostics support consistency but do not replace analytical proof.

No manuscript or supplement full text, DOCX/PDF files, third-party full texts, private correspondence or personal records are included. Document names in JSON identify separately held artifacts and are not download links. Computational code, data, scientific outputs and the earlier revision package remain preserved; this update changes only closure records and README pointers. This snapshot is identified by its immutable Git commit; no formal GitHub release, tag or DOI is asserted.

The existing [revision package](../revision-2026-10-12/README.md) remains the reproduction entry point. Paths in artifact checks are repository-root-relative unless they identify a separately held document or an internal DOCX component. Existing licensing and third-party-data restrictions continue to apply; this record grants no rights to the excluded full texts.
