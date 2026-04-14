"""
Per-attribute accuracy metrics for garment classification evaluation.
"""

from typing import Any


_SCORED_FIELDS = [
    "garment_type",
    "style",
    "material",
    "pattern",
    "season",
    "occasion",
    "consumer_profile",
    "continent",
    "country",
    "city",
]


def exact_match(predicted: Any, expected: Any) -> bool:
    """
    Case-insensitive exact match.
    Both None/null values count as a match (model correctly said 'unknown').
    """
    if predicted is None and expected is None:
        return True
    if predicted is None or expected is None:
        return False
    return str(predicted).strip().lower() == str(expected).strip().lower()


def compute_per_field_accuracy(results: list[dict]) -> dict:
    """
    Given a list of {'expected': {...}, 'predicted': {...}} dicts,
    return per-field accuracy as a fraction and as a percentage.
    """
    counts = {f: {"correct": 0, "total": 0} for f in _SCORED_FIELDS}

    for item in results:
        exp = item.get("expected", {})
        pred = item.get("predicted", {})
        for field in _SCORED_FIELDS:
            if field not in exp:
                continue  # skip unlabeled fields
            counts[field]["total"] += 1
            if exact_match(pred.get(field), exp.get(field)):
                counts[field]["correct"] += 1

    accuracy = {}
    for field, c in counts.items():
        if c["total"] == 0:
            accuracy[field] = None
        else:
            accuracy[field] = round(c["correct"] / c["total"], 3)

    return accuracy


def compute_macro_average(per_field: dict) -> float:
    """Macro-average accuracy across all scored fields that have labels."""
    scores = [v for v in per_field.values() if v is not None]
    return round(sum(scores) / len(scores), 3) if scores else 0.0


def format_report(per_field: dict, macro: float, n_images: int) -> str:
    lines = [
        f"Evaluation Report — {n_images} images",
        "=" * 44,
        f"{'Field':<22} {'Accuracy':>8}",
        "-" * 44,
    ]
    for field, score in sorted(per_field.items()):
        bar = ""
        if score is not None:
            filled = int(score * 20)
            bar = "█" * filled + "░" * (20 - filled)
            lines.append(f"  {field:<20} {score:>6.1%}  {bar}")
        else:
            lines.append(f"  {field:<20} {'N/A':>6}")
    lines.append("-" * 44)
    lines.append(f"  {'Macro average':<20} {macro:>6.1%}")
    return "\n".join(lines)
