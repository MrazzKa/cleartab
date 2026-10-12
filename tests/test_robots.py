from pipeline.robots import Robots

NORTHWEST = """user-agent: *
allow: /*.ico$
allow: /Uploads/public/documents/favicons/*
disallow: /Uploads/*
"""
COMMONSPIRIT = "User-agent: *\nAllow: /\n\nDisallow: /*default*\nDisallow: /*conf*\n"


def test_wildcard_disallow_blocks_northwest_files():
    r = Robots(200, NORTHWEST)
    url = ("https://www.healthiertucson.com/Uploads/Public/Documents/charge-masters/charge-masters-2024/"
           "621762430_northwest-medical-center-tucson_standardcharges.csv")
    assert not r.can_fetch(url)
    assert r.can_fetch("https://www.healthiertucson.com/cms-hpt.txt")
    assert not r.can_fetch("https://www.healthiertucson.com/Uploads/x.ico")  # longer rule wins
    assert r.can_fetch("https://www.healthiertucson.com/favicon.ico")


def test_longest_match_and_allow_on_tie():
    r = Robots(200, COMMONSPIRIT)
    assert r.can_fetch("https://www.commonspirit.org/content/dam/x/finance/price-transparency/a_standardcharges.json")
    assert not r.can_fetch("https://www.commonspirit.org/content/default/page")


def test_status_codes():
    assert Robots(403).can_fetch("https://images.example/x.csv")      # 4xx: no restrictions (RFC 9309)
    assert Robots(404).can_fetch("https://images.example/x.csv")
    assert not Robots(503).can_fetch("https://images.example/x.csv")  # 5xx: assume disallow
    assert not Robots(None).can_fetch("https://images.example/x.csv")  # unreachable


def test_disallow_root_and_crawl_delay():
    r = Robots(200, "User-Agent: *\nDisallow: /\n")
    assert not r.can_fetch("https://www.tmcaz.com/cms-hpt.txt")
    assert Robots(200, "User-agent: * \nCrawl-Delay: 20\n").crawl_delay == 20.0


def test_specific_agent_group_wins():
    r = Robots(200, "User-agent: *\nDisallow: /\n\nUser-agent: ClearTab-capstone\nAllow: /\n")
    assert r.can_fetch("https://x.org/file.csv")
