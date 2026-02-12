import corti_canal


def test_version_fallback():
    assert isinstance(corti_canal.__version__, str)
