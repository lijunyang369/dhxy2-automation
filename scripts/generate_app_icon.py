from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


def _lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def _vertical_gradient(size: int, top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    image = Image.new("RGBA", (size, size))
    pixels = image.load()
    for y in range(size):
        t = y / max(1, size - 1)
        color = (
            _lerp(top[0], bottom[0], t),
            _lerp(top[1], bottom[1], t),
            _lerp(top[2], bottom[2], t),
            255,
        )
        for x in range(size):
            pixels[x, y] = color
    return image


def _radial_glow(size: int, color: tuple[int, int, int, int], scale: float) -> Image.Image:
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    margin = int(size * (1 - scale) / 2)
    draw.ellipse((margin, margin, size - margin, size - margin), fill=color)
    return glow.filter(ImageFilter.GaussianBlur(radius=size // 10))


def _node(draw: ImageDraw.ImageDraw, center: tuple[int, int], radius: int, fill: tuple[int, int, int, int]) -> None:
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def build_icon(size: int = 1024) -> Image.Image:
    canvas = _vertical_gradient(size, (10, 22, 44), (4, 10, 22))
    canvas.alpha_composite(_radial_glow(size, (24, 128, 122, 90), 0.64))
    canvas.alpha_composite(_radial_glow(size, (255, 193, 94, 50), 0.40))

    vignette = Image.new("L", (size, size), 0)
    ImageDraw.Draw(vignette).ellipse(
        (size * 0.08, size * 0.08, size * 0.92, size * 0.92),
        fill=220,
    )
    vignette = ImageChops.invert(vignette.filter(ImageFilter.GaussianBlur(radius=size // 7)))
    vignette_rgba = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    vignette_rgba.putalpha(vignette)
    canvas.alpha_composite(vignette_rgba)

    draw = ImageDraw.Draw(canvas)
    outer = int(size * 0.11)
    draw.rounded_rectangle(
        (outer, outer, size - outer, size - outer),
        radius=int(size * 0.22),
        outline=(222, 184, 104, 255),
        width=max(10, size // 42),
    )
    inner = int(size * 0.18)
    draw.rounded_rectangle(
        (inner, inner, size - inner, size - inner),
        radius=int(size * 0.17),
        outline=(92, 232, 213, 110),
        width=max(6, size // 96),
    )

    cx = cy = size // 2
    gold = (232, 193, 113, 255)
    cyan = (114, 236, 223, 255)
    cyan_soft = (74, 178, 177, 255)

    # Orbit ring and motion notch to hint automation/runtime.
    ring_box = (int(size * 0.28), int(size * 0.28), int(size * 0.72), int(size * 0.72))
    draw.arc(ring_box, start=26, end=330, fill=gold, width=max(12, size // 38))
    draw.arc(
        (ring_box[0] + size * 0.02, ring_box[1] + size * 0.02, ring_box[2] + size * 0.02, ring_box[3] + size * 0.02),
        start=212,
        end=24,
        fill=cyan_soft,
        width=max(6, size // 90),
    )

    # Core geometry: a rune-like "2" built from linked nodes/paths, readable at small sizes.
    path = [
        (int(size * 0.36), int(size * 0.33)),
        (int(size * 0.58), int(size * 0.33)),
        (int(size * 0.63), int(size * 0.43)),
        (int(size * 0.44), int(size * 0.55)),
        (int(size * 0.40), int(size * 0.66)),
        (int(size * 0.64), int(size * 0.66)),
    ]
    draw.line(path[:3], fill=cyan, width=max(18, size // 30), joint="curve")
    draw.line(path[2:5], fill=gold, width=max(18, size // 30), joint="curve")
    draw.line(path[4:], fill=cyan, width=max(18, size // 30), joint="curve")

    for point, color in (
        (path[0], cyan),
        (path[2], gold),
        (path[4], gold),
        (path[5], cyan),
    ):
        _node(draw, point, max(11, size // 44), color)

    # Crosshair spark at top-right for "automation target /识别".
    spark_center = (int(size * 0.74), int(size * 0.26))
    spark_r = max(8, size // 60)
    draw.line(
        (spark_center[0] - spark_r * 2, spark_center[1], spark_center[0] + spark_r * 2, spark_center[1]),
        fill=(255, 216, 135, 230),
        width=max(4, size // 160),
    )
    draw.line(
        (spark_center[0], spark_center[1] - spark_r * 2, spark_center[0], spark_center[1] + spark_r * 2),
        fill=(255, 216, 135, 230),
        width=max(4, size // 160),
    )
    _node(draw, spark_center, spark_r, (255, 240, 204, 255))

    return canvas


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    output_dir = project_root / "resources" / "app"
    output_dir.mkdir(parents=True, exist_ok=True)

    icon = build_icon(1024)
    png_path = output_dir / "dhxy2-platform-icon.png"
    ico_path = output_dir / "dhxy2-platform.ico"
    icon.save(png_path)
    icon.save(ico_path, sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])

    print(png_path)
    print(ico_path)


if __name__ == "__main__":
    main()
