from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import replace

from .hashing import semantic_hash, unit_hash_payload
from .model import Marker, PlanSegment, PlanUnit


def make_units(
    segments: tuple[PlanSegment, ...], markers: tuple[Marker, ...], kind: str
) -> tuple[PlanUnit, ...]:
    groups: dict[tuple[int, int], list[PlanSegment]] = defaultdict(list)
    for segment in segments:
        groups[(segment.paragraph, segment.sentence if kind == "sentence" else -1)].append(segment)
    units = []
    for index, ((_paragraph, _sentence), group) in enumerate(sorted(groups.items())):
        start, end = group[0].spoken_start, group[-1].spoken_end
        marker_ids = tuple(
            marker.id for marker in markers if start <= marker.spoken_position <= end
        )
        provisional = PlanUnit(
            f"unit-{index:04d}", index, kind, start, end, tuple(x.id for x in group), marker_ids
        )
        units.append(
            replace(
                provisional,
                content_hash=semantic_hash(unit_hash_payload(_UnitView(group, marker_ids))),
            )
        )
    return tuple(units)


class _UnitView:
    def __init__(self, segments: Iterable[PlanSegment], marker_ids: tuple[str, ...]):
        self.segments = tuple(segments)
        self.marker_ids = marker_ids
