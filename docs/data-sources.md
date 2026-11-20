# Data sources – what can be automated

| Dataset | Format | Automatable? | Notes |
|---|---|---|---|
| CET Cell CAP cut-off lists, MH/minority seats, 2022–2024 (R1–R3) and 2026 (R1–R4) | text-layer PDF | **Yes** – `data-engine/parsers/cet_cutoff.py` | Round I 2024 parsed: 31,690 cells, 0 structural errors |
| CET Cell All-India (`*_AI_CutOff.pdf`) | PDF | Likely, **needs its own parser** | Not yet inspected; do not reuse the MH parser blindly |
| Seat matrices (`*SeatMatrix.pdf`, `2026_fe_seatmatrix_V1.pdf`) | PDF | Probably, own parser | Not yet inspected |
| Cut-off lists are for Home/Other-than-Home/State seats; "Minority" included in the same file | | | Seat-type distinction preserved via section headings |
| DMER / MCC (NEET) | unknown | Unknown | Phase 6 |
| NIRF | site returns 403 to scripts | **Manual** download | Ask permission / use official downloads |
| Fees (MahaFRA), AICTE approvals/intake, AISHE, placements | unknown | Unknown / likely manual | Show "Data not available" until sourced |
| College address/district | not in cut-off PDFs | Manual or AICTE | Locations empty until sourced |

**First usable dataset:** `http://fe2025.mahacet.org/2024/2024ENGG_CAP1_CutOff.pdf` (MHT-CET, 2024-25, CAP Round I, 1,590 pages). Then 2024 R2/R3, 2023, 2022 with the same parser.
