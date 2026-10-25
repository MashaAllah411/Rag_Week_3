"""Guards the System / Light / Dark theme switcher.

Streamlit only offers the switcher when more than one theme is defined. A single [theme] block
(for example `base = "light"`) pins one theme and silently removes it, which is how it was lost before.
"""
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _theme():
    return tomllib.loads((ROOT / ".streamlit" / "config.toml").read_text(encoding="utf-8"))["theme"]


def test_both_light_and_dark_themes_are_defined():
    theme = _theme()
    assert {"light", "dark"} <= set(theme)
    for name in ("light", "dark"):
        assert {"primaryColor", "backgroundColor", "secondaryBackgroundColor", "textColor"} <= set(theme[name])


def test_no_single_pinned_theme():
    """Scalar keys directly under [theme] (base, backgroundColor, ...) pin one theme and hide the switcher."""
    assert [k for k, v in _theme().items() if not isinstance(v, dict)] == []


def test_dark_theme_is_actually_dark_and_light_is_light():
    def luminance(hex_colour):
        r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
        return 0.299 * r + 0.587 * g + 0.114 * b
    theme = _theme()
    assert luminance(theme["dark"]["backgroundColor"]) < 60 < 200 < luminance(theme["light"]["backgroundColor"])
    assert luminance(theme["dark"]["textColor"]) > 150 > 100 > luminance(theme["light"]["textColor"])


def test_stylesheet_has_no_fixed_light_surface_colours():
    """Surfaces must come from the active theme; fixed light values made the sidebar stay light in dark mode."""
    source = (ROOT / "ui" / "components.py").read_text(encoding="utf-8")
    css = source[source.index('_CSS = """'):source.index("def apply_theme")]
    assert '[data-testid="stSidebar"]' not in css
    for fixed in ("#f4f6fa", "#eef1f6", "#e8f0fe", "#5b6675", "#fffaf0", "#fff5f5"):
        assert fixed not in css, fixed


def test_theme_preference_is_shared_across_pages():
    """Streamlit keys the saved choice by page URL; the router must mirror it to every page."""
    router = (ROOT / "ui" / "app.py").read_text(encoding="utf-8")
    assert "persist_theme_across_pages(" in router
    components = (ROOT / "ui" / "components.py").read_text(encoding="utf-8")
    assert "stActiveTheme-" in components and "unsafe_allow_javascript=True" in components
