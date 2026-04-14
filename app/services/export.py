import csv
import io
import json


_CSV_FIELDS = [
    "id", "original_filename", "uploaded_at", "designer",
    "garment_type", "style", "material", "color_palette",
    "pattern", "season", "occasion", "consumer_profile",
    "trend_notes", "continent", "country", "city", "year", "month",
    "description", "user_tags", "user_notes",
]


def to_csv(garments) -> str:
    """Serialize a list of Garment ORM objects to a CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()

    for g in garments:
        row = {}
        for field in _CSV_FIELDS:
            val = getattr(g, field, "")
            if field in ("color_palette", "user_tags"):
                try:
                    parsed = json.loads(val or "[]")
                    val = ", ".join(str(v) for v in parsed)
                except (json.JSONDecodeError, TypeError):
                    val = val or ""
            elif val is None:
                val = ""
            row[field] = val
        writer.writerow(row)

    return output.getvalue()
