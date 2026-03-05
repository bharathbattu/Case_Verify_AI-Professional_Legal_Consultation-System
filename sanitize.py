"""
HTML sanitization utilities for Streamlit ``unsafe_allow_html=True`` blocks.

S-07 / Hardening Plan: Every dynamic value rendered inside raw HTML must be
escaped to prevent reflected XSS.  Use ``esc()`` for all user-supplied or
AI-generated strings that are interpolated into HTML templates.
"""

import html


def esc(value: object) -> str:
    """
    HTML-escape *value* for safe embedding inside ``unsafe_allow_html`` blocks.

    Converts ``<``, ``>``, ``&``, ``"``, ``'`` to their HTML entities.
    Handles ``None`` gracefully (returns empty string).

    >>> esc('<script>alert(1)</script>')
    '&lt;script&gt;alert(1)&lt;/script&gt;'
    >>> esc(None)
    ''
    """
    if value is None:
        return ""
    return html.escape(str(value), quote=True)
