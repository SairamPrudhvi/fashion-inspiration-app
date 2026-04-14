#!/usr/bin/env python3
"""
Garment classification evaluation script.

Usage
-----
  python eval/run_eval.py \
      --images-dir eval/sample_images/ \
      --labels-file eval/labels_template.jsonl \
      --output-json eval/results.json

Each line in the labels file must be valid JSON with this shape:

  {
    "image": "filename.jpg",
    "expected": {
      "garment_type": "dress",
      "style": "casual",
      "material": "cotton",
      "pattern": "floral",
      "season": "spring/summer",
      "occasion": "casual everyday",
      "consumer_profile": "young urban professional",
      "continent": "Europe",
      "country": "France",
      "city": "Paris"
    }
  }

Fields you don't want to evaluate can be omitted from 'expected'.

Getting test images
-------------------
Pexels (https://www.pexels.com/search/fashion/) provides free images.
Download 50-100 images into eval/sample_images/, name each one to match
the "image" field in your labels JSONL, then run this script.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow running from project root: python eval/run_eval.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.classifier import classify_image
from eval.metrics import compute_macro_average, compute_per_field_accuracy, format_report


def load_labels(labels_file: Path) -> list[dict]:
    records = []
    with open(labels_file) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  Warning: skipping line {i} — {e}")
    return records


def run_evaluation(images_dir: Path, labels_file: Path, output_json: Path | None):
    print(f"Loading labels from {labels_file}…")
    records = load_labels(labels_file)
    print(f"  {len(records)} labelled entries found.")

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "\nWarning: ANTHROPIC_API_KEY is not set. "
            "Predictions will use the mock classifier — results are not meaningful."
        )

    results = []
    for i, record in enumerate(records, 1):
        image_path = images_dir / record["image"]
        if not image_path.exists():
            print(f"  [{i}/{len(records)}] SKIP  {record['image']} — file not found")
            continue

        print(f"  [{i}/{len(records)}] Classifying {record['image']}…", end=" ", flush=True)
        try:
            predicted = classify_image(str(image_path))
            print("done")
        except Exception as e:
            print(f"ERROR: {e}")
            predicted = {}

        results.append({
            "image": record["image"],
            "expected": record["expected"],
            "predicted": predicted,
        })

    if not results:
        print("\nNo results to report — check your images directory and labels file.")
        return

    per_field = compute_per_field_accuracy(results)
    macro = compute_macro_average(per_field)

    print()
    print(format_report(per_field, macro, len(results)))

    # Attach per-image detail to output
    output = {
        "n_images": len(results),
        "macro_accuracy": macro,
        "per_field_accuracy": per_field,
        "items": results,
    }

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nDetailed results written to {output_json}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate garment classifier accuracy.")
    parser.add_argument("--images-dir",  type=Path, default=Path("eval/sample_images"))
    parser.add_argument("--labels-file", type=Path, default=Path("eval/labels_template.jsonl"))
    parser.add_argument("--output-json", type=Path, default=Path("eval/results.json"))
    args = parser.parse_args()

    if not args.labels_file.exists():
        print(f"Labels file not found: {args.labels_file}")
        sys.exit(1)

    run_evaluation(args.images_dir, args.labels_file, args.output_json)


if __name__ == "__main__":
    main()
