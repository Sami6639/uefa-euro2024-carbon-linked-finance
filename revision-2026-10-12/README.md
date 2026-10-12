# UEFA climate-finance revision: replication and matched benchmark

This addendum accompanies *Climate Finance under Reporting Uncertainty: A Feasibility Framework Illustrated by UEFA EURO 2024*. It preserves the original numerical results and adds an independent implementation check and an operational matched-contract benchmark. These are hypothetical design calculations, not empirical estimates of UEFA obligations or recipient cash gaps.

## Reproduce

Use Python 3.12. From this folder:

    python -m venv .venv
    .venv/bin/pip install -r requirements-lock.txt
    .venv/bin/python run_all.py

The command verifies the frozen original manifest, copies the baseline to a writable working directory, regenerates the original results, runs the independent analysis and compares all 17 original scientific outputs. No network connection is used after dependency installation. The numerical code contains no workspace-absolute paths. The command was successfully tested after extracting the portable package into a different directory.

The baseline is read from the unchanged sibling folder `../revision-2026-10-07`. The source baseline is the [7 October revision at commit 9254a7e](https://github.com/Sami6639/uefa-euro2024-carbon-linked-finance/tree/9254a7eff67bf87310b7935be567832b9314f253/revision-2026-10-07). Its metadata retains the earlier working title. Its files and scientific outputs are unchanged.

## Results and audit scope

The original 540 uniform, 32 ceiling, 36 Gaussian and 20 constructive checks reproduce. New analyses separately comprise 154 uniform ramp comparisons and payment-node LP checks, 36 Gaussian quadrature comparisons, 14 domain checks and 18 advance-maximization LPs. An optimally tuned simple capped linear ramp matches the unrestricted frontier in this benchmark; no gain from greater schedule flexibility is claimed.

Start with `04_Independent_Replication_Log.txt`, `05_Table_Figure_Code_Map.xlsx`, and `analysis/new_analysis_summary.json`. The scenario and constraint-remedy note is `analysis/scenario_design_and_decision_map.txt`. Source code and full benchmark records are in `analysis/`. Historical execution records in `logs/` document the performed tests; rerunning adds new runtime logs. Manuscript cell comparisons are a frozen authoring audit, not required by the numerical command.

This is AI-assisted implementation and mathematical checking, not a signed independent human review. The `sources/` folder contains 36 reviewed institutional claims, source URLs and locators, source-document hashes and the bounded public cash-flow search. Original full texts are excluded. The `literature/` folder contains the contribution comparison. The `math/` folder provides a separate mathematical implementation and results. To rerun that additional audit, execute `.venv/bin/python math/independent_math_audit_v1.py` from this folder; it is separate from the counts reported above.

The `publication_manifest_sha256.csv` records exact release bytes (excluding the manifest itself). Check these before rerunning, since regenerated results and runtime logs can change file hashes.

## Rights and version

Sami Küçükoğlu’s original software is provided under the MIT License in `LICENSE`, within the software-only scope set out in `THIRD_PARTY_DATA.md`. Third-party sources, manuscript prose and unrelated or jointly owned data are excluded. No third-party source documents are bundled. Cite the exact Git commit of the published snapshot to freeze this version; a version-folder name alone is not a release tag or archival DOI. No GitHub release tag or archival DOI is claimed.
