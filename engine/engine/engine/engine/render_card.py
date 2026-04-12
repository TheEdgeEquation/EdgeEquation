from utils.logger import log

def render_card(card_json, output_path):
    log(f"Rendering card to {output_path}")

    # TODO: Replace with real rendering
    with open(output_path, "w") as f:
        f.write("Rendered card placeholder")

    return output_path
