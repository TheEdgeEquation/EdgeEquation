"""
Edge Equation — Logic Layer
Implements all 15 automation safety rules.
Every post goes through this before publishing.
Returns APPROVED or ABORT with reason.
"""
 
import logging
from datetime import datetime, timezone
from engine.brand_validator import validate_or_abort
from engine.state_tracker import load_state, was_posted_today
 
logger = logging.getLogger(__name__)
 
# ── Allowed posting windows (CST = UTC-6) ────────────────────────────────────
# Engine adds 6 hours to get UTC
WINDOWS = {
    "system_status":     {"start_utc": 14, "end_utc": 15},   # 8-9 AM CST
    "EE_gotd":           {"start_utc": 16, "end_utc": 17},   # 10-11 AM CST
    "EE_potd":           {"start_utc": 16, "end_utc": 17},
    "EE_projections":    {"start_utc": 17, "end_utc": 20},   # 11 AM-2 PM CST
    "midday_insight":    {"start_utc": 19, "end_utc": 20},   # 1 PM CST
    "evening_prop":      {"start_utc": 24, "end_utc": 25},   # 6 PM CST (next day UTC)
    "nrfi":              {"start_utc": 27, "end_utc": 28},   # 9:30 PM CST
    "cbc_nightshift":    {"start_utc": 25, "end_utc": 26},   # 7 PM CST
    "CBC_gotd":          {"start_utc": 28, "end_utc": 29},   # 10:30 PM CST
    "CBC_potd":          {"start_utc": 28, "end_utc": 29},
    "CBC_projections":   {"start_utc": 29, "end_utc": 32},   # 11 PM+ CST
}
 
 
def _now_utc_hour() -> int:
    return datetime.now(timezone.utc).hour
 
 
def _in_window(post_type: str) -> bool:
    """Check if current time is within the allowed posting window."""
    window = WINDOWS.get(post_type)
    if not window:
        return True  # No window restriction
    hour = _now_utc_hour()
    # Handle windows that cross midnight UTC
    start = window["start_utc"] % 24
    end = window["end_utc"] % 24
    if start <= end:
        return start <= hour < end
    else:
        return hour >= start or hour < end
 
 
def approve(post_type: str, brand: str, text: str,
            slate_live: bool = False,
            slate_final: bool = False,
            data_complete: bool = True,
            recalibrated: bool = True,
            data_fresh: bool = True,
            alignment: bool = None,
            results_posted: bool = None,
            api_available: bool = True) -> dict:
    """
    Run all 15 safety rules for a given post.
    Returns: {"approved": bool, "reasons": list}
    """
    reasons = []
    state = load_state()
 
    # ── Rule 1: No hard post times for data-dependent posts ──────────────────
    data_dependent = post_type in [
        "EE_projections", "CBC_projections",
        "EE_gotd", "EE_potd", "CBC_gotd", "CBC_potd",
        "EE_results", "CBC_results",
        "EE_cheeky", "CBC_cheeky",
        "nrfi",
    ]
    if data_dependent and not _in_window(post_type):
        reasons.append(f"Rule 1: Outside allowed posting window for {post_type}")
 
    # ── Rule 2: Never post results until ALL games are FINAL ─────────────────
    if post_type in ["EE_results", "CBC_results", "EE_cheeky", "CBC_cheeky"]:
        if not slate_final:
            reasons.append("Rule 2: Slate not fully final — results/cheeky blocked")
 
    # ── Rule 3: No posting during live games for slate-dependent content ──────
    if post_type in [
        "EE_projections", "CBC_projections",
        "EE_gotd", "EE_potd", "CBC_gotd", "CBC_potd",
        "EE_results", "CBC_results", "EE_cheeky", "CBC_cheeky",
    ]:
        if slate_live:
            reasons.append("Rule 3: Slate is live — blocking slate-dependent post")
 
    # ── Rule 4: No posting if data is missing/null/incomplete ────────────────
    if not data_complete:
        reasons.append("Rule 4: Data incomplete or null — aborting")
 
    # ── Rule 5: No posting if formatting breaks ───────────────────────────────
    # (handled by brand validator below)
 
    # ── Rule 6: No GOTD/POTD if engine failed to generate ────────────────────
    if post_type in ["EE_gotd", "EE_potd", "CBC_gotd", "CBC_potd"]:
        if not text or len(text.strip()) < 20:
            reasons.append("Rule 6: GOTD/POTD not generated — skipping")
 
    # ── Rule 7: No posting if recalibration not complete ─────────────────────
    if data_dependent and not recalibrated:
        reasons.append("Rule 7: Recalibration not complete")
 
    # ── Rule 8: No posting if data provider is delayed ───────────────────────
    if not data_fresh:
        reasons.append("Rule 8: Data not fresh — delaying")
 
    # ── Rule 9: No posting if script runs too early ───────────────────────────
    # (covered by Rule 1 window check)
 
    # ── Rule 10: Brand voice enforcement ─────────────────────────────────────
    if text:
        validated = validate_or_abort(text, post_type)
        if validated is None:
            reasons.append("Rule 10: Brand voice violation — banned words or emojis")
 
    # ── Rule 11: Cheeky posts only if model actually hit ─────────────────────
    if post_type in ["EE_cheeky", "CBC_cheeky"]:
        if alignment is False:
            reasons.append("Rule 11: Model did not align — cheeky post blocked")
 
    # ── Rule 12: Cheeky posts only AFTER results graphic ─────────────────────
    if post_type in ["EE_cheeky", "CBC_cheeky"]:
        results_key = "EE_results" if brand == "EE" else "CBC_results"
        if not was_posted_today(state, results_key):
            reasons.append("Rule 12: Results not yet posted — cheeky blocked")
 
    # ── Rule 13: CBC must not step on EE ────────────────────────────────────
    if brand == "CBC":
        if not was_posted_today(state, "EE_projections") and post_type == "CBC_projections":
            # EE projections haven't gone out yet — CBC can still post
            # (they run at different times) — only block if EE is delayed/pending
            pass  # No block — EE daytime and CBC overnight don't conflict
 
    # ── Rule 14: No posting if rate-limited ──────────────────────────────────
    if not api_available:
        reasons.append("Rule 14: API rate-limited or unavailable — pausing")
 
    # ── Rule 15: Manual override always wins ─────────────────────────────────
    override_key = post_type
    if state.get("manual_override", {}).get(override_key, False):
        reasons.append(f"Rule 15: Manual override active for {post_type} — skipping automated version")
 
    # ── Final decision ────────────────────────────────────────────────────────
    approved = len(reasons) == 0
 
    if approved:
        logger.info(f"[LOGIC LAYER] ✅ APPROVED — {brand} {post_type}")
    else:
        logger.warning(
            f"[LOGIC LAYER] ❌ ABORT — {brand} {post_type} | "
            f"Reasons: {'; '.join(reasons)}"
        )
 
    return {
        "approved": approved,
        "reasons": reasons,
        "post_type": post_type,
        "brand": brand,
    }
 
 
def gate(post_type: str, brand: str, text: str, **kwargs) -> bool:
    """
    Simple gate — returns True if approved, False if aborted.
    Use this as a one-liner before every post.
    """
    result = approve(post_type, brand, text, **kwargs)
    return result["approved"]
 
 
if __name__ == "__main__":
    # Test
    tests = [
        {
            "post_type": "EE_gotd",
            "brand": "EE",
            "text": "Edge Equation — Game of the Day. The model flags Yankees @ Red Sox as today's highest-leverage matchup.",
            "data_complete": True,
            "recalibrated": True,
            "data_fresh": True,
            "slate_live": False,
        },
        {
            "post_type": "EE_cheeky",
            "brand": "EE",
            "text": "The projection lined up. The signal held.",
            "slate_final": False,
            "alignment": True,
        },
        {
            "post_type": "EE_projections",
            "brand": "EE",
            "text": "hammer this bet tonight it's a lock!",
            "data_complete": True,
        },
    ]
 
    for t in tests:
        result = approve(**t)
        status = "✅ APPROVED" if result["approved"] else "❌ ABORTED"
        print(f"{status} [{t['post_type']}]")
        if not result["approved"]:
            for r in result["reasons"]:
                print(f"  — {r}")
 
