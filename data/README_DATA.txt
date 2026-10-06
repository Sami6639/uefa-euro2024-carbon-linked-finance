UEFA EURO 2024 climate-finance evidence dataset
Snapshot acquired: 6 October 2026 (UTC)

Purpose
This package preserves reviewed public evidence for a case study of carbon-linked
financial commitments. It is not an individual-level dataset, a causal evaluation,
an uncertainty distribution, or proof of verified emissions offsets.

Sources and preservation
source_catalog.json lists eight official sources: UEFA's English ESG report,
DEKRA's 30 September 2024 ex-post study hosted by the University of Bielefeld,
Öko-Institut's original ex-ante report, and five UEFA climate-fund webpages.
The original analysis archive preserves downloaded PDFs/HTML and extracted text.
This portable release omits raw/ to avoid assuming redistribution rights. source_manifest.csv
records SHA-256, byte count, retrieval date, cover/article dates and PDF metadata.
Rendered PDF evidence pages were inspected in the original archive and are omitted
from this portable release. Source URLs and original snapshot hashes remain recorded.
The English ESG PDF's metadata identifies a December 5, 2024 creation/modification;
the package does not claim that these exact bytes existed on an earlier release date.

Core boundaries
- UEFA 316,912 tCO2e = 67,955 operations + 248,957 ticket-holder travel.
- DEKRA 778,968 tCO2e includes fan zones and accommodation in a broader inventory.
- DEKRA's restricted Table 19 gives 463,970.80 tCO2e. It does not recreate UEFA's
  inventory. Scope, factor and calculation differences are not a sampling interval.
- Original fund basis: minimum 280,000 tCO2e at EUR 25 per emitted tonne, with an
  approximately EUR 7m fund. This is distinct from the ESG report's forecast rows
  78,000 operations and 330,000 travel, and Öko-Institut's approximately 490,000.

Version discipline
The earlier ESG report says 227 clubs, approximately/just over EUR 8m and roughly
67,000 tonnes of expected lifecycle savings. The July 2024 article says 190 clubs
and roughly 60,000 expected lifecycle tonnes. January/July 2025 report 225 clubs
and EUR 7.925m. Closure reports EUR 7,923,013 invested, separately from allocations
of EUR 5.825m to clubs and EUR 2.1m to associations. All versions are retained.
The source does not explain every discrepancy. No residual is assigned a cause.

Observation and estimation
All inventory emissions are estimates. Transport activities rely on survey-based
extrapolation. Administrative funding figures are reported by UEFA, not externally
audited by this package. The savings estimates concern project lifetimes, do not
specify annual paths, and are not realised avoided emissions. No project-by-project
capital costs, realised savings, lifetimes, discount rates or raw survey records
are invented. The EUR 25 rule applies to emissions produced, not tonnes avoided.

Transport extraction
transport_activity.csv transcribes DEKRA Tables 13–18, PDF pages 35–38. Source
values are in million passenger-km with two decimal places. Unit conversion adds
no underlying precision. Printed totals and shares are retained even when rounded
components differ. Two fan-zone walking/cycling rows display 0.00 in the source,
but footnotes explain missing data; activity_pkm therefore stays blank. DEKRA
provides three modal-shift differential factors on p35; a complete set of absolute
mode emission factors matched to these tables is not disclosed and remains blank.

Reproducibility
From the package root, run:
  python scripts/acquire_sources.py
  python scripts/build_verified_data.py
The acquisition script preserves existing archived bytes. Use --refresh only to
write new versions into a separate timestamped folder. Refreshed sources require
renewed verification before updating reviewed numeric transcriptions.
build_verified_data.py rebuilds tables from explicit, page-cited transcriptions,
hashes archived sources, extracts text and tests exact accounting identities.
The actual runtime is recorded in runtime_environment.json. Conda/micromamba were
not installed or used. A proposed Conda environment may reproduce the workflow,
but must not be described as an environment in which this run was executed.

Reading the files
data_dictionary.csv explains every dataset and shared field. No source versions
should be silently collapsed. In the appendix emissions hierarchy, category totals
and their components must not be added together. source_reconciliation.csv and
validation_report.json make the known non-matches visible.

Scope and rights
The archive is a local research provenance package. No raw PDF, webpage or data
has been uploaded publicly. Original publishers retain rights to their documents.
Citation should link to the official source URLs, with the documented PDF pages.
