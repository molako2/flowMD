"""La compilation à la volée de PyTorch doit être désactivée (Windows sans MSVC)."""

import os


def test_torchdynamo_disabled_after_import():
    import flowmd  # noqa: F401

    assert os.environ.get("TORCHDYNAMO_DISABLE") == "1"


def test_shorten_error_dedupes_and_truncates():
    from flowmd.jobs import shorten_error

    repeated = " ; ".join(["InvalidCxxCompiler: Compiler: cl is not found"] * 21)
    compact = shorten_error(repeated)
    assert compact.count("InvalidCxxCompiler") == 1

    long_message = "x" * 2000
    assert len(shorten_error(long_message)) <= 710
