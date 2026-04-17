from datetime import datetime

PUBLIC_TAGS_DB = "data/public_picks.json"


def _load_public_tags():
    try:
        import json
        with open(PUBLIC_TAGS_DB, "r") as f:
            return json.load(f)
    except:
        return {}


def _save_public_tags(data):
    import json
    with open(PUBLIC_TAGS_DB, "w") as f:
        json.dump(data, f, indent=2)


def tag_public_pick(play, category: str):
    data = _load_public_tags()
    date_key = datetime.now().strftime("%Y-%m-%d")

    if date_key not in data:
        data[date_key] = []

    data[date_key].append({
        "category": category,
        "game_id": play.get("game_id"),
        "prop_label": play.get("prop_label"),
        "side": play.get("side"),
        "edge": play.get("edge"),
        "result": play.get("result"),  # filled in later
    })

    _save_public_tags(data)



def get_public_picks_for_today():
    data = _load_public_tags()
    date_key = datetime.now().strftime("%Y-%m-%d")
    return data.get(date_key, [])
