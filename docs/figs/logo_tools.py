"""Tools to create the pkgcreator logo."""

from pathlib import Path


def dict_to_xml_object(name, config: dict) -> str:
    """Convert a dictionary to an xml object."""
    result = "\n\t".join(f'{key}="{value}"' for key, value in config.items())
    return f"<{name}\n\t{result} />"


def make_background_box(
    color: str = "",
    stroke_color: str = "",
    stroke_width: int = 2,
    width: float = 100,
    height: float = 100,
):
    """Make a colored box (e.g. as a background), widht/height are percent."""
    return dict_to_xml_object(
        "rect",
        {
            "id": "background",
            "width": f"{width}%",
            "height": f"{height}%",
            "fill": color,
            "stroke": stroke_color,
            "stroke-width": stroke_width,
        },
    )


def make_3d_box(
    x: float = 30,
    y: float = 30,
    height: float = 40,
    width: float = 40,
    delta_height: float = 10,  # to lazy to do angle calculation
    delta_width: float = 10,  # to lazy to do angle calculation
    front_color: str = "#f3c76b",
    side_color: str = "#d6a24c",
    top_color: str = "#ffe19c",
    stroke_color: str = "#a66a2c",
    stroke_width: int = 2,
):
    """Make a 3D box."""
    front = dict_to_xml_object(
        "rect",
        {
            "id": "package box front",
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "fill": front_color,
            # "stroke": stroke_color,
            # "stroke-width": stroke_width,
        },
    )

    x_right = x + width
    x_left = x - delta_width
    y_up = y - delta_height
    y_down = y + height
    front_top_left = f"{x},{y}"
    front_top_right = f"{x_right},{y}"
    front_bottom_left = f"{x},{y_down}"
    top_top_left = f"{x_left},{y_up}"
    top_top_right = f"{x_right - delta_width},{y_up}"
    side_bottom_left = f"{x_left},{y_down - delta_height}"

    top = dict_to_xml_object(
        "polygon",
        {
            "id": "package box top",
            "points": (
                f"{front_top_left} {front_top_right} {top_top_right} " f"{top_top_left}"
            ),
            "fill": top_color,
            # "stroke": stroke_color,
            # "stroke-width": stroke_width,
        },
    )

    side = dict_to_xml_object(
        "polygon",
        {
            "id": "package box side",
            "points": (
                f"{front_top_left} {top_top_left} {side_bottom_left} "
                f"{front_bottom_left}"
            ),
            "fill": side_color,
            # "stroke": stroke_color,
            # "stroke-width": stroke_width,
        },
    )

    outline = dict_to_xml_object(
        "path",
        {
            "id": "package box outline",
            "d": (
                f"M {top_top_left} V {y_down - delta_height} L {front_bottom_left} "
                f"H {x_right} V {y} L {top_top_right} Z"
            ),
            "fill": "none",
            "stroke": stroke_color,
            "stroke-width": stroke_width,
        },
    )

    return "\n\n".join([front, top, side, outline])


def make_text(
    text: str,
    x: float = 30,
    y: float = 30,
    color: str = "#000000",
    font: str = "Liberation Sans",
    size: int = 20,
    weight: str = "bold",
    stroke_color: str = "",
    stroke_width: float = 2,
):
    """Make a text element."""
    return (
        f'<text id="text-{text}" x="{x}" y="{y}" font-family="{font}" '
        f'font-size="{size}" font-weight="{weight}" fill="{color}" '
        f'stroke="{stroke_color}" stroke-width="{stroke_width}">'
        f"\n\t{text}\n</text>"
    )


def save_svg(
    filename: str | Path,
    content: str,
    overwrite: bool = False,
    width: int = 200,
    height: int = 200,
    replace_tab: str = "   ",
    background_color: str = "",
):
    """Save a svg content string to an svg document (header is created)."""
    filepath = Path(filename)
    if filepath.exists() and not overwrite:
        raise FileExistsError(f"{filepath} exists!")
    header = "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            '<svg xmlns="http://www.w3.org/2000/svg"',
            f'\twidth="{width}" height="{height}"',
            f'\tviewBox="0 0 {width} {height}"',
            f'\tstyle="background-color:{background_color}"',
            '\tversion="1.1">',
        ]
    )
    file_content = f"{header}\n{content}\n</svg>"
    if replace_tab:
        file_content = file_content.replace("\t", replace_tab)

    with open(filename, "w") as file:
        file.write(file_content)


if __name__ == "__main__":
    filename = "pkgcreator_logo.svg"
    overwrite = True
    width = 200
    height = 70
    font = "Liberation Sans"
    font_size = 20
    # Python colors: #3572A5 and #FFD43B
    # Terminal: #1e2933
    background_color = ""

    # terminal_box = make_background_box(
    #     color="#1d405d", stroke_color="#1e2933", stroke_width=5
    # )

    box_config = {"x": 30, "y": 20, "width": 40, "height": 40}

    box = make_3d_box(**box_config)
    x_text = box_config["x"] + box_config["width"] + 10
    y_text = box_config["y"] + box_config["height"] / 2 + 5
    x_symbol = box_config["x"] + box_config["width"] / 2 - 5
    y_symbol = y_text + 2
    console_symbol = make_text(
        ">",
        x=x_symbol,
        y=y_symbol,
        font=font,
        size=font_size + 4,
        color="#3572A5",
        stroke_color="#1d405d",
        stroke_width=0.4,
    )
    text = make_text(
        "pkgcreator",
        x=x_text,
        y=y_text,
        font=font,
        size=font_size,
        color="#FFD43B",
        stroke_color="#1d405d",
        stroke_width=0.4,
    )
    content = "\n".join(
        [
            # terminal_box,
            box,
            console_symbol,
            text,
        ]
    )
    save_svg(
        filename,
        content,
        overwrite=overwrite,
        width=width,
        height=height,
        background_color=background_color,
    )
