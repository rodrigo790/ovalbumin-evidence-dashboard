"""An interactive evidence panel for the chicken ovalbumin reference protein."""
import json

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from common import DATA

st.set_page_config(page_title="Ovalbumin Evidence Dashboard", page_icon="🧬", layout="wide")


@st.cache_data
def load_tables():
    return (
        pd.read_csv(DATA / "assays.csv").fillna(""),
        pd.read_csv(DATA / "residues.csv"),
        pd.read_csv(DATA / "region_scores.csv"),
        json.loads((DATA / "bibliography.json").read_text(encoding="utf-8")),
        (DATA / "ova.fasta").read_text(encoding="utf-8"),
    )


assays, structure, predictions, bibliography, fasta = load_tables()
sequence = "".join(fasta.splitlines()[1:])
st.title("Ovalbumin evidence dashboard")
st.caption("Gallus gallus · UniProt P01012 · reference antigen")
left, middle, right = st.columns(3)
left.metric("Sequence length", len(sequence))
middle.metric("Curated binding assays", len(assays))
right.metric("AlphaFold mean pLDDT", f"{structure.plddt.mean():.1f}")

evidence_tab, structure_tab, prediction_tab, sequence_tab, source_tab = st.tabs(
    ["Experiments", "3D structure", "Predictions", "Sequence", "Sources"]
)
with evidence_tab:
    st.subheader("Experimental binding assays")
    study = st.selectbox("PubMed study", ["All", *sorted(assays.pubmed_id.unique())])
    result = st.selectbox("Recorded outcome", ["All", *sorted(assays.qualitative_measure.unique())])
    selected = assays
    if study != "All":
        selected = selected[selected.pubmed_id.eq(study)]
    if result != "All":
        selected = selected[selected.qualitative_measure.eq(result)]
    display = selected[[
        "linear_sequence", "assay_names", "host_organism_name", "qualitative_measure", "pubmed_id"
    ]].copy()
    display["Assay record"] = selected.bcell_id.map(
        lambda x: f"https://www.iedb.org/details_v3.php?id={x}&type=assay"
    )
    display["Publication"] = selected.pubmed_id.map(lambda x: f"https://pubmed.ncbi.nlm.nih.gov/{x}/")
    display = display.drop(columns="pubmed_id").rename(columns={
        "linear_sequence": "Peptide", "assay_names": "Assay", "host_organism_name": "Host",
        "qualitative_measure": "Outcome",
    })
    st.dataframe(display, hide_index=True, width="stretch", column_config={
        "Assay record": st.column_config.LinkColumn("Assay record", display_text="IEDB record"),
        "Publication": st.column_config.LinkColumn("Publication", display_text="PubMed"),
    })
    st.download_button("Download selected assays", display.to_csv(index=False),
                       file_name="ovalbumin-assays.csv", mime="text/csv")

with structure_tab:
    st.subheader("AlphaFold model and fitted crystal chain")
    st.caption("AlphaFold AF-P01012-F1 v6 and experimental PDB 1OVA chain C.")
    protein, profile = st.columns([1.15, 1], gap="large")
    with protein:
        html = (DATA / "structure.html").read_text(encoding="utf-8")
        html = html.replace("width: 840px; height: 530px", "width: 100%; height: 420px")
        components.html(html, height=430)
        st.caption("Blue-gray is the AlphaFold model. Pale gray is the fitted crystal chain.")
    with profile:
        fig = px.line(structure, x="uniprot_position", y="plddt", hover_data=["aa", "ca_distance_A"])
        fig.update_traces(line_color="#187867")
        fig.update_layout(xaxis_title="UniProt residue", yaxis_title="Predicted pLDDT",
                          template="plotly_white", height=410, margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(fig, width="stretch")
    st.markdown("**Highlighted assay regions** · SIINFEKL (orange) · OVA 319–334 (teal) · OVA-108 (purple)")

with prediction_tab:
    st.subheader("Published predictors evaluated on ovalbumin")
    st.caption("Each percentile is computed within the full ovalbumin sequence for its own model.")
    columns = [c for c in predictions.columns if c.endswith("_percentile")]
    models = st.multiselect("Display model ranks", columns, default=columns)
    if models:
        fig = px.line(predictions, x="position", y=models)
        fig.update_layout(xaxis_title="UniProt residue", yaxis_title="Within-protein percentile",
                          legend_title="Model", template="plotly_white")
        st.plotly_chart(fig, width="stretch")

with sequence_tab:
    st.subheader("Reference sequence")
    st.code(fasta, language=None)
    st.download_button("Download UniProt FASTA", fasta,
                       file_name="P01012.fasta", mime="text/plain")

with source_tab:
    st.markdown("- [UniProt P01012](https://www.uniprot.org/uniprotkb/P01012/entry)")
    st.markdown("- [AlphaFold AF-P01012-F1](https://alphafold.ebi.ac.uk/entry/P01012)")
    st.markdown("- [RCSB PDB 1OVA](https://www.rcsb.org/structure/1OVA)")
    st.markdown("- [IEDB Query API](https://query-api.iedb.org/docs/swagger/)")
    for pmid, paper in bibliography.items():
        st.markdown(f"- {paper['title']} [{paper['year']} · PubMed](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
