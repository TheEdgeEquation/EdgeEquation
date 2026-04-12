from utils.math_models import compute_confidence, compute_grade
from utils.logger import log

def grade_props(props):
    graded = []

    for p in props:
        confidence = compute_confidence(p)
        letter, score = compute_grade(confidence)

        p["confidence"] = confidence
        p["grade_letter"] = letter
        p["grade_score"] = score

        graded.append(p)

    log(f"Graded {len(graded)} props")
    return graded
