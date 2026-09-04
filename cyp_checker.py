#!/usr/bin/env python3
"""
CYP Drug Interaction Checker
CYP450 substrate/inhibitor/inducer interaction checker with severity tiers.
Stdlib parser / mapper with batch CSV and single lookup.
"""
import argparse
import csv
import sys


# CYP450 drug interaction database
# Format: (display_name, search_key, interaction_type, severity)
CYP_DRUG_DATABASE = [
    # CYP3A4 interactions
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
    # CYP2D6 interactions
    ("Fluoxetine - strong CYP2D6 inhibitor", "fluoxetine", "inhibitor", "major"),
    ("Paroxetine - strong CYP2D6 inhibitor", "paroxetine", "inhibitor", "major"),
    ("Quinidine - strong CYP2D6 inhibitor", "quinidine", "inhibitor", "major"),
    ("Codeine - CYP2D6 substrate (prodrug)", "codeine", "substrate", "major"),
    ("Tamoxifen - CYP2D6 substrate (prodrug)", "tamoxifen", "substrate", "major"),
    ("Metoprolol - CYP2D6 substrate", "metoprolol", "substrate", "moderate"),
    # CYP2C19 interactions
    ("Omeprazole - CYP2C19 inhibitor", "omeprazole", "inhibitor", "moderate"),
    ("Clopidogrel - CYP2C19 substrate (prodrug)", "clopidogrel", "substrate", "major"),
    # CYP2C9 interactions
    ("Warfarin - CYP2C9 substrate", "warfarin", "substrate", "major"),
    ("Fluconazole - CYP2C9 inhibitor", "fluconazole", "inhibitor", "moderate"),
    # CYP1A2 interactions
    ("Fluvoxamine - strong CYP1A2 inhibitor", "fluvoxamine", "inhibitor", "major"),
    ("Caffeine - CYP1A2 substrate", "caffeine", "substrate", "minor"),
    # CYP2B6 interactions
    ("Efavirenz - CYP2B6 substrate", "efavirenz", "substrate", "moderate"),
    ("Bupropion - CYP2B6 substrate", "bupropion", "substrate", "moderate"),
]

# Severity ranking for scoring
SEVERITY_SCORE = {"major": 3, "moderate": 2, "minor": 1}


def lookup(query, extra=None):
    """Single lookup: token overlap + substring scoring (no deps). Returns top hits.

    Args:
        query: Drug name or CYP interaction term to search for
        extra: Optional dict with additional context (unused in scoring but returned in result)

    Returns:
        dict with query, top_hit, score, interaction_type, severity, and all matches
    """
    q = str(query).lower().strip()
    if not q:
        return {"query": query, "top_hit": "no match", "score": 0, "interaction_type": None, "severity": None, "all": [], "extra": extra}

    scored = []
    for label, key, interaction_type, severity in CYP_DRUG_DATABASE:
        score = 0
        label_lower = label.lower()

        # Exact substring match
        if key in q:
            score += 10

        # Token overlap
        qt = set(q.split())
        lt = set(label_lower.split())
        overlap = len(qt & lt)
        score += overlap * 2

        # Only add severity bonus if there's an actual match
        if score > 0:
            score += SEVERITY_SCORE.get(severity, 0)
            scored.append((score, label, interaction_type, severity))

    scored.sort(reverse=True, key=lambda x: x[0])
    top = scored[0] if scored else (0, "no match", None, None)
    return {
        "query": query,
        "top_hit": top[1],
        "score": top[0],
        "interaction_type": top[2],
        "severity": top[3],
        "all": [(s, l, it, sev) for s, l, it, sev in scored[:5]],
        "extra": extra,
    }


def process_csv(inp, out):
    """Process a CSV file for drug interaction lookups.

    Args:
        inp: Path to input CSV file
        out: Path to output CSV file

    Returns:
        List of result rows

    Raises:
        FileNotFoundError: If input file does not exist
        ValueError: If CSV is malformed or empty
    """
    try:
        with open(inp, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fn = reader.fieldnames

            if not fn:
                raise ValueError(f"CSV file '{inp}' is empty or has no headers")
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: '{inp}'")

    # Guess query column
    qcol = fn[0]
    for cand in ["query", "test", "drug", "code", "variant", "hla", "lab", "name"]:
        if cand in [c.lower() for c in fn]:
            qcol = [c for c in fn if c.lower() == cand][0]
            break

    results = []
    for row in rows:
        res = lookup(row.get(qcol, ""), row)
        merged = {**row, "top_hit": res["top_hit"], "lookup_score": res["score"],
                  "interaction_type": res["interaction_type"], "severity": res["severity"]}
        results.append(merged)

    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fn) + ["top_hit", "lookup_score", "interaction_type", "severity"])
        w.writeheader()
        w.writerows(results)

    return results


def build_parser():
    p = argparse.ArgumentParser(prog="cyp_checker", description="CYP Drug Interaction Checker")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single")
    s.add_argument("query", nargs="?", default="simvastatin")
    s.add_argument("--query", dest="q2")
    b = sub.add_parser("batch")
    b.add_argument("--input", required=True, help="Path to input CSV file")
    b.add_argument("--output", required=True, help="Path to output CSV file")
    return p


def main(argv=None):
    p = build_parser()
    a = p.parse_args(argv)
    if a.cmd == "single":
        q = getattr(a, "q2", None) or getattr(a, "query")
        print(lookup(q))
        return 0
    if a.cmd == "batch":
        try:
            res = process_csv(a.input, a.output)
            print(f"Processed {len(res)} -> {a.output}")
            return 0
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    p.print_help()
    return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
