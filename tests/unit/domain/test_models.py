import pytest

from pnr_convertor.domain.models import SegmentStatus, SegmentStatusCategory


@pytest.mark.parametrize(
    ("code", "category"),
    [
        ("HK", SegmentStatusCategory.CONFIRMED),
        ("HL", SegmentStatusCategory.WAITLISTED),
        ("NN", SegmentStatusCategory.REQUESTED),
        ("UN", SegmentStatusCategory.CANCELLED),
        ("ZZ", SegmentStatusCategory.UNKNOWN),
    ],
)
def test_segment_status_category(code: str, category: SegmentStatusCategory) -> None:
    assert SegmentStatus(code).category is category


def test_segment_status_description() -> None:
    assert SegmentStatus("SS").description == "Sold"
    assert SegmentStatus("ZZ").description is None
