def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converts a hex color string to an RGB tuple.

    Args:
        hex_color: A 6-character hex string, with or without leading '#'.

    Returns:
        A tuple of (red, green, blue) values in the range 0-255.
    """
    hex_color = hex_color.strip()
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)
