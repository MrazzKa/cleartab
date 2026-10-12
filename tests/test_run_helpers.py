from pipeline.run import parse_date


def test_parse_date_formats_seen_in_files():
    assert parse_date("2026-04-01") == "2026-04-01"      # HonorHealth, Banner
    assert parse_date("2/1/2026") == "2026-02-01"        # Exceptional
    assert parse_date("08/14/2026") == "2026-08-14"      # Mayo
    assert parse_date("not a date") is None
