"""
Edge Equation — Brand Voice Validator
Enforces automation safety rule #10.
Blocks any text containing tout language, hype, gambling advice, or emojis.
"""
 
import re
import logging
 
logger = logging.getLogger(__name__)
 
# ── Banned words / phrases ────────────────────────────────────────────────────
 
BANNED_GAMBLING = [
    "bet", "wager", "take", "hammer", "lock", "ride", "sprinkle",
    "ladder", "parlay", "same-game parlay", "sgp", "unit", "units",
    "max play", "best bet", "free pick", "premium pick", "tail", "fade",
    "risk", "stake",
]
 
BANNED_HYPE = [
    "winner", "cash out", "easy money", "guarantee", "no brainer",
    "can't lose", "must play", "love this", "feel good", "vibes",
    "hot streak", "heater", "we're on", "we like", "trust me",
    "let's go", "let's ride",
]
 
BANNED_SLANG = [
    "smash", "nuke", "bomb", "whale", "mega", "banger", "cook",
    "cook up", "cookin", "slap", "slapper",
]
 
BANNED_TONE = [
    "celebrate", "sorry", "apologize", "my bad", "oops",
]
 
# "cash" is banned as hype but "Cash Before Coffee" is our brand name
# So we check for standalone "cash" not as part of "Cash Before Coffee"
BANNED_STANDALONE = ["cash"]
 
ALL_BANNED = BANNED_GAMBLING + BANNED_HYPE + BANNED_SLANG + BANNED_TONE
 
# Emoji pattern
EMOJI_PATTERN = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
 
# Null/placeholder tokens
NULL_TOKENS = [
    "[INSERT", "[PLACEHOLDER", "[TBD", "[TODO", "{{", "}}",
    "XXXXX", "X.X", "undefined", "null", "None",
]
 
 
def check_banned_words(text: str) -> list[str]:
    """Return list of banned words found in text."""
    text_lower = text.lower()
    found = []
 
    for word in ALL_BANNED:
        # Match whole word only
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(word)
 
    # Check standalone "cash" — not part of "Cash Before Coffee"
    for word in BANNED_STANDALONE:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Check if it's part of "cash before coffee"
            start = match.start()
            snippet = text_lower[start:start + 20]
            if "cash before coffee" not in snippet:
                found.append(word + " (standalone)")
                break
 
    return found
 
 
def check_emojis(text: str) -> bool:
    """Return True if text contains emojis."""
    return bool(EMOJI_PATTERN.search(text))
 
 
def check_null_tokens(text: str) -> list[str]:
    """Return list of null/placeholder tokens found."""
    found = []
    for token in NULL_TOKENS:
        if token.lower() in text.lower():
            found.append(token)
    return found
 
 
def check_formatting(text: str) -> list[str]:
    """Check for malformed formatting."""
    issues = []
    if text.count("{") != text.count("}"):
        issues.append("Unclosed braces")
    if text.count("[") != text.count("]"):
        issues.append("Unclosed brackets")
    if len(text.strip()) == 0:
        issues.append("Empty text")
    if len(text) > 280:
        issues.append(f"Exceeds 280 chars ({len(text)})")
    return issues
 
 
def validate(text: str, context: str = "") -> dict:
    """
    Full brand voice validation.
    Returns dict with:
      - approved: bool
      - reasons: list of violation strings
    """
    reasons = []
 
    banned = check_banned_words(text)
    if banned:
        reasons.append(f"Banned words: {', '.join(banned)}")
 
    if check_emojis(text):
        reasons.append("Contains emojis")
 
    null_tokens = check_null_tokens(text)
    if null_tokens:
        reasons.append(f"Null/placeholder tokens: {', '.join(null_tokens)}")
 
    fmt_issues = check_formatting(text)
    if fmt_issues:
        reasons.extend(fmt_issues)
 
    approved = len(reasons) == 0
 
    if not approved:
        logger.warning(
            f"[BRAND VALIDATOR] ABORT — {context or 'unknown'} | "
            f"Violations: {'; '.join(reasons)}"
        )
    else:
        logger.info(f"[BRAND VALIDATOR] APPROVED — {context or 'unknown'}")
 
    return {
        "approved": approved,
        "reasons": reasons,
        "text": text,
        "context": context,
    }
 
 
def validate_or_abort(text: str, context: str = "") -> str | None:
    """
    Validate text. Return text if approved, None if aborted.
    Use this as a gate before every post.
    """
    result = validate(text, context)
    if result["approved"]:
        return text
    return None
 
 
if __name__ == "__main__":
    # Quick test
    tests = [
        ("No feelings. Just facts. | Algorithmic projections. Not picks. Not advice.", "footer"),
        ("Hammer this bet tonight it's a lock!", "bad_post"),
        ("The engine flagged Yankees @ Red Sox as today's highest-leverage matchup.", "GOTD"),
        ("We're on this one trust me let's ride 🔥", "spam_post"),
        ("Edge: 12.4% | Proj Total: 9.9 | Vegas: 9.5", "data_row"),
    ]
 
    for text, ctx in tests:
        result = validate(text, ctx)
        status = "✅ APPROVED" if result["approved"] else "❌ ABORTED"
        print(f"{status} [{ctx}]")
        if not result["approved"]:
            print(f"  Reasons: {result['reasons']}")
 
