import json
import unittest

import pandas as pd

from common import DATA, RESULTS


class DashboardTests(unittest.TestCase):
    def test_provenance_and_common_coordinates(self):
        assays = pd.read_csv(DATA / "assays.csv")
        papers = json.loads((DATA / "bibliography.json").read_text())
        reference = "".join((DATA / "ova.fasta").read_text().splitlines()[1:])
        structure = pd.read_csv(DATA / "residues.csv")
        predictions = pd.read_csv(DATA / "region_scores.csv")
        self.assertEqual(reference, "".join(structure.aa))
        self.assertEqual(reference, "".join(predictions.aa))
        self.assertEqual(list(structure.uniprot_position), list(predictions.position))
        self.assertEqual(set(assays.pubmed_id.astype(str)), set(papers))
        self.assertTrue(assays.bcell_id.is_unique)
        self.assertEqual(json.loads((RESULTS / "summary.json").read_text())["assay_records"], len(assays))
