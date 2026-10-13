#!/usr/bin/env python3
"""Small, illustrative CYP450 role catalog and command-line CSV lookup.

Record tiers are legacy tags, NOT validated pairwise DDI risk classifications.
"""
import argparse
import csv
import re
import sys

CYP_DRUG_DATABASE = [
    ("Ketoconazole - strong CYP3A4 inhibitor", "ketoconazole", "inhibitor", "major"),
    ("Itraconazole - strong CYP3A4 inhibitor", "itraconazole", "inhibitor", "major"),
    ("Clarithromycin - strong CYP3A4 inhibitor", "clarithromycin", "inhibitor", "major"),
    ("Ritonavir - strong CYP3A4 inhibitor", "ritonavir", "inhibitor", "major"),
    ("Simvastatin - CYP3A4 substrate", "simvastatin", "substrate", "major"),
    ("Midazolam - CYP3A4 substrate", "midazolam", "substrate", "moderate"),
    ("Cyclosporine - CYP3A4 substrate", "cyclosporine", "substrate", "major"),
    ("Carbamazepine - CYP3A4 inducer", "carbamazepine", "inducer", "major"),
    ("Phenytoin - CYP3A4 inducer", "phenytoin", "inducer", "major"),
    ("Rifampin - CYP3A4 inducer", "rifampin", "inducer", "major"),
    ("St. John's Wort - CYP3A4 inducer", "st. john", "inducer", "major"),
    ("Fluoxetine - strong CYP2D6 inhibitor", "fluoxetine", "inhibitor", "major"),
    ("Paroxetine - strong CYP2D6 inhibitor", "paroxetine", "inhibitor", "major"),
    ("Quinidine - strong CYP2D6 inhibitor", "quinidine", "inhibitor", "major"),
    ("Codeine - CYP2D6 substrate (prodrug)", "codeine", "substrate", "major"),
    ("Tamoxifen - CYP2D6 substrate (prodrug)", "tamoxifen", "substrate", "major"),
    ("Metoprolol - CYP2D6 substrate", "metoprolol", "substrate", "moderate"),
    ("Omeprazole - CYP2C19 inhibitor", "omeprazole", "inhibitor", "moderate"),
    ("Clopidogrel - CYP2C19 substrate (prodrug)", "clopidogrel", "substrate", "major"),
    ("Warfarin - CYP2C9 substrate", "warfarin", "substrate", "major"),
    ("Fluconazole - CYP2C9 inhibitor", "fluconazole", "inhibitor", "moderate"),
    ("Fluvoxamine - strong CYP1A2 inhibitor", "fluvoxamine", "inhibitor", "major"),
    ("Caffeine - CYP1A2 substrate", "caffeine", "substrate", "minor"),
    ("Efavirenz - CYP2B6 substrate", "efavirenz", "substrate", "moderate"),
    ("Bupropion - CYP2B6 substrate", "bupropion", "substrate", "moderate"),
]

SEVERITY_SCORE = {"major": 3, "moderate": 2, "minor": 1}
OUTPUT_FIELDS = ("top_hit", "lookup_score", "interaction_type", "severity")


def lookup(query, extra=None):
    """Search catalog by drug key and label tokens; ranking is text relevance."""
    q = str(query or "").casefold().strip()
    if not q:
        return {"query": query, "top_hit": "no match", "score": 0,
                "interaction_type": None, "severity": None, "all": [], "extra": extra}
    query_terms = set(q.split())
    scored = []
    for label, key, role, tier in CYP_DRUG_DATABASE:
        # Match drug names as phrases, not inside unrelated longer words.
        name_match = re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", q) is not None
        overlap = len(query_terms.intersection(label.casefold().split()))
        score = (10 if name_match else 0) + overlap * 2
        if score:
            scored.append((score + SEVERITY_SCORE[tier], label, role, tier))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[0] if scored else (0, "no match", None, None)
    return {"query": query, "top_hit": top[1], "score": top[0],
            "interaction_type": top[2], "severity": top[3], "all": scored[:5],
            "extra": extra}


def process_csv(inp, out):
    """Process UTF-8 CSV; reject invalid headers and malformed rows."""
    try:
        with open(inp, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f, restkey="__extra_columns__", strict=True)
            fields = reader.fieldnames
            if not fields or not any(name and name.strip() for name in fields):
                raise ValueError("CSV is empty or has no headers")
            if any(not name or not name.strip() for name in fields):
                raise ValueError("CSV contains a blank column heading")
            if len(set(name.casefold() for name in fields)) != len(fields):
                raise ValueError("CSV headers must be unique")
            rows = list(reader)
    except FileNotFoundError as exc:
        raise FileNotFoundError("Input file not found: '" + str(inp) + "'") from exc
    except csv.Error as exc:
        raise ValueError("Malformed CSV: " + str(exc)) from exc

    qcol = fields[0]
    for candidate in ("query", "test", "drug", "code", "variant", "hla", "lab", "name"):
        match = next((name for name in fields if name.casefold() == candidate), None)
        if match is not None:
            qcol = match
            break

    results = []
    for row_number, row in enumerate(rows, start=2):
        if "__extra_columns__" in row or any(row[name] is None for name in fields):
            raise ValueError("CSV row " + str(row_number) + " has the wrong number of columns")
        match = lookup(row[qcol])
        merged = dict(row)
        merged.update(top_hit=match["top_hit"], lookup_score=match["score"],
                      interaction_type=match["interaction_type"], severity=match["severity"])
        results.append(merged)

    output_fields = list(dict.fromkeys(list(fields) + list(OUTPUT_FIELDS)))
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(results)
    return results


def build_parser():
    parser = argparse.ArgumentParser(prog="cyp_checker", description="CYP role catalog (not clinical DDI decision support)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    single = sub.add_parser("single")
    single.add_argument("query", nargs="?", default="simvastatin")
    single.add_argument("--query", dest="q2")
    batch = sub.add_parser("batch")
    batch.add_argument("--input", required=True)
    batch.add_argument("--output", required=True)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "single":
        print(lookup(args.q2 or args.query))
        return 0
    if args.cmd == "batch":
        try:
            results = process_csv(args.input, args.output)
        except (FileNotFoundError, ValueError, OSError) as exc:
            print("Error: " + str(exc), file=sys.stderr)
            return 1
        print("Processed " + str(len(results)) + " -> " + args.output)
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
