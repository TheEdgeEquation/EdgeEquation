# core/formatting.py
from datetime import datetime

def format_insight_block(label: str, insight: dict) -> str:
    """
    label: 'MLB Insight' or 'KBO/NPB Insight'
    insight: {
      'timestamp', 'league', 'entity', 'prop_or_angle',
      'key_metric', 'context', 'model_signal',
      'trend', 'matchup_delta', 'historical_comp',
      'edge_summary'
    }
    """
    date_str = datetime.fromisoformat(insight["timestamp"].replace("Z", "")).strftime("%Y-%m-%d")

    lines = [
        f"📊 {label} — {date_str}",
        "",
        f"• Key Metric: {insight['key_metric']}",
        f"• Context: {insight['context']}",
        f"• Model Signal: {insight['model_signal']}",
        f"• Trend: {insight['trend']}",
        f"• Matchup Delta: {insight['matchup_delta']}",
        f"• Historical Comparison: {insight['historical_comp']}",
        f"• Edge Summary: {insight['edge_summary']}",
        "",
        "#AnalyticsNotFeelings",
    ]
    return "\n".join(lines)
