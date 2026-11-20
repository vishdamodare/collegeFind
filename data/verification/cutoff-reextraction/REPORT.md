# cutoff-reextraction
Independent PyMuPDF extractor (extract.py; row grouping by y, column by horizontal overlap of rank+percentile box with header span) vs DB (compare.py). Raw numbers: report.json, extract_log.json.
Result: 187,149 DB cutoff_records, 187,149 extracted cells, 187,149 exact matches (rank, percentile, 0.0 -> NULL), 0 only-in-DB, 0 only-in-PDF, 0 value differences, 0 source_page mismatches, 0 duplicate keys, 0 fallback column assignments, 0 unpaired ranks.
Overflow bands skipped: 86 stage-rows / 266 cells (2022R1 16/56, 2023R1 32/104, 2023R2 1/1, 2024R1 24/91, 2024R2 13/14) = documented gap; not in DB.
Caveat: overflow cells were skipped, not extracted, so their absence from the DB is not independently cell-verified beyond the count.
