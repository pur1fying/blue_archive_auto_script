"""Keep lesson preferences when regions are added to the catalog."""


def normalize_lesson_preferences(times, priorities, region_count):
    """Preserve existing regions and leave newly added regions unselected."""
    times = list(times[:region_count])
    priorities = [list(levels) for levels in priorities[:region_count]]
    times.extend([0] * (region_count - len(times)))
    priorities.extend(
        ["primary", "normal", "advanced", "superior"]
        for _ in range(region_count - len(priorities))
    )
    return times, priorities
