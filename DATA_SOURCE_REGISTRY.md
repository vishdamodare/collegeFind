# Data Source Registry
Checked 2026-11-10 by plain HTTP GET (no authentication, no candidate portals).

| Source | URL | Reachable | Content found | Status |
|---|---|---|---|---|
| FE 2025 portal (CET Cell) | https://fe2025.mahacet.org/ | 200 | Per-year folders `/2022/ /2023/ /2024/` with `YYYYENGG_CAP{1,2,3}_CutOff.pdf` (Maharashtra+minority), `YYYYENGG_CAP{n}_AI_CutOff.pdf` (All India), `YYYYSeatMatrix.pdf`; 2025 merit lists; CAP Round 1–4 allotment pages | Primary for 2022–2024 cutoffs |
| FE 2026 portal | https://fe2026.mahacet.org/ | 200 | `cappublicdocs2026.blob.core.windows.net/documents/2026ENGG_CAP{1-4}_{MH,AI}_CutOff*.pdf`, `2026_fe_seatmatrix_V1.pdf`; Diploma CAP4 list | Current year |
| CET Cell | https://cetcell.mahacet.org/ | 200 | not yet crawled | TODO |
| DMER Maharashtra | https://dmer.maharashtra.gov.in/ | 200 | not yet crawled | TODO Phase 6 |
| MCC | https://mcc.nic.in/ | 200 | not yet crawled | TODO Phase 6 |
| NIRF | https://www.nirfindia.org/ | **403** to automated GET | — | Manual download / permission needed; see KNOWN_LIMITATIONS |
| AISHE, UGC, AICTE, MahaFRA | — | not checked | — | TODO |

Terms of use / reuse licensing of these PDFs has **not** been reviewed yet; original PDFs are stored locally (`data/raw/`, git-ignored) and are not redistributed. Review before public launch.

## Datasets imported (2026-11-10)
| Dataset | URL pattern | Status |
|---|---|---|
| CAP cut-off lists, Maharashtra & Minority seats, R1–R3, 2022-23/2023-24/2024-25 | `http://fe2025.mahacet.org/{year}/{year}ENGG_CAP{1,2,3}_CutOff.pdf` | imported, `pending`; 2022 R1 title anomaly noted |
| Provisional seat matrices (CAP Round I) 2022/2023/2024 | `http://fe2025.mahacet.org/{year}/{year}SeatMatrix.pdf` (published 12 Oct 2022, 19 Jul 2023, 8 Aug 2024) | imported, `pending` |
| All-India lists `*_AI_CutOff.pdf`, Round 4, 2025–26, DMER/MCC, NIRF, fees, AICTE | — | not imported |
