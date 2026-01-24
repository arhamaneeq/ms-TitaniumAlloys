import pandas as pd
import json
from pathlib import Path

ATOMIC_WEIGHTS = {
    "Ti": 47.867,
    "Al": 26.9815385,
    "V": 50.9415,
    "Mo": 95.95,
    "Fe": 55.845,
    "Cr": 51.9961,
    "Sn": 118.71,
    "Zr": 91.224,
    "O": 15.999,
    "W": 183.84,
    "Si": 28.09,
    "Y": 88.91,
    "Nb": 92.91,
    "C": 12.01,
    "Bi": 208.98,
    "Nd": 144.24,
    "Ta": 180.95,
}

DATA_DIR = Path("data")
OUT_DIR = Path("out")
OUT_DIR.mkdir(exist_ok=True)


def load_csv(name):
    df = pd.read_csv(DATA_DIR / name, 
                     encoding="utf-8")
    df.columns = df.columns.str.strip()
    return df

mech = load_csv("mechanical.csv")
micro = load_csv("microstructure.csv")
comp = load_csv("composition.csv")
meta = load_csv("metadata.csv")

comp = comp.rename(columns={"wt%": "wt_pct"})
mech = mech.rename(columns={"elong_%": "elong_pct"})
comp["element"] = comp["element"].astype(str).str.strip()

for label, df in {
    "mechanical": mech,
    "microstructure": micro,
    "composition": comp,
    "metadata": meta
}.items():
    if "alloy_id" not in df.columns:
        raise ValueError(f"{label}.csv missing alloy_id column")

def compute_atomic_percent(df):
    rows = []
    for alloy_id, group in df.groupby("alloy_id"):
        moles = []
        for _, r in group.iterrows():
            el = r["element"]
            if el not in ATOMIC_WEIGHTS:
                raise ValueError(f"Atomic weight missing for {el}")
            moles.append(r["wt_pct"] / ATOMIC_WEIGHTS[el])

        total = sum(moles)
        for (_, r), mol in zip(group.iterrows(), moles):
            rows.append({
                "alloy_id": alloy_id,
                "element": r["element"],
                "wt_pct": r["wt_pct"],
                "at_pct": 100.0 * mol / total
            })

    return pd.DataFrame(rows)

comp = compute_atomic_percent(comp)

common_ids = (
    set(mech.alloy_id)
    & set(comp.alloy_id)
    & set(meta.alloy_id)
    & set(micro.alloy_id)
)

if not common_ids:
    raise RuntimeError("No common alloy_id across all CSVs")

for alloy_id in sorted(common_ids):
    mech_row = mech[mech.alloy_id == alloy_id].iloc[0]
    meta_row = meta[meta.alloy_id == alloy_id].iloc[0]
    comp_rows = comp[comp.alloy_id == alloy_id]
    micro_rows = micro[micro.alloy_id == alloy_id]

    composition = {
        r.element: {
            "wt_pct": float(r.wt_pct),
            "at_pct": float(r.at_pct)
        }
        for r in comp_rows.itertuples()
    }

    phases = []
    for r in micro_rows.itertuples():
        phases.append({
            "phase": r.phases_reported,
            "shape": r.shape,
            "volume_fraction": r.vol_fr,
            "grain_size_um": r.grain_size_um,
            "identification_method": r.phase_id_method
        })

    alloy_json = {
        "alloy_id": alloy_id,
        "phase_class": mech_row.phase_class,
        "composition": composition,
        "mechanical_properties": {
            "yield_strength_MPa": mech_row.YS_MPa,
            "ultimate_tensile_strength_MPa": mech_row.UTS_MPa,
            "elongation_pct": mech_row.elong_pct,
            "hardness": {
                "value": mech_row.hardness_value,
                "scale": mech_row.hardness_scale
            }
        },
        "test_conditions": {
            "temperature_K": mech_row.test_temp_K,
            "strain_rate_s-1": mech_row["strain_rate_s-1"]
        },
        "microstructure": phases,
        "metadata": {
            "DOI": meta_row.DOI,
            "source_type": meta_row.source_type,
            "data_location": meta_row.data_location,
            "processing_history": meta_row.processing_history,
            "test_standard": meta_row.test_standard
        }
    }

    out_file = OUT_DIR / f"{alloy_id}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(alloy_json, f, indent=2)

print(f"Generated {len(common_ids)} JSON files in '{OUT_DIR}'")
