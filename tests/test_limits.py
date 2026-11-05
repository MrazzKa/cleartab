from api.limits import DAY, HOUR, ReadLimiter


def test_per_hour_then_recovers():
    lim = ReadLimiter(per_hour=2, per_day=10, global_day=100)
    assert lim.check("a", now=0) is None
    assert lim.check("a", now=10) is None
    assert "last hour" in lim.check("a", now=20)
    assert lim.check("b", now=20) is None          # other clients are not affected
    assert lim.check("a", now=HOUR + 11) is None    # first read has left the hour window


def test_per_day_and_global():
    lim = ReadLimiter(per_hour=0, per_day=2, global_day=3)
    assert lim.check("a", now=0) is None
    assert lim.check("a", now=1) is None
    assert "today's limit for reading" in lim.check("a", now=2)
    assert lim.check("b", now=3) is None
    assert "for everyone" in lim.check("c", now=4)
    assert lim.check("c", now=DAY + 5) is None


def test_refused_reads_are_not_counted():
    lim = ReadLimiter(per_hour=1, per_day=0, global_day=0)
    assert lim.check("a", now=0) is None
    for t in range(1, 50):
        assert lim.check("a", now=t) is not None
    assert lim.check("a", now=HOUR + 1) is None
