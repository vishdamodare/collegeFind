import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from parsers.cet_seat_matrix import MatrixResult, RE_PUB, _State, consume_page

# Text of pages 1-2 of the official 2024 Provisional Seat Matrix (CAP Round I), as extracted from the PDF.
PAGE1 = """Government of Maharashtra
Published Date : 08/08/2024
Autonomous Institute
01002 - Government College of Engineering, Amravati
Government Autonomous CAP Seats:60
Choice Code Course Name SI MS Seats Minority Seats All India Institute Seats Orphan
0100219110 Civil Engineering 60 60 0 0 0 1
Category OPEN SC ST VJ/DT NTB NTC NTD OBC SEBC Total
Economically Weaker Section (EWS) Seats: 6 Tution Fee Waiver Scheme Choice Code: 0100219111T : Seats: 3"""
PAGE2 = """01002 - Government College of Engineering, Amravati
Government Autonomous CAP Seats:60
Choice Code Course Name SI MS Seats Minority Seats All India Institute Seats Orphan
0100224210 Computer Science and Engineering 60 60 0 0 0 1"""


def test_course_rows_status_and_publication_date():
    res, st = MatrixResult(), _State()
    consume_page(PAGE1, 1, res, st); consume_page(PAGE2, 2, res, st)
    assert res.errors == []
    assert [(r.institute_code, r.choice_code, r.course_name, r.status_raw) for r in res.rows] == [
        ("01002", "0100219110", "Civil Engineering", "Government Autonomous"),
        ("01002", "0100224210", "Computer Science and Engineering", "Government Autonomous")]
    r = res.rows[0]
    assert (r.si, r.ms_seats, r.minority_seats, r.all_india_seats, r.institute_seats, r.orphan_seats) == (60, 60, 0, 0, 0, 1)
    m = RE_PUB.search(PAGE1)
    assert (m.group(1), m.group(2), m.group(3)) == ("08", "08", "2024")


def test_tfws_choice_code_line_is_not_mistaken_for_a_course_and_2023_zero_dropped_codes_pad():
    res, st = MatrixResult(), _State()
    consume_page("1002 - Government College of Engineering, Amravati\nGovernment Autonomous CAP Seats:60\n"
                 "Choice Code Course Name SI MS Seats Minority Seats All India Institute Orphan\nSeats\n"
                 "100219110 Civil Engineering 60 60 0 0 0 1\n0100219111T Seats: 3", 1, res, st)
    assert [r.choice_code for r in res.rows] == ["0100219110"] and res.rows[0].institute_code == "01002"


def test_unparsable_course_row_is_reported_not_skipped():
    res, st = MatrixResult(), _State()
    consume_page(PAGE1.split("0100219110")[0] + "0100219110 Civil Engineering sixty 60 0 0 0 1", 1, res, st)
    assert len(res.errors) == 1 and not res.rows


def test_choice_code_must_match_its_institute():
    res, st = MatrixResult(), _State()
    consume_page(PAGE1.split("0100219110")[0] + "0999919110 Civil Engineering 60 60 0 0 0 1", 1, res, st)
    assert len(res.errors) == 1 and not res.rows


def test_2026_two_orphan_columns_do_not_shift_the_intake():
    # 2026 prints "OrphanI OrphanN" (Institutional / Non-Institutional): 7 numbers instead of 6.
    from parsers.cet_seat_matrix import MatrixResult, _State, consume_page
    text = ("01002 - Government College of Engineering, Amravati\n"
            "Government Autonomous CAP Seats:60\n"
            "Choice Code Course Name SI MS Seats Minority Seats All India Institute Seats OrphanI OrphanN\n"
            "0100219110 Civil Engineering 60 60 0 0 0 1 2\n")
    res, st = MatrixResult(), _State()
    consume_page(text, 1, res, st)
    r = res.rows[0]
    assert (r.course_name, r.si, r.ms_seats, r.minority_seats, r.all_india_seats, r.institute_seats, r.orphan_seats) == \
        ("Civil Engineering", 60, 60, 0, 0, 0, 3)
    assert res.errors == []


def test_shifted_columns_are_reported_not_stored():
    # Old one-orphan header but a row with an extra number: the sum check must refuse it.
    from parsers.cet_seat_matrix import MatrixResult, _State, consume_page
    text = ("01002 - Government College of Engineering, Amravati\n"
            "Government Autonomous CAP Seats:60\n"
            "Choice Code Course Name SI MS Seats Minority Seats All India Institute Seats Orphan\n"
            "0100219110 Civil Engineering 60 60 0 0 0 1 0\n")
    res, st = MatrixResult(), _State()
    consume_page(text, 1, res, st)
    assert res.rows == [] and "do not add up" in res.errors[0][1]


def test_fitz_fallback_keeps_left_to_right_order_within_a_row(tmp_path):
    # 2026: some pages break pdfminer; the PyMuPDF fallback must rebuild "status CAP Seats:N" even when
    # the right-hand words sit a fraction of a point higher than the left-hand ones.
    import fitz
    from parsers.cet_seat_matrix import fitz_page_text
    d = fitz.open(); p = d.new_page()
    p.insert_text((300, 100.0), "CAP Seats:60"); p.insert_text((50, 100.2), "Government Autonomous")
    p.insert_text((50, 120), "0100219110 Civil Engineering 60 60 0 0 0 1 0")
    f = tmp_path / "m.pdf"; d.save(f)
    assert fitz_page_text(str(f), 1).split("\n") == ["Government Autonomous CAP Seats:60",
                                                     "0100219110 Civil Engineering 60 60 0 0 0 1 0"]
