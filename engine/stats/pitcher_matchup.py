def get_pitcher_matchup_adjustment(profile):
    """
    Adjusts batter expectation based on pitcher handedness and pitch mix.
    """
    pitcher_hand = profile.get("pitcher_hand", "R")
    batter_hand = profile.get("batter_hand", "R")

    # Basic platoon advantage
    if batter_hand == "L" and pitcher_hand == "R":
        platoon = 1.08
    elif batter_hand == "R" and pitcher_hand == "L":
        platoon = 1.05
    else:
        platoon = 0.96

    # Pitch mix adjustments (stub for now)
    pitch_mix_adj = 1.0

    return round(platoon * pitch_mix_adj, 3)
