"""Validate dashboard assets and summarize the evidence snapshot."""
import json

import pandas as pd

from common import DATA, save_summary


def main():
    assays = pd.read_csv(DATA / "assays.csv")
    residues = pd.read_csv(DATA / "residues.csv")
    prediction = pd.read_csv(DATA / "region_scores.csv")
    reference = "".join((DATA / "ova.fasta").read_text().splitlines()[1:])
    papers = json.loads((DATA / "bibliography.json").read_text(encoding="utf-8"))
    if not assays.bcell_id.is_unique or not all(str(pmid) in papers for pmid in assays.pubmed_id):
        raise ValueError("Invalid provenance for experimental records")
    if reference != "".join(residues.aa) or reference != "".join(prediction.aa):
        raise ValueError("Sequence, structure and predictor tracks differ")
    save_summary({
        "antigen": "Gallus gallus ovalbumin", "uniprot": "P01012",
        "sequence_length": len(reference), "assay_records": len(assays), "studies": len(papers),
        "mapped_crystal_residues": int(residues.pdb_resnum.notna().sum()),
        "prediction_tracks": [name for name in prediction.columns if name.endswith("_percentile")],
        "experimental_outcomes": {name: int(value) for name, value in assays.qualitative_measure.value_counts().items()},
    })


if __name__ == "__main__":
    main()
