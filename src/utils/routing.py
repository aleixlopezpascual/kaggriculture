"""Kaggriculture Manhattan routing and pathfinding utilities."""


def manhattan_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Calculates Manhattan distance between two 2D coordinates."""
    return abs(x1 - x2) + abs(y1 - y2)


def find_shortest_path(
    start_x: int, start_y: int, end_x: int, end_y: int
) -> list[tuple[str, str]]:
    """Generates a sequence of move commands towards the target tile.

    Returns:
        List of tuples: [("MOVE", direction), ...]
    """
    path = []
    curr_x, curr_y = start_x, start_y

    while curr_x != end_x:
        if curr_x < end_x:
            path.append(("MOVE", "RIGHT"))
            curr_x += 1
        else:
            path.append(("MOVE", "LEFT"))
            curr_x -= 1

    while curr_y != end_y:
        if curr_y < end_y:
            path.append(("MOVE", "DOWN"))
            curr_y += 1
        else:
            path.append(("MOVE", "UP"))
            curr_y -= 1

    return path
