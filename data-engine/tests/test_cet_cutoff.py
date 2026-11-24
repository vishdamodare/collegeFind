import json, os, sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers.cet_cutoff import CetCutoffParser

# Page 301 of the official 2024 CAP Round I cut-off list (Saraswati College of Engineering, Civil, code 0315419110).
# Expected values transcribed by hand from the printed page.
FIX = os.path.join(os.path.dirname(__file__), "..", "fixtures", "cet2024_cap1_p301_words.json")


def parse():
    p = CetCutoffParser()
    p.feed_page(301, json.load(open(FIX)))
    return p.res


def test_no_errors_and_cell_count():
    r = parse()
    assert r.errors == [] and len(r.cells) == 19


def test_sparse_stage_row_aligns_by_position_not_order():
    # Stage II has 4 values that belong to the LAST four of ten header columns, not the first four.
    s2 = {c.category_code: c.closing_rank for c in parse().cells if c.stage == 2}
    assert s2 == {"LSCH": 166545, "LNT2H": 172968, "LNT3H": 164621, "LOBCH": 149111}


def test_rank_and_percentile_pair_and_context():
    c = next(c for c in parse().cells if c.category_code == "GOPENH")
    assert (c.institute_code, c.choice_code, c.seat_type_code) == ("03154", "0315419110", "HU_TO_HU")
    assert c.closing_rank == 92688 and c.closing_percentile == Decimal("65.3627105")
    assert c.original_text == "92688 (65.3627105)"


def test_sections_not_mixed():
    cells = parse().cells
    assert {c.category_code for c in cells if c.seat_type_code == "STATE_LEVEL"} == {"DEFOPENS", "EWS"}


def test_course_code_with_trailing_letter_is_not_merged_into_previous_course():
    # Page 255: course '0302524570U' (letter suffix). Previously unmatched -> cells leaked to the prior course.
    p = CetCutoffParser()
    p.feed_page(255, json.load(open(FIX.replace("p301", "p255"))))
    r = p.res
    assert r.errors == []
    assert {c.choice_code for c in r.cells} == {"0302524570U"}
    c = next(c for c in r.cells if c.category_code == "GOPENH")
    assert (c.closing_rank, c.closing_percentile) == (16913, Decimal("94.3796484"))
    assert len(r.cells) == 5


def test_unrecognised_code_line_resets_context_instead_of_reusing_it():
    p = CetCutoffParser()
    w = lambda t, x, top: {"text": t, "x0": x, "x1": x + 5 * len(t), "top": top}
    p.feed_page(1, [w("01002", 10, 10), w("-", 60, 10), w("Some", 70, 10), w("College", 100, 10)])
    p.feed_page(1, [w("0100299999!", 10, 30), w("-", 90, 30), w("Odd", 100, 30)])
    assert p.course is None and len(p.res.errors) == 1


def test_course_code_regex_accepts_letter_suffixes():
    from parsers.cet_cutoff import RE_COURSE
    for code in ("0100219110", "0302524570U", "0303337293LK", "100219110"):
        m = RE_COURSE.match(f"{code} - Some Engineering")
        assert m.group(1) + m.group(2) == code


def test_2023_format_zero_padded_codes_and_status_without_university():
    # Page 301 of the 2023-24 CAP I list: codes printed without leading zeros ('3183', '318324610')
    # and a 'Status:' line with no 'Home University :' part. Expected values transcribed from the printed page.
    p = CetCutoffParser()
    p.feed_page(301, json.load(open(FIX.replace("cet2024", "cet2023"))))
    r = p.res
    assert r.errors == []
    got = {(c.seat_type_code, c.category_code): (c.closing_rank, c.closing_percentile) for c in r.cells}
    assert got == {
        ("HU_TO_HU", "GOPENH"): (28852, Decimal("88.1444070")), ("HU_TO_HU", "LOPENH"): (36384, Decimal("84.9532361")),
        ("OHU_TO_OHU", "GOPENO"): (50896, Decimal("78.3308876")), ("OHU_TO_OHU", "LOPENO"): (78011, Decimal("63.6910141")),
        ("STATE_LEVEL", "MI"): (46109, Decimal("80.6210251")), ("STATE_LEVEL", "TFWS"): (14693, Decimal("94.1946157")),
    }
    assert {(c.institute_code, c.choice_code) for c in r.cells} == {("03183", "0318324610")}
    assert r.cells[0].status_raw == "Un-Aided Religious Minority - Muslim" and r.cells[0].university_raw == ""


def test_course_code_not_matching_institute_is_rejected():
    p = CetCutoffParser()
    w = lambda t, x, top: {"text": t, "x0": x, "x1": x + 5 * len(t), "top": top}
    p.feed_page(1, [w("01002", 10, 10), w("-", 60, 10), w("College", 70, 10)])
    p.feed_page(1, [w("0999919110", 10, 30), w("-", 90, 30), w("Civil", 100, 30)])
    assert p.course is None and len(p.res.errors) == 1


def _round2_pages():
    p = CetCutoffParser()
    for n in (205, 206):
        p.feed_page(n, json.load(open(FIX.replace("cet2024_cap1_p301", f"cet2024_cap2_p{n}"))))
    return p.res


def test_round2_stage_labels_two_line_labels_and_page_continuation():
    # 2024 CAP II pp.205-206: course 0225437210 spans two pages (page 206 repeats the college line, not the course),
    # and has stage rows 'I-Non PWD' / 'I-Non Defence' whose label wraps onto a second line, plus 'VII'.
    r = _round2_pages()
    assert r.errors == []
    got = {(c.seat_type_code, c.stage_label, c.category_code): (c.closing_rank, c.closing_percentile, c.choice_code)
           for c in r.cells}
    k = "0225437210"
    assert got[("HU_TO_HU", "I", "GOPENH")] == (161664, Decimal("20.9410678"), k)
    assert got[("HU_TO_HU", "I-Non PWD", "PWDOPENH")] == (111009, Decimal("56.0103934"), k)
    assert got[("STATE_LEVEL", "I", "TFWS")] == (147034, Decimal("32.8923205"), k)        # page 206, no course line
    assert got[("STATE_LEVEL", "I", "EWS")] == (176477, Decimal("4.5424794"), k)
    assert got[("STATE_LEVEL", "I-Non Defence", "DEFOPENS")] == (124712, Decimal("48.0648514"), k)
    assert got[("STATE_LEVEL", "VII", "DEFOBCS")] == (164539, Decimal("18.1287777"), k)
    assert {c.stage_label for c in r.cells} == {"I", "II", "VII", "I-Non PWD", "I-Non Defence"}


def test_unrecognised_row_in_table_is_reported_not_skipped():
    p = CetCutoffParser()
    w = lambda t, x, top: {"text": t, "x0": x, "x1": x + 5 * len(t), "top": top}
    p.feed_page(1, [w("01002", 10, 10), w("-", 60, 10), w("College", 70, 10),
                    w("0100219110", 10, 30), w("-", 90, 30), w("Civil", 100, 30),
                    w("State", 10, 50), w("Level", 40, 50),
                    w("Stage", 10, 70), w("GOPENS", 80, 70),
                    w("XIV", 10, 90), w("123", 80, 90)])
    assert any("Unrecognised row" in e[1] for e in p.res.errors)


def _fx(name):
    return json.load(open(os.path.join(os.path.dirname(FIX), name)))


def test_2022_minority_candidature_section_with_MH_row_label():
    # 2022 CAP III p.40: 'Minority Seats Allotted to Maharashtra State Candidature Candidates', header MI, row label 'MH'.
    p = CetCutoffParser()
    p.feed_page(40, _fx("cet2022_cap3_p40_words.json"))
    got = {(c.choice_code, c.seat_type_code, c.stage_label, c.category_code): (c.closing_rank, c.closing_percentile) for c in p.res.cells}
    assert got[("0112019110", "MIN_TO_MH", "MH", "MI")] == (122566, Decimal("0.1311825"))
    assert got[("0112024210", "MIN_TO_MH", "MH", "MI")] == (51430, Decimal("71.1253958"))
    assert got[("0112019110", "HU_TO_HU", "I", "GOPENH")] == (114224, Decimal("13.5440394"))
    assert got[("0112019110", "OHU_TO_HU", "I", "GOPENO")] == (115128, Decimal("12.2194150"))
    assert got[("0112024210", "OHU_TO_OHU", "I", "LOPENO")] == (68014, Decimal("59.5292331"))
    assert not [e for e in p.res.errors if "Unrecognised" in e[1]]


def test_page_width_overflow_band_is_attributed_by_y_position_to_the_previous_page():
    # 2022 CAP I p.389 holds only the overflow columns 'DEFROBCS ORPHAN EWS' of a table too wide for p.388.
    # Its header/rank/percentile rows sit at the same y as that table's rows on p.388.
    p = CetCutoffParser()
    p.feed_page(388, _fx("cet2022_cap1_p388_words.json"))
    p.feed_page(389, _fx("cet2022_cap1_p389_words.json"))
    got = {(c.choice_code, c.seat_type_code, c.stage_label, c.category_code): (c.closing_rank, c.closing_percentile)
           for c in p.res.cells if c.page == 389}
    assert got == {("0321524510", "STATE_LEVEL", "I", "DEFROBCS"): (3244, Decimal("98.1223099")),
                   ("0321524510", "STATE_LEVEL", "I", "ORPHAN"): (91883, Decimal("39.4196471")),
                   ("0321524510", "STATE_LEVEL", "I", "EWS"): (983, Decimal("99.3529240"))}
    assert p.res.errors == []


def test_overflow_band_without_previous_page_stays_a_reported_gap():
    # Without the wide page there is nothing to align to: never guess.
    p = CetCutoffParser()
    p.header = [(100.0, "GOPENS")]                           # stale header from an unrelated table
    p.feed_page(389, _fx("cet2022_cap1_p389_words.json"))
    assert p.res.cells == []
    assert sum("Overflow band" in e[1] for e in p.res.errors) == 3   # header + rank row + percentile row


def test_2023_round3_mh_seats_for_all_india_candidates_is_its_own_section_not_state_level():
    # 2023 CAP III p.292: 'Maharashtra State Seats Allotted to All India Candidature Candidates' follows a State Level
    # section. Before the fix its rows were silently filed under STATE_LEVEL (colliding with real State Level cells).
    p = CetCutoffParser()
    p.feed_page(292, _fx("cet2023_cap3_p292_words.json"))
    got = {(c.seat_type_code, c.category_code): (c.closing_rank, c.closing_percentile) for c in p.res.cells
           if c.choice_code == "0319824610"}
    assert got[("STATE_LEVEL", "TFWS")] == (64372, Decimal("71.4000828"))
    assert got[("STATE_LEVEL", "EWS")] == (86791, Decimal("58.1382561"))
    assert got[("MH_TO_AI", "EWS")] == (86767, Decimal("58.1382561"))
    keys = [(c.choice_code, c.seat_type_code, c.stage_label, c.category_code) for c in p.res.cells]
    assert len(keys) == len(set(keys))                      # no more colliding cells
    assert p.res.errors == []


def test_section_heading_is_never_swallowed_by_the_footer_whitelist():
    p = CetCutoffParser()
    w = lambda t, x, top: {"text": t, "x0": x, "x1": x + 5 * len(t), "top": top}
    p.feed_page(1, [w("01002", 10, 10), w("-", 60, 10), w("College", 70, 10),
                    w("0100219110", 10, 30), w("-", 90, 30), w("Civil", 100, 30),
                    w("State", 10, 50), w("Level", 40, 50), w("Stage", 10, 70), w("GOPENS", 80, 70),
                    # an UNKNOWN section heading that starts like the footer legend must be reported
                    w("Maharashtra", 10, 90), w("State", 60, 90), w("Seats", 90, 90), w("Allotted", 120, 90), w("to", 160, 90), w("Somebody", 180, 90)])
    assert any("Unrecognised row" in e[1] for e in p.res.errors)


def test_printed_zero_percentile_is_stored_as_missing_not_as_zero():
    # 2024 CAP I p.266: TFWS cell printed '1102 (0.0000000)'. The rank is real; there is no percentile.
    p = CetCutoffParser()
    p.feed_page(266, _fx("cet2024_cap1_p266_words.json"))
    z = [c for c in p.res.cells if c.original_text == "1102 (0.0000000)"]
    assert len(z) == 1
    assert z[0].category_code == "TFWS" and z[0].closing_rank == 1102
    assert z[0].closing_percentile is None            # never 0


def test_category_code_whose_last_letter_wrapped_to_the_next_line_is_restored():
    # 2022 CAP I p.388 prints 'PWDROBC' with a lone 'S' on the line below it. Stored as 'PWDROBC' before the fix.
    p = CetCutoffParser()
    p.feed_page(388, _fx("cet2022_cap1_p388_words.json"))
    cats = {c.category_code for c in p.res.cells}
    assert "PWDROBCS" in cats and "PWDROBC" not in cats
    assert p.res.errors == [] or all("Overflow" in e[1] for e in p.res.errors)


def test_wrapped_category_suffix_is_H_in_home_university_sections_and_S_in_state_level():
    # 2022 CAP I p.11: the Home University header cell 'PWDROBC' has a lone 'H' under it (PWDROBCH, not PWDROBCS).
    p = CetCutoffParser()
    p.feed_page(11, _fx("cet2022_cap1_p11_words.json"))
    hu = {c.category_code for c in p.res.cells if c.seat_type_code == "HU_TO_HU"}
    assert "PWDROBCH" in hu and "PWDROBC" not in hu and "PWDROBCS" not in hu
    # and the State Level table of page 388 still gets 'S'
    q = CetCutoffParser()
    q.feed_page(388, _fx("cet2022_cap1_p388_words.json"))
    st = {c.category_code for c in q.res.cells if c.seat_type_code == "STATE_LEVEL"}
    assert "PWDROBCS" in st
