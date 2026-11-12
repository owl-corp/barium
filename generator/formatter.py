import html
import re
import uuid

# Discord markdown patterns
CODE_BLOCK_RE = re.compile(r"```(?:([a-zA-Z0-9_+-]+)?\n)?([\s\S]*?)```")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")
RAW_URL_RE = re.compile(r'https?://[^\s<>"]+')

BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
UNDERLINE_RE = re.compile(r"__([^_]+)__")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")
STRIKE_RE = re.compile(r"~~([^~]+)~~")
SPOILER_RE = re.compile(r"\|\|([^|]+)\|\|")


def _trim_trailing_url_punctuation(url: str):
    """Separate trailing punctuation not belonging to the URL, handling balanced parentheses."""
    trailing = ""
    while url and url[-1] in ").,;:!?'\"":
        if url[-1] == ")" and url.count("(") >= url.count(")"):
            # If open and closed parens in URL are balanced or excess opens, stop stripping
            break
        trailing = url[-1] + trailing
        url = url[:-1]
    return url, trailing


def format_discord_content(text: str) -> str:
    """Format Discord markdown, Markdown links, and auto-link plain URLs cleanly."""
    if not text:
        return ""

    tokens = {}
    uid_hex = uuid.uuid4().hex[:12]

    def make_token(val: str) -> str:
        tid = f"\x00{uid_hex}_{len(tokens)}\x00"
        tokens[tid] = val
        return tid

    # 1. Protect code blocks
    def code_block_sub(match):
        lang = match.group(1) or ""
        code = html.escape(match.group(2).rstrip("\n"))
        return make_token(f'<pre><code class="code-block {lang}">{code}</code></pre>')

    escaped = CODE_BLOCK_RE.sub(code_block_sub, text)

    # 2. Protect inline code
    def inline_code_sub(match):
        code = html.escape(match.group(1))
        return make_token(f'<code class="inline-code">{code}</code>')

    escaped = INLINE_CODE_RE.sub(inline_code_sub, escaped)

    # 3. Protect Markdown links: [Label](https://url)
    def md_link_sub(match):
        label = html.escape(match.group(1))
        url = match.group(2)
        url_clean, trailing = _trim_trailing_url_punctuation(url)
        safe_url = html.escape(url_clean, quote=True)
        return make_token(
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{label}</a>'
        ) + html.escape(trailing)

    escaped = MD_LINK_RE.sub(md_link_sub, escaped)

    # 4. Protect and autolink raw URLs
    def raw_url_sub(match):
        raw = match.group(0)
        url_clean, trailing = _trim_trailing_url_punctuation(raw)
        safe_url = html.escape(url_clean, quote=True)
        displayed_url = html.escape(url_clean)
        return make_token(
            f'<a href="{safe_url}" target="_blank" rel="noopener noreferrer">{displayed_url}</a>'
        ) + html.escape(trailing)

    # Escape HTML of surrounding non-token text first
    escaped = html.escape(escaped)

    # Match raw URLs
    escaped = RAW_URL_RE.sub(raw_url_sub, escaped)

    # 5. Discord inline formatting
    escaped = BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = UNDERLINE_RE.sub(r"<u>\1</u>", escaped)
    escaped = ITALIC_RE.sub(r"<em>\1</em>", escaped)
    escaped = STRIKE_RE.sub(r"<del>\1</del>", escaped)
    escaped = SPOILER_RE.sub(r'<span class="spoiler">\1</span>', escaped)

    # 6. Newlines to <br>
    escaped = escaped.replace("\n", "<br>")

    # 7. Restore protected tokens
    for tid, val in tokens.items():
        escaped = escaped.replace(tid, val)

    return escaped


def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


KEY_RE = re.compile(r"[A-Za-z0-9_-]+")


def get_thread_path(key: str) -> str:
    """Output path for a log; served as /logs/<key> by Netlify's pretty URLs."""
    if not KEY_RE.fullmatch(key):
        raise ValueError(f"Unsafe log key: {key!r}")
    return f"logs/{key}.html"
