from datetime import datetime


def build_daily_brief(
    graphic_prompt_text: str,
    graphic_picks_text: str,
    engine_accuracy_text: str,
    public_accuracy_text: str,
    personal_parlay_text: str,
    personal_top10_text: str,
    prop_top10_text: str,
    public_card_text: str,
) -> str:
    date_str = datetime.now().strftime("%B %-d, %Y")

    sections = []

    sections.append(
        "\n".join([
            "EDGE EQUATION — DAILY INTELLIGENCE BRIEF",
            date_str,
            "",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "1. GRAPHIC PROMPT",
            "=" * 60,
            graphic_prompt_text.strip() or "[No graphic prompt generated]",
            "",
            "PICKS INSIDE THE GRAPHIC:",
            "",
            graphic_picks_text.strip() or "[No picks selected for graphic]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "2. ENGINE ACCURACY (INTERNAL)",
            "=" * 60,
            engine_accuracy_text.strip() or "[No engine accuracy available]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "3. PUBLIC ACCURACY (POSTED PICKS ONLY)",
            "=" * 60,
            public_accuracy_text.strip() or "[No public accuracy available]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "4. PERSONAL PARLAY",
            "=" * 60,
            personal_parlay_text.strip() or "[No personal parlay built]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "5. PERSONAL TOP 10 GRADED PICKS",
            "=" * 60,
            personal_top10_text.strip() or "[No personal top 10 available]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "6. TOP 10 PROPS (WITH LETTER GRADES)",
            "=" * 60,
            prop_top10_text.strip() or "[No top 10 props available]",
        ])
    )

    sections.append(
        "\n".join([
            "=" * 60,
            "7. FULL PUBLIC CARD (ALL PICKS BEING POSTED TODAY)",
            "=" * 60,
            public_card_text.strip() or "[No public card built]",
        ])
    )

    return "\n\n".join(sections)
