def get_full_batter_profile(player, team, opponent):
    # Safe baseline profile
    return {
        "hits_per_game": 1.0,
        "tb_per_game": 2.0,
        "hr_per_game": 0.25,
        "rbi_per_game": 0.8,
        "runs_per_game": 0.8,
        "stat_per_game": 1.0,
        "pitcher_hand": "R",
        "batter_hand": "R",
    }
