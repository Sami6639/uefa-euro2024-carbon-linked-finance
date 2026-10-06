# Reproducible climate-finance contract analysis

This analysis companion supports *Financing Credible Decarbonisation in Mega-Events: Carbon-Linked Commitments and Emissions Uncertainty at UEFA EURO2024*. It implements a conditional, applied analytical framework. It does not estimate UEFA behavioral responses, event-caused abatement, project additionality, causal effects, or empirical measurement-error distributions.

## Reproduce

From this directory:

```sh
conda env create -f environment.yml
conda activate euro-finance
python run_analysis.py
```

Alternatively, use a compatible Python environment with the pinned `requirements.txt`, then execute the same runner. The runner uses existing local source files and makes no network requests.

The supplied results were executed in the provided Python 3.12.14 runtime, with the exact versions recorded in `outputs/preflight.json`. A pinned Conda environment is defined but was not created or tested: Conda was absent in the execution environment. The standard-library `unittest` framework is used; pytest and Jupyter are not required. No stochastic computation occurs, so no random seed is applicable. Root finding, adaptive integration and linear programming are deterministic at the stated tolerance; bitwise identity across different numerical libraries/platforms is not promised. Figure files can differ in embedded creation metadata across runs, while the CSV numerical outputs are deterministic.

## Project map

- `data/raw/`: source snapshots in the original archive; omitted from this portable release. The source catalog and acquisition script identify how to retrieve sources.
- `data/headline_metrics.csv`, `data/timing_and_rules.csv`, `data/source_reconciliation.csv`: verified source-specific observations and distinctions. The model never overwrites them.
- `model/config.json`: locked scenario domain and quantitative reference scale.
- `model/contracts.py`: analytical contract calibration, fixed-schedule evaluation, independent quadrature, capped-slope LP, and the discrete counterexample.
- `model/generate_results.py`: machine-readable results, table data, validations and provenance checks.
- `model/render_figures.py`: four Matplotlib figures, reading generated CSVs only.
- `model/equations.tex`: canonical formula bank with units and domain restrictions.
- `tests/`: standard-library unit tests, including corner regimes and a deliberate moving-normalization diagnostic.
- `outputs/`: machine-readable scientific results, diagnostics and software/hash manifest.
- `figures/`: PNG (300 dpi), vector PDF and editable SVG versions of four analytical figures.

## Scientific contract

At the fixed reference emissions scale, a precommitted schedule maps a reported inventory to a sponsor's funding obligation. The benchmark expected payment is the announced final fund, rather than an assumed ex-ante forecast or legal payment obligation. The public EUR 25 per emitted tonne rate is imposed as a common normative slope cap across compared schedules, not described as an observed legal restriction. The report scale, announced budget, and rate are read from verified source rows and checked against the locked configuration.

Admissible schedules are absolutely continuous on a neighborhood of the supports reached by local physical-mean perturbations, nondecreasing, bounded below by a guaranteed floor, and have slope between zero and the common cap. A schedule is calibrated once at the reference mean and then held fixed when the physical mean changes. Its expected local derivative is a marginal contractual funding obligation. A behavioral interpretation additionally requires an enforceable, precommitted liability internalized by the actor choosing emissions.

For positive-width uniform reporting noise, the sharp lower expected-budget bound for floor F and marginal obligation m is F+d*m^2/p. A capped-slope upper-tail hinge attains the bound. The independent LP permits arbitrary admissible cellwise slopes rather than imposing the hinge. The linear-program output converges to the analytical bound and preserves finite-grid approximation error rather than replacing it with the exact value.

For an upfront financing gap H, the floor is assumed irrevocable, bankable, and released before verification. With positive-width uniform noise, a target q in [0,p] is achievable at expected cost at most B exactly when B >= H+d*q^2/p. This is a mean-budget frontier, not a minimum-variance or welfare theorem. Guarantee-loading and fixed-verification costs are a conditional algebraic extension only; they are not estimated.

### Zero-noise endpoint

When noise is zero and discretionary budget B-F is strictly positive, the selected schedule has local slope p. When F=B, the selected constant contract has slope zero. A hinge placed at the reference point is not two-sided differentiable, so it cannot be substituted silently. For a positive target at zero noise, the exact financing condition is H<B. The value B at the displayed floor frontier is an unattained supremum. Output flags explicitly distinguish attained and unattained boundaries.

### Distribution and accounting boundaries

All standard deviations, noise families, floor shares and liquidity gaps are assumptions or sensitivity scenarios. UEFA/DEKRA accounting totals are never pooled into a reporting-noise sample. The reference ex-post inventory is a dimensional scale, not an ex-ante expected inventory. Uniform support remains nonnegative over the declared event-scale grid. Gaussian sensitivity permits signed reporting error and a negative-report tail; it is not claimed to be a literal nonnegative emissions-inventory process. Gaussian and uniform scenarios have the same variance at the same configured standard deviation.

Within-family scale increases weakly reduce the uniform marginal obligation and reduce the Gaussian obligation for a fixed positive discretionary budget. This is not distribution-free: the explicitly constructed independent-noise counterexample preserves expected payment while increasing the local marginal slope. Its normalized report values and budget are not observations.

The announced budget differs from the reported rate times the reported inventory; the exact later investment amount also differs. `budget_reconciliation.json` preserves these amounts without inventing a fee, rounding rule, or emissions revision. The equal-budget affine comparator is mathematically centered at the benchmark; its intercept is not an observed administration charge. A separate arithmetic-budget robustness file repeats the uniform scenarios consistently at the product of the reported rate and inventory.

## Outputs for manuscript use

- `contracts_grid.csv`: complete main uniform/Gaussian scenario grid.
- `selected_manuscript_scenarios.csv`: exact selected rows for narrative lookup.
- `liquidity_frontier_grid.csv`: financing requirements and feasibility flags.
- `tables/table1_source_ledger.csv`: institutional values with dates, source URLs and analytical roles.
- `tables/table2_boundary_regimes.csv`: normalized corner checks.
- `tables/table3_uniform_financing_thresholds.csv`: floor limits at selected marginal targets.
- `tables/table4_validation_summary.csv`: independent numerical diagnostics.
- `figure_captions.json` and `table_captions.json`: short caption/assumption banks.
- `independent_quadrature_validation.csv`, `lp_frontier_validation.csv`, `counterexample_*.csv`, `budget_rounding_robustness.csv`, and `normalization_diagnostic.json`: all numerical robustness results.
- `validation_summary.json`, `test_report.json`, and `manifest.json`: execution evidence and exact file hashes.

Every scientific numerical statement should consume these machine-readable files or the original verified source ledgers. No manuscript figure should be modified independently of the rendering script and its source CSV.

## Validation and restrictions

The runner stops on failed unit tests or numerical acceptance checks. It compares analytical moments against direct payment quadrature, fixed-schedule derivatives against finite differences, and the sharp bound against independent finite-dimensional LPs. Boundary tests retain zero noise, zero floor, floor equal to budget, zero cap, large-noise clipping, full-slope boundary, and the constructed reversal. False moving normalization is intentionally recorded to demonstrate that recalibrating the schedule at every physical mean eliminates the very derivative being evaluated.

This package supplies analysis code, derived evidence ledgers, results and figures for reproducibility. Source redistribution rights are not presumed. The model runner does not publish or upload files. See THIRD_PARTY_DATA.md before distributing source material.

## Acquisition and extraction environment

The minimal analysis environment above regenerates model results from the included processed source files. Rebuilding source extractions additionally requires pypdf 6.10.0, lxml 6.1.1 and PyMuPDF 1.26.6 (including the acquisition manifest's package audit), plus the external Poppler `pdftotext` executable, observed version 25.03.0. These are defined in `environment-acquisition.yml` and `acquisition_requirements.txt`. Poppler is not installed by pip. For the fully declared acquisition environment:

```sh
conda env create -f environment-acquisition.yml
conda activate euro-finance-acquisition
python scripts/acquire_sources.py
python scripts/build_verified_data.py
python run_analysis.py
```

Acquisition preserves existing archived bytes. Its optional refresh mode stores newly retrieved content separately; it must not silently replace the reviewed analytical snapshot. Source availability and redistribution rights remain external constraints. The supplied extraction used the already available managed-runtime packages and Poppler; this second Conda definition is also untested and is not an OS-level lockfile. The model runner does not automatically repeat acquisition.

### Numerical display caveat

For finite positive discretionary budget and positive Gaussian noise, the exact marginal obligation is strictly below the cap. Some near-cap normal probabilities round to one at float64 precision (the dynamically counted cases are in `validation_summary.json`). Apparent Gaussian plateaus in charts are numerical near-cap values, not exact full-rate feasibility. The uniform positive-width frontier can achieve the cap exactly. All plotted noise-scale ratios refer to standard deviation divided by the reference scale; uniform half-width is the standard deviation multiplied by the square root of three.

The equal-floor endpoint added to the floor-share grid is a diagnostic corner test. It is recorded separately from the prespecified interior sensitivity values and retains the selected constant-payment convention.


The manuscript notation uses e* for the physical reference level, d for uniform half-width, H for the euro financing gap, and q for the target marginal obligation. CSV columns use descriptive names. Function argument names `mean`, `halfwidth`, `gap` and `target` correspond to these symbols.


## Text-format portability

Release text files use canonical LF line endings. CSV writers specify LF explicitly, and package hashes are calculated after text normalization. This keeps scientific values and published hash ledgers consistent with Git text normalization. Original source snapshot hashes refer to unmodified downloaded bytes; derived CSV line endings are a separate representation choice.


## Portable release contents

This release contains derived evidence ledgers, the analysis code and tests, generated results and figures, and verified citation metadata. It intentionally omits full-text PDFs/HTML, evidence screenshots, archival literature-preparation scripts and review-working files. Acquisition can retrieve sources, but remote bytes may change; original source hashes are retained in source_manifest.csv. The numerical analysis runs from the included processed files without downloads. Citation registries contain only the final manuscript bibliography, supplied as verified metadata rather than a rerunnable literature-search pipeline. Public availability of a source is not represented as a redistribution licence.
