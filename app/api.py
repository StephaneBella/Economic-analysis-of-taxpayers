from fastapi import FastAPI
from pydantic import BaseModel
import pickle
import pandas as pd
import os
from typing import List
import base64
import matplotlib.pyplot as plt
from fastapi.responses import JSONResponse



app = FastAPI()

# --- Chemins absolus ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
multiclass_model_path = os.path.join(BASE_DIR, "..", "models", "modele.pkl")
binary_model_path = os.path.join(BASE_DIR, "..", "models", "modele_binaire.pkl")

# --- Charger les modèles ---
with open(multiclass_model_path, "rb") as f:
    multiclass_model = pickle.load(f)

with open(binary_model_path, "rb") as f:
    binary_model = pickle.load(f)

# --- Mapping des labels ---
binary_labels = {0: "Pas risqué", 1: "Risqué"}
multiclass_labels = {0: "Pas de risque", 1: "Risque faible", 2: "Risque élevé"}


# --- Définition des features ---
class FraudFeatures(BaseModel):
    Regime: str
    Persojuri: str
    gctax__groupe_de_compte_de_gestion_des_contribuables: str
    Type_de_declarant_des_MP_dans_les_DSF: str
    Conformite_de_declaration_de_marches_en_2023: str
    MinCA23: str
    Nbprestation_marches: str
    Typedemarche: str
    MontantMP24: float
    DSF23: str


@app.get("/")
def read_root():
    return {"message": "API de Détection de Fraudes Fiscales prête 🚀"}


@app.post("/predict_one")
def predict_one(features: FraudFeatures, mode: str = "binary"):
    """
    mode = "binary" ou "multiclass"
    """
    # Créer un DataFrame avec les bons noms de colonnes
    input_df = pd.DataFrame([{
        "Regime": features.Regime,
        "Persojuri": features.Persojuri,
        "gctax (groupe de compte de gestion des contribuables)": features.gctax__groupe_de_compte_de_gestion_des_contribuables,
        "Type de déclarant des MP dans les DSF": features.Type_de_declarant_des_MP_dans_les_DSF,
        "Conformité de déclaration de marchés en 2023": features.Conformite_de_declaration_de_marches_en_2023,
        "MinCA23": features.MinCA23,
        "Nbprestation_marchés": features.Nbprestation_marches,
        "Typedemarché": features.Typedemarche,
        "MontantMP24": features.MontantMP24,
        "DSF23": features.DSF23
    }])

    # Choisir le modèle
    model = binary_model if mode == "binary" else multiclass_model

    # Prediction brute
    prediction = model.predict(input_df)[0]
    proba = model.predict_proba(input_df)[0]

    # Mapping des labels
    if mode == "binary":
        predicted_label = binary_labels.get(prediction, "Inconnu")
        proba_dict = {binary_labels[i]: float(p) for i, p in enumerate(proba)}
    else:
        predicted_label = multiclass_labels.get(prediction, "Inconnu")
        proba_dict = {multiclass_labels[i]: float(p) for i, p in enumerate(proba)}

    return {
        "modele_utilise": mode,
        "prediction": predicted_label,
        "probabilites": proba_dict
    }


@app.post("/predict_batch")
def predict_batch(features_list: List[FraudFeatures], mode: str = "binary"):
    """
    Prédictions en lot
    """
    input_data = []

    for f in features_list:
        input_data.append({
            "Regime": f.Regime,
            "Persojuri": f.Persojuri,
            "gctax (groupe de compte de gestion des contribuables)": f.gctax__groupe_de_compte_de_gestion_des_contribuables,
            "Type de déclarant des MP dans les DSF": f.Type_de_declarant_des_MP_dans_les_DSF,
            "Conformité de déclaration de marchés en 2023": f.Conformite_de_declaration_de_marches_en_2023,
            "MinCA23": f.MinCA23,
            "Nbprestation_marchés": f.Nbprestation_marches,
            "Typedemarché": f.Typedemarche,
            "MontantMP24": f.MontantMP24,
            "DSF23": f.DSF23
        })

    input_df = pd.DataFrame(input_data)

    # Choisir le modèle
    model = binary_model if mode == "binary" else multiclass_model

    predictions = model.predict(input_df)
    probas = model.predict_proba(input_df)

    results = []
    for i, pred in enumerate(predictions):
        if mode == "binary":
            label = binary_labels.get(pred, "Inconnu")
            proba_dict = {binary_labels[j]: float(p) for j, p in enumerate(probas[i])}
        else:
            label = multiclass_labels.get(pred, "Inconnu")
            proba_dict = {multiclass_labels[j]: float(p) for j, p in enumerate(probas[i])}

        results.append({
            "prediction": label,
            "probabilites": proba_dict
        })

    return {
        "modele_utilise": mode,
        "resultats": results
    }

@app.get("/plot_single")
def plot_single(mode: str = "binary"):
    # simulation de probabilités pour le graphique
    if mode == "binary":
        probs = [0.2, 0.8]
        labels = ["Pas risqué", "Risqué"]
    else:
        probs = [0.1,0.5,0.4]
        labels = ["Pas de risque","Risque faible","Risque élevé"]

    fig, ax = plt.subplots()
    bars = ax.bar(labels, probs, color=["green","orange","red"])
    for bar, p in zip(bars, probs):
        ax.text(bar.get_x()+bar.get_width()/2, p, f"{p*100:.1f}%", ha='center', va='bottom')
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return JSONResponse({"plot": base64.b64encode(buf.read()).decode()})