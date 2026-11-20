# Visual audit report

Method: for 65 pages (9 cut-off PDFs, 6+ random pages each, seed 20241110, stratified by sixths of each file, plus the 11 required hard pages) the PDF page was rendered to PNG (PyMuPDF, zoom 2, cropped, wide pages split in two overlapping halves), opened with the Read tool and compared by eye, value by value, with a DB dump of cutoff_records for that file+page (course choice_code, seat_type, category_code_raw, stage_label, rank, percentile). Files: crops/*.png, dbdump/*.txt, sample.py dump.py crop.py. (img/ and db/ hold stale mis-tagged earlier output, ignore.)

Result: all 1119 rank/percentile values on 63 data pages were stored under the correct college, course, seat section, stage label and category column with correct rank and percentile. 7 of them carry a category_code_raw missing its trailing S (see findings). No value was misplaced or wrong. Two sampled pages (2022 R1 p389 and p1028) are overflow-only pages: DB has 0 rows for them (documented gap, 3 and 15 printed cells).

| file | page | values checked | correct | note |
|---|---|---|---|---|
| 2022R1 | 8 | 25 | 25 |  |
| 2022R1 | 272 | 6 | 6 |  |
| 2022R1 | 388 | 80 | 77 | very wide table verified both halves; overflow cells for 3215 course 321524510 (DEFROBCS 3244 / ORPHAN 91883 / EWS 983) printed on p389 not in DB (documented gap) LABEL: 3 cells have category_code_raw missing trailing S (printed wrapped 'PWDROBC'/'S' or 'DEFRSEBC'/'S') |
| 2022R1 | 389 | 0 | 0 | overflow-only page: 3 printed cells (DEFROBCS 3244 91883 ORPHAN EWS 983) absent from DB (documented gap); DB has 0 rows for page |
| 2022R1 | 481 | 24 | 24 |  |
| 2022R1 | 845 | 18 | 18 |  |
| 2022R1 | 1028 | 0 | 0 | overflow-only page: 15 printed cells absent from DB (documented gap); DB has 0 rows for page |
| 2022R1 | 1279 | 19 | 19 |  |
| 2022R2 | 189 | 29 | 29 |  |
| 2022R2 | 305 | 14 | 14 |  |
| 2022R2 | 592 | 7 | 7 |  |
| 2022R2 | 641 | 15 | 15 |  |
| 2022R2 | 830 | 19 | 19 |  |
| 2022R2 | 1177 | 3 | 3 |  |
| 2022R3 | 40 | 7 | 7 | minority section MH label verified |
| 2022R3 | 122 | 12 | 12 |  |
| 2022R3 | 241 | 13 | 13 |  |
| 2022R3 | 412 | 4 | 4 |  |
| 2022R3 | 655 | 6 | 6 |  |
| 2022R3 | 905 | 11 | 11 |  |
| 2022R3 | 1006 | 3 | 3 |  |
| 2023R1 | 49 | 6 | 6 |  |
| 2023R1 | 301 | 6 | 6 |  |
| 2023R1 | 389 | 29 | 29 |  |
| 2023R1 | 572 | 18 | 18 |  |
| 2023R1 | 755 | 9 | 9 |  |
| 2023R1 | 1029 | 2 | 2 |  |
| 2023R1 | 1305 | 3 | 3 |  |
| 2023R2 | 92 | 22 | 22 |  |
| 2023R2 | 379 | 16 | 16 |  |
| 2023R2 | 648 | 7 | 7 |  |
| 2023R2 | 775 | 20 | 20 |  |
| 2023R2 | 950 | 8 | 8 |  |
| 2023R2 | 1250 | 23 | 23 |  |
| 2023R3 | 184 | 4 | 4 |  |
| 2023R3 | 292 | 14 | 14 | MH_TO_AI section verified |
| 2023R3 | 391 | 4 | 4 |  |
| 2023R3 | 482 | 12 | 12 |  |
| 2023R3 | 775 | 16 | 16 |  |
| 2023R3 | 956 | 8 | 8 |  |
| 2023R3 | 1021 | 10 | 10 |  |
| 2024R1 | 251 | 96 | 93 |  LABEL: 3 cells have category_code_raw missing trailing S (printed wrapped 'PWDROBC'/'S' or 'DEFRSEBC'/'S') |
| 2024R1 | 266 | 55 | 55 | TFWS 0.0000000 printed -> NULL in DB as documented |
| 2024R1 | 301 | 19 | 19 |  |
| 2024R1 | 488 | 6 | 6 |  |
| 2024R1 | 542 | 21 | 21 |  |
| 2024R1 | 609 | 14 | 14 |  |
| 2024R1 | 939 | 19 | 19 |  |
| 2024R1 | 1111 | 25 | 25 |  |
| 2024R1 | 1570 | 8 | 8 |  |
| 2024R2 | 205 | 20 | 20 | course spanning two pages (first part); I-Non PWD and VII rows verified |
| 2024R2 | 206 | 4 | 4 | continuation page (State Level; I-Non Defence and VII rows) attached to correct course |
| 2024R2 | 256 | 32 | 32 |  |
| 2024R2 | 511 | 6 | 6 |  |
| 2024R2 | 753 | 14 | 14 |  |
| 2024R2 | 870 | 30 | 30 |  |
| 2024R2 | 1241 | 31 | 31 |  |
| 2024R2 | 1331 | 6 | 6 |  |
| 2024R3 | 136 | 21 | 21 |  |
| 2024R3 | 341 | 4 | 4 |  |
| 2024R3 | 563 | 16 | 16 |  |
| 2024R3 | 755 | 39 | 39 |  |
| 2024R3 | 1096 | 45 | 44 |  LABEL: 1 cells have category_code_raw missing trailing S (printed wrapped 'PWDROBC'/'S' or 'DEFRSEBC'/'S') |
| 2024R3 | 1155 | 15 | 15 |  |
| 2024R3 | 1338 | 21 | 21 |  |

## Findings
1. category_code_raw truncation (minor, systematic). When a header cell wraps ("PWDROBC" / "S", "DEFRSEBC" / "S", "PWDRSEBC" / "S") the DB stores the code without the trailing S. Confirmed in the PDF text of 2022 R1 p388 and 2024 R3 p1096. In the sample: 2022 R1 p388 (3 cells PWDROBC), 2024 R1 p251 (3 cells PWDROBC), 2024 R3 p1096 (1 cell DEFRSEBC). Whole DB: PWDROBC 186 rows, DEFRSEBC 77, PWDRSEBC 6 (269 rows; zero rows with PWDROBCS/DEFRSEBCS/PWDRSEBCS). Rank, percentile, column placement are correct; only the code string differs from the printed one. Check whether downstream category mapping handles these codes.
2. Overflow gap confirmed visually: 2022 R1 p388 course 321524510 has 3 cells printed on p389 (DEFROBCS 3244 / 98.1223099, ORPHAN 91883 / 39.4196471, EWS 983 / 99.3529240) not in DB; p1028 is an overflow-only page with 15 printed cells (9+5+1) not in DB. Documented, not counted as discrepancies. Of the 65 sampled pages only p388 is followed by an overflow page (checked programmatically for all sample+1 pages).
3. TFWS 0.0000000 (2024 R1 p266 course 0303651310, TFWS rank 1102) is NULL in DB with rank kept, as documented.
4. Verified hard pages: 2022 R1 p388-389, 2022 R3 p40 (MH minority label), 2023 R3 p292 (MH_TO_AI), 2024 R3 p1096, 2024 R1 p266, 2024 R2 p205+p206 (continuation, I-Non PWD / I-Non Defence / VII), 2024 R1 p542, 2023 R1 p301, 2024 R1 p301.
Limits: visual comparison by one reader of rendered crops; values were read from the images and compared against the DB dump, not OCR. Only the sampled pages were audited.
