import re

_MAX_LOG_STRING_LENGTH = 512

# Regex to check if a string could be Base64-encoded (only contains valid chars and whitespace)
_BASE64_CHARS_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")

# These regexes are used to extract summary counts of added/removed/changed issues from delta report text.
_ADDED_ISSUE_RE = re.compile(r"(?m)^\+\s+Added Issue\s*$")
_REMOVED_ISSUE_RE = re.compile(r"(?m)^-\s+Removed Issue\s*$")
_CHANGED_ISSUE_RE = re.compile(r"(?im)^(?:\*|~)\s+Changed Issue\s*$")

# Regex to strip ANSI escape sequences from strings for safe logging.
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

# Map of control characters and common delimiters to their sanitized replacements for safe logging.
_LOG_SANITIZE_MAP: dict[int, str | None] = {i: None for i in range(32)}
_LOG_SANITIZE_MAP.update(
    {
        ord("\n"): " ",
        ord("\r"): " ",
        ord("\t"): " ",
        127: None,  # DEL
        ord('"'): r"\"",
        ord("'"): r"\'",
        ord("|"): r"\|",
        ord(","): r"\,",
        ord(";"): r"\;",
        ord("="): r"\=",
        ord(":"): r"\:",
    }
)
_LOG_SANITIZE_TRANSLATION = str.maketrans(_LOG_SANITIZE_MAP)

def _sanitize_string(input_str: str) -> str:
    """Sanitize user provided strings by stripping control chars, escaping delimiters, and truncating."""
    if input_str is None:
        return ""
    if not isinstance(input_str, str):
        input_str = str(input_str)
    sanitized = _ANSI_ESCAPE_RE.sub("", input_str)
    sanitized = sanitized.translate(_LOG_SANITIZE_TRANSLATION).strip()
    if len(sanitized) > _MAX_LOG_STRING_LENGTH:
        sanitized = sanitized[: _MAX_LOG_STRING_LENGTH - 3] + "..."
    return sanitized