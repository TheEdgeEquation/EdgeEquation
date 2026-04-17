import logging
from engine.results_loader import get_todays_graded_plays
from engine.results_checker import (
    check_mlb_results,
    check_pitcher_results,
)
from engine.content_generators import (
    generate_called_it_post,
    generate_daily_accuracy_post,
)
from engine.global_accuracy import (
    evaluate_global_results,
    generate_global_accuracy_post,
)
from engine.social import post_tweet

logger = logging.getLogger(__name__)

def run_results():
    logger.info("MODE: results")

    todays_plays = get_todays_graded_plays() or []

    mlb_game_projs = [
        p for p in todays_plays
        if p.get("sport") == "baseball_mlb"
        and p.get("prop_label") not in ("K", "NRFI", "YRFI")
    ]

    pitcher_projs = [
        p for p in todays_plays
        if p.get("prop_label") == "K"
    ]

    game_hits, game_misses = check_mlb_results(mlb_game_projs)
    pitcher_hits, pitcher_misses = check_pitcher_results(pitcher_projs)

    # Called it posts
    called_it_pitcher = generate_called_it_post(pitcher_hits, "pitcher")
    if called_it_pitcher:
        post_tweet(called_it_pitcher)

    called_it_game = generate_called_it_post(game_hits, "game")
    if called_it_game:
        post_tweet(called_it_game)

    # Daily accuracy
    accuracy_post = generate_daily_accuracy_post(
        game_hits, game_misses,
        pitcher_hits, pitcher_misses
    )
    if accuracy_post:
        post_tweet(accuracy_post)

    # Global accuracy
    global_plays = [
        p for p in todays_plays
        if p.get("sport") in ("kbo", "npb", "soccer_epl", "soccer_ucl")
    ]

    global_stats = evaluate_global_results(global_plays)
    global_accuracy_post = generate_global_accuracy_post(global_stats)
    if global_accuracy_post:
        post_tweet(global_accuracy_post)

    logger.info("Results posted")
