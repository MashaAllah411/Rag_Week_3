"""
ui/components.py

Shared UI helpers so every page has the same structure and behaves the same way:
  - apply_theme()      one stylesheet for the whole app
  - page_header()      title, one-line purpose, week chips, optional notice
  - call()             run a backend call with a loading spinner and a readable error
  - simulated_notice() / ollama_notice() / info_card()   consistent callouts
  - status_pill() / pill()                               small coloured labels

The UI NEVER imports backend internals; it only talks to the API through ui/api_client.py.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Iterable, Optional, Tuple

import requests
import streamlit as st

_CSS = """
<style>
  /* Theme-aware: every colour is either inherited from the active theme (System / Light / Dark)
     or a tint mixed with the current text colour, so the same rules read well in both modes. */
  .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }
  h1 { letter-spacing: -0.01em; margin-bottom: .1rem; }
  .page-sub { opacity: .72; font-size: 1.02rem; margin: 0 0 .6rem 0; }
  .chip { display: inline-block; padding: 2px 10px; margin: 0 6px 6px 0; border-radius: 999px;
          font-size: .78rem; font-weight: 600;
          background: color-mix(in srgb, #1f6feb 18%, transparent);
          color: color-mix(in srgb, #1f6feb 62%, currentColor); }
  .chip.week { background: color-mix(in srgb, currentColor 11%, transparent); color: inherit; opacity: .85; }
  .chip.ok   { background: color-mix(in srgb, #2ea043 22%, transparent); color: color-mix(in srgb, #2ea043 55%, currentColor); }
  .chip.warn { background: color-mix(in srgb, #d29922 24%, transparent); color: color-mix(in srgb, #d29922 55%, currentColor); }
  .chip.bad  { background: color-mix(in srgb, #f85149 20%, transparent); color: color-mix(in srgb, #f85149 55%, currentColor); }
  .chip.sim  { background: color-mix(in srgb, #d29922 24%, transparent); color: color-mix(in srgb, #d29922 55%, currentColor);
               border: 1px solid color-mix(in srgb, #d29922 45%, transparent); }
  .callout { border-left: 4px solid #1f6feb; background: color-mix(in srgb, #1f6feb 9%, transparent);
             padding: .7rem 1rem; border-radius: 6px; margin: .4rem 0 1rem 0; }
  .callout.sim  { border-left-color: #d29922; background: color-mix(in srgb, #d29922 10%, transparent); }
  .callout.warn { border-left-color: #f85149; background: color-mix(in srgb, #f85149 9%, transparent); }
  [data-testid="stMetricValue"] { font-size: 1.6rem; }
</style>
"""


def apply_theme() -> None:
    """Inject the shared stylesheet. Called once from ui/app.py (the navigation router)."""
    st.markdown(_CSS, unsafe_allow_html=True)


def pill(text: str, tone: str = "") -> str:
    """HTML for a small coloured label. tone: '' | week | ok | warn | bad | sim."""
    return f'<span class="chip {tone}">{text}</span>'


def status_pill(ok: bool, yes: str = "Active", no: str = "Inactive") -> str:
    return pill(yes if ok else no, "ok" if ok else "bad")


def page_header(title: str, icon: str, subtitle: str, weeks: Iterable[str] = (), notice: Optional[str] = None) -> None:
    """Consistent page top: title, purpose, the weeks it covers, and an optional notice."""
    st.title(f"{icon} {title}")
    st.markdown(f'<p class="page-sub">{subtitle}</p>', unsafe_allow_html=True)
    chips = "".join(pill(f"Week {w}", "week") for w in weeks)
    if chips:
        st.markdown(chips, unsafe_allow_html=True)
    if notice:
        st.markdown(f'<div class="callout">{notice}</div>', unsafe_allow_html=True)


def info_card(text: str, tone: str = "") -> None:
    """tone: '' (info) | sim (simulated data) | warn."""
    st.markdown(f'<div class="callout {tone}">{text}</div>', unsafe_allow_html=True)


def simulated_notice(what: str) -> None:
    """Say plainly that a result comes from a simulation, not live measurement."""
    info_card(f"<b>Simulation.</b> {what}", "sim")


def ollama_notice(what: str = "This needs the local LLM") -> None:
    info_card(f"<b>{what}.</b> Ollama is not reachable. Start it with <code>ollama serve</code> and "
              "<code>ollama pull llama3.2</code>, then try again. Retrieval and citations still work without it.", "warn")


def friendly_error(exc: BaseException) -> str:
    """Turn an exception from the API client into a message a non-developer can act on."""
    if isinstance(exc, requests.ConnectionError):
        return "Can't reach the backend. Start the app with `python run.py` and refresh this page."
    if isinstance(exc, requests.Timeout):
        return "The request took too long. It may still be running; try again, or use a smaller input."
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        detail: Any = ""
        try:
            detail = exc.response.json().get("detail", "")
        except Exception:
            detail = exc.response.text[:300]
        if isinstance(detail, list):
            detail = "; ".join(str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail)
        return f"The server said ({exc.response.status_code}): {detail or exc.response.reason}"
    return f"{type(exc).__name__}: {exc}"


def call(fn: Callable[..., Any], *args: Any, spinner: str = "Working...", show_error: bool = True,
         **kwargs: Any) -> Tuple[bool, Any]:
    """Run an API call with a loading state. Returns (ok, data); on failure shows a readable error.

    ok, data = call(api.list_documents, spinner="Loading documents...")
    if ok: ...
    """
    try:
        with st.spinner(spinner):
            return True, fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 - every failure becomes a readable message
        if show_error:
            st.error(friendly_error(exc))
        return False, None


def kv_table(rows: dict) -> None:
    """Two-column key/value table without index noise."""
    st.dataframe([{"Setting": k, "Value": str(v)} for k, v in rows.items()], hide_index=True, width="stretch")


# Streamlit stores the System / Light / Dark choice in localStorage under a key that includes the
# page URL ("stActiveTheme-/documents-v2"). On its own, a choice made on one page is therefore
# forgotten when a different page is refreshed. This small static script (no user input) mirrors
# every explicit theme change to the keys of all pages, so the preference survives a refresh anywhere.
# It deliberately does not reconcile at load time: Streamlit writes a default key for any page the
# moment it loads, so a stored value cannot be told apart from a deliberate choice. A preference saved
# before this was added is simply picked once more, then it persists on every page.
_THEME_SYNC_JS = """
<script>
(function () {
  if (window.__ragThemeSync) return;
  window.__ragThemeSync = true;
  var PATHS = __PATHS__;
  var RE = /^stActiveTheme-.*-(v\\d+)$/;
  var ls = window.localStorage;
  var origSet = Storage.prototype.setItem;

  function mirror(version, value) {
    PATHS.forEach(function (p) {
      var k = 'stActiveTheme-' + p + '-' + version;
      if (ls.getItem(k) !== value) origSet.call(ls, k, value);
    });
  }

  Storage.prototype.setItem = function (k, v) {
    origSet.apply(this, arguments);
    if (this === ls && RE.test(k)) mirror(RE.exec(k)[1], String(v));
  };

})();
</script>
"""


def persist_theme_across_pages(page_paths: Iterable[str]) -> None:
    """Make the System / Light / Dark preference survive a refresh on every page (call once from the router)."""
    paths = ["/" + p.strip("/") if p.strip("/") else "/" for p in page_paths]
    st.html(_THEME_SYNC_JS.replace("__PATHS__", json.dumps(sorted(set(paths)))), unsafe_allow_javascript=True)
