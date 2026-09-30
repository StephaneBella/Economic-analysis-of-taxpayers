import os
import io

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = "http://localhost:8000"

ORANGE = "#D9650A"
GREEN = "#157A42"
YELLOW = "#E2A710"
RED = "#C6303E"

# Libellés bruts renvoyés par l'API -> (classe de risque, icône)
RISK_CLASS = {
    "Pas risqué": "none",
    "Risqué": "high",
    "Pas de risque": "none",
    "Risque faible": "low",
    "Risque élevé": "high",
}
RISK_COLOR = {"none": GREEN, "low": YELLOW, "high": RED}
RISK_ICON = {"none": "check_circle", "low": "warning", "high": "report"}

MODE_LABELS = {
    "binary": "Lecture simple — Risqué / Pas risqué",
    "multiclass": "Lecture détaillée — Pas de risque / Risque faible / Risque élevé",
}

FIELD_OPTIONS = {
    "Regime": ["IGS", "REEL"],
    "Persojuri": ["Morale", "Physique"],
    "gctax": ["Petits comptes", "Grands comptes"],
    "TypeDecl": ["Déclarants permanents", "Défaillants"],
    "DSF23": ["Oui", "Non"],
    "Conformite": ["MD", "NPC", "MND"],
    "MinCA23": ["Non", "Oui"],
    "Nbprestation": ["Plus de deux marchés", "Un marché", "Deux marchés"],
    "Typedemarche": ["Bons_commande", "Lettre_commande&Marchés", "Mixte"],
}

# Libellés affichés à l'utilisateur (les valeurs envoyées à l'API restent inchangées)
DISPLAY_LABELS = {
    "IGS": "Impôt Général Synthétique (petites activités)",
    "REEL": "Régime du réel (activités plus importantes)",
    "Morale": "Entreprise ou organisation",
    "Physique": "Particulier (entrepreneur individuel)",
    "Déclarants permanents": "Oui, il déclare régulièrement",
    "Défaillants": "Non, des déclarations manquent",
    "MD": "Marchés déclarés",
    "MND": "Marchés non déclarés",
    "NPC": "Autre situation (NPC)",
    "Bons_commande": "Bons de commande (petites commandes)",
    "Lettre_commande&Marchés": "Lettres de commande et marchés",
    "Mixte": "Les deux à la fois",
}

# Éléments qui pèsent le plus dans l'estimation, du plus au moins important
FACTORS = {
    "multiclass": [
        ("Montant des marchés publics obtenus en 2024", "Très fort"),
        ("Régularité des déclarations de marchés", "Fort"),
        ("Régime d'imposition", "Fort"),
        ("Nombre de marchés obtenus", "Moyen"),
        ("Taille du contribuable (petit ou grand compte)", "Faible"),
        ("Déclaration des marchés en 2023", "Faible"),
        ("Type de contrat obtenu", "Faible"),
        ("Entreprise ou particulier", "Très faible"),
    ],
    "binary": [
        ("Régime d'imposition", "Très fort"),
        ("Régularité des déclarations de marchés", "Fort"),
        ("Montant des marchés publics obtenus en 2024", "Fort"),
        ("Nombre de marchés obtenus", "Moyen"),
        ("Déclaration des marchés en 2023", "Moyen"),
        ("Taille du contribuable (petit ou grand compte)", "Moyen"),
        ("Type de contrat obtenu", "Faible"),
        ("Entreprise ou particulier", "Très faible"),
    ],
}
FACTOR_LEVEL_CLASS = {"Très fort": "lvl-4", "Fort": "lvl-3", "Moyen": "lvl-2", "Faible": "lvl-1", "Très faible": "lvl-0"}

SERVICE_UNAVAILABLE = (
    "Le service de calcul n'est pas disponible pour le moment. "
    "Réessayez dans quelques instants."
)


def display_label(value):
    return DISPLAY_LABELS.get(value, value)


def inject_css(css_file="style.css"):
    css_path = os.path.join(BASE_DIR, css_file)
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_hero():
    st.markdown(
        """
        <div class="hero-banner">
          <div class="hero-risk-stripe"><span></span><span></span><span></span></div>
          <div class="hero-eyebrow">Travail de recherche · Cameroun</div>
          <div class="hero-title">Les comportements à risque des contribuables camerounais</div>
          <div class="hero-subtitle">
            Cette étude cherche à comprendre quels profils de contribuables sont les plus
            susceptibles de ne pas respecter leurs obligations fiscales. Décrivez un profil
            fictif et découvrez le niveau de risque estimé.
          </div>
          <div class="hero-badge-row">
            <span class="hero-badge"><span class="material-symbols-rounded">school</span>Étude à visée de recherche</span>
            <span class="hero-badge"><span class="material-symbols-rounded">science</span>Données simulées</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_simulated_data_notice():
    st.markdown(
        """
        <div class="sim-notice">
          <span class="material-symbols-rounded">verified_user</span>
          <div>
            <div class="sim-notice-title">Des données entièrement fictives</div>
            <div class="sim-notice-text">
              Toutes les informations présentées ici — profils de contribuables, montants des
              marchés, résultats — sont <strong>inventées pour les besoins de l'étude</strong>.
              Elles ne concernent aucune personne ni aucune entreprise réelle. Ce que vous
              saisissez n'est pas conservé.
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def form_section_header(title, icon=None):
    icon_html = f'<span class="material-symbols-rounded" style="font-size:1rem;color:var(--orange-d);margin-right:.15rem;">{icon}</span>' if icon else '<span class="fsn-dot"></span>'
    st.markdown(
        f"""
        <div class="form-section-header">{icon_html}{title}</div>
        """,
        unsafe_allow_html=True,
    )


def empty_result_message(text_title, text_body):
    st.markdown(
        f"""
        <div class="empty-state">
          <div class="empty-icon"><span class="material-symbols-rounded" style="font-size:3rem;">query_stats</span></div>
          <h3>{text_title}</h3>
          <p>{text_body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_factor_list(mode):
    items = "".join(
        f'<li class="factor-item">'
        f'<span class="factor-rank">{i}</span>'
        f'<span class="factor-name">{name}</span>'
        f'<span class="factor-level {FACTOR_LEVEL_CLASS[level]}">{level}</span>'
        f"</li>"
        for i, (name, level) in enumerate(FACTORS[mode], start=1)
    )
    st.markdown(f'<ol class="factor-list">{items}</ol>', unsafe_allow_html=True)


def show_error(message, details=None):
    st.error(message, icon=":material/error:")
    if details:
        with st.expander("Détails (pour l'assistance)"):
            st.code(str(details))


def plot_probabilities(proba_dict: dict):
    labels = list(proba_dict.keys())
    values = [float(v) for v in proba_dict.values()]
    colors = [RISK_COLOR.get(RISK_CLASS.get(label, "low"), ORANGE) for label in labels]

    fig = go.Figure()
    for label, value, color in zip(labels, values, colors):
        fig.add_trace(
            go.Bar(
                x=[value],
                y=[label],
                orientation="h",
                marker=dict(color=color, line=dict(width=0)),
                text=f"<b>{value * 100:.1f}%</b>",
                textposition="auto",
                textfont=dict(size=13, family="Inter"),
                hovertemplate=f"<b>{label}</b><br>Estimation : {value * 100:.1f}%<extra></extra>",
                showlegend=False,
            )
        )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#191712"),
        xaxis=dict(tickformat=".0%", range=[0, 1], showgrid=True, gridcolor="#E8E0D3", zeroline=False),
        yaxis=dict(showgrid=False, automargin=True),
        bargap=0.35,
        height=max(180, len(labels) * 70),
        margin=dict(l=10, r=20, t=10, b=10),
    )
    return fig


def plot_batch_distribution(counts: pd.Series):
    labels = list(counts.index)
    values = list(counts.values)
    colors = [RISK_COLOR.get(RISK_CLASS.get(label, "low"), ORANGE) for label in labels]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=labels,
            y=values,
            text=values,
            textposition="auto",
            marker=dict(color=colors),
            showlegend=False,
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#191712"),
        title="Répartition des profils par niveau de risque",
        xaxis_title="Niveau de risque",
        yaxis_title="Nombre de profils",
        height=320,
        margin=dict(l=10, r=20, t=50, b=10),
    )
    return fig


def render_verdict_card(prediction_label: str, proba_dict: dict):
    risk_class = RISK_CLASS.get(prediction_label, "low")
    color = RISK_COLOR[risk_class]
    icon = RISK_ICON[risk_class]
    confidence = max(proba_dict.values()) * 100 if proba_dict else 0

    st.markdown(
        f"""
        <div class="pred-card verdict-{risk_class}">
          <div class="verdict-tag" style="color:{color}">
            <span class="material-symbols-rounded" style="font-size:1rem;">{icon}</span>
            Résultat
          </div>
          <div class="verdict-label {risk_class}">{prediction_label}</div>
          <div class="verdict-description">
            Ce résultat est une estimation obtenue à partir du profil fictif que vous avez
            décrit. Il ne constitue en aucun cas un jugement sur une personne réelle.
          </div>
          <div class="verdict-confidence">
            <span class="material-symbols-rounded" style="font-size:.95rem;">insights</span>
            Degré de certitude : {confidence:.1f}%
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_payload(regime, persojuri, gctax, typedecl, conformite, minca23, nbprestation, typedemarche, montant, dsf23):
    return {
        "Regime": regime,
        "Persojuri": persojuri,
        "gctax__groupe_de_compte_de_gestion_des_contribuables": gctax,
        "Type_de_declarant_des_MP_dans_les_DSF": typedecl,
        "Conformite_de_declaration_de_marches_en_2023": conformite,
        "MinCA23": minca23,
        "Nbprestation_marches": nbprestation,
        "Typedemarche": typedemarche,
        "MontantMP24": montant,
        "DSF23": dsf23,
    }


def main():
    st.set_page_config(
        page_title="Comportements à risque des contribuables",
        page_icon=":material/query_stats:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    inject_css()

    render_hero()
    render_simulated_data_notice()

    tab1, tab2, tab3 = st.tabs(
        [
            ":material/menu_book: À propos de l'étude",
            ":material/insights: Ce qui influence le risque",
            ":material/fact_check: Évaluer un profil",
        ]
    )

    # =================================================
    # Onglet 1 : À propos de l'étude
    # =================================================
    with tab1:
        st.markdown('<div class="section-title">De quoi parle cette étude ?</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-lead">Ce travail de recherche s\'intéresse aux contribuables camerounais '
            "qui obtiennent des marchés publics, c'est-à-dire des contrats avec l'État ou des "
            "organismes publics. L'objectif est de repérer les comportements qui augmentent le "
            "risque de ne pas respecter ses obligations fiscales : déclarations manquantes, "
            "marchés non déclarés, etc. Toutes les données utilisées sont fictives.</div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="model-grid">
              <div class="model-card binary">
                <div class="model-card-icon"><span class="material-symbols-rounded">balance</span></div>
                <div class="model-card-tag">Lecture simple</div>
                <div class="model-card-title">Risqué ou pas risqué ?</div>
                <div class="model-card-text">
                  Une réponse directe : au vu de son profil, le contribuable présente-t-il
                  un comportement à risque, oui ou non ?
                </div>
                <div class="model-card-classes">
                  <span class="class-chip risk-none">Pas risqué</span>
                  <span class="class-chip risk-high">Risqué</span>
                </div>
              </div>
              <div class="model-card multiclass">
                <div class="model-card-icon"><span class="material-symbols-rounded">stacked_bar_chart</span></div>
                <div class="model-card-tag">Lecture détaillée</div>
                <div class="model-card-title">Trois niveaux de risque</div>
                <div class="model-card-text">
                  Une lecture plus nuancée, qui distingue les profils sans risque, ceux
                  qui présentent un risque faible et ceux qui présentent un risque élevé.
                </div>
                <div class="model-card-classes">
                  <span class="class-chip risk-none">Pas de risque</span>
                  <span class="class-chip risk-low">Risque faible</span>
                  <span class="class-chip risk-high">Risque élevé</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="info-callout">
              <span class="material-symbols-rounded">lightbulb</span>
              <div>
                <strong>Comment ça marche ?</strong>
                L'outil a été construit à partir d'un grand nombre de profils fictifs dont on
                connaissait déjà le niveau de risque. En les comparant, il a appris à
                reconnaître les situations qui reviennent le plus souvent chez les profils à
                risque. Lorsqu'on lui présente un nouveau profil, il estime à quel groupe
                celui-ci ressemble le plus.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # =================================================
    # Onglet 2 : Ce qui influence le risque
    # =================================================
    with tab2:
        st.markdown('<div class="section-title">Ce qui influence le plus le risque</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-lead">Les éléments du profil ci-dessous sont classés du plus '
            "au moins déterminant dans l'estimation du risque.</div>",
            unsafe_allow_html=True,
        )

        sub_multi, sub_bin = st.tabs(["Lecture détaillée (3 niveaux)", "Lecture simple (oui / non)"])

        with sub_multi:
            with st.container(border=True):
                form_section_header("Classement des éléments — lecture détaillée", icon="stacked_bar_chart")
                render_factor_list("multiclass")
                st.markdown(
                    """
                    <div class="info-callout">
                      <span class="material-symbols-rounded">lightbulb</span>
                      <div>
                        <strong>Ce que l'on observe.</strong>
                        Le montant des marchés publics obtenus est, de loin, l'élément qui pèse
                        le plus : plus les sommes en jeu sont importantes, plus il faut être
                        attentif. Viennent ensuite la régularité des déclarations et le régime
                        d'imposition : les contribuables qui ne déclarent pas tous leurs
                        marchés, ainsi que ceux du régime du réel, présentent plus souvent un
                        risque. Le nombre de marchés obtenus compte aussi : les contribuables
                        ayant un seul marché ou plus de deux marchés ont des profils de risque
                        différents. La déclaration des marchés en 2023 et le type de contrat
                        complètent le tableau.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with sub_bin:
            with st.container(border=True):
                form_section_header("Classement des éléments — lecture simple", icon="balance")
                render_factor_list("binary")
                st.markdown(
                    """
                    <div class="info-callout">
                      <span class="material-symbols-rounded">lightbulb</span>
                      <div>
                        <strong>Ce que l'on observe.</strong>
                        Ici, c'est le régime d'imposition qui compte le plus : être au régime du
                        réel est le signe le plus marquant d'un risque. La régularité des
                        déclarations arrive en deuxième position : déclarer ou non ses marchés
                        publics fait une vraie différence. Le montant des marchés reste
                        important mais passe au troisième rang, ce qui montre que la situation
                        et les habitudes du contribuable comptent davantage que la seule valeur
                        de ses contrats. Le nombre de marchés et leur déclaration en 2023 jouent
                        un rôle notable, tandis que le type de contrat et le fait d'être une
                        entreprise ou un particulier pèsent peu.
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # =================================================
    # Onglet 3 : Évaluer un profil
    # =================================================
    with tab3:
        st.markdown('<div class="section-title">Évaluer un profil de contribuable</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-lead">Décrivez un contribuable fictif, ou importez une liste de '
            "profils fictifs, pour connaître le niveau de risque estimé.</div>",
            unsafe_allow_html=True,
        )

        mode_pred = st.selectbox(
            "Que souhaitez-vous faire ?",
            ["Évaluer un seul profil", "Évaluer une liste de profils"],
        )

        # -----------------------------------------
        # Mode 1 : un seul profil
        # -----------------------------------------
        if mode_pred == "Évaluer un seul profil":
            with st.form("profil_form"):
                with st.container(border=True):
                    form_section_header("Qui est le contribuable ?", icon="person")
                    c1, c2 = st.columns(2)
                    with c1:
                        regime = st.selectbox(
                            "Régime d'imposition",
                            FIELD_OPTIONS["Regime"],
                            format_func=display_label,
                            help="Le régime dépend surtout de la taille de l'activité : les petites "
                            "activités paient un impôt simplifié, les plus importantes relèvent du régime du réel.",
                        )
                        persojuri = st.selectbox(
                            "Entreprise ou particulier ?",
                            FIELD_OPTIONS["Persojuri"],
                            format_func=display_label,
                        )
                        gctax = st.selectbox(
                            "Taille du contribuable",
                            FIELD_OPTIONS["gctax"],
                            help="Les « grands comptes » regroupent les contribuables les plus importants.",
                        )
                    with c2:
                        typedecl = st.selectbox(
                            "Déclare-t-il régulièrement ses marchés publics ?",
                            FIELD_OPTIONS["TypeDecl"],
                            format_func=display_label,
                            help="Indique si le contribuable mentionne bien ses marchés publics "
                            "dans ses déclarations annuelles.",
                        )
                        dsf23 = st.selectbox(
                            "A-t-il déposé sa déclaration annuelle 2023 ?",
                            FIELD_OPTIONS["DSF23"],
                            help="La déclaration annuelle est le document dans lequel le contribuable "
                            "présente chaque année ses comptes et son activité.",
                        )

                st.write("")
                with st.container(border=True):
                    form_section_header("Ses marchés publics", icon="work_history")
                    c3, c4 = st.columns(2)
                    with c3:
                        conformite = st.selectbox(
                            "Ses marchés de 2023 ont-ils été déclarés ?",
                            FIELD_OPTIONS["Conformite"],
                            format_func=display_label,
                        )
                        minca23 = st.selectbox(
                            "Chiffre d'affaires minimum atteint en 2023 ?",
                            FIELD_OPTIONS["MinCA23"],
                            help="Le chiffre d'affaires correspond au total des ventes ou des recettes de l'année.",
                        )
                        nbprestation = st.selectbox(
                            "Nombre de marchés obtenus",
                            FIELD_OPTIONS["Nbprestation"],
                        )
                    with c4:
                        typedemarche = st.selectbox(
                            "Type de contrat obtenu",
                            FIELD_OPTIONS["Typedemarche"],
                            format_func=display_label,
                        )
                        montant = st.number_input(
                            "Montant total des marchés obtenus en 2024 (FCFA)",
                            min_value=0.0,
                            step=100000.0,
                            format="%.0f",
                        )

                mode = st.selectbox(
                    "Type de lecture du risque",
                    ["binary", "multiclass"],
                    format_func=lambda v: MODE_LABELS[v],
                )
                submitted = st.form_submit_button(
                    "Voir le résultat",
                    icon=":material/bolt:",
                    use_container_width=True,
                )

            if not submitted:
                empty_result_message(
                    "Aucun résultat pour l'instant",
                    "Remplissez le profil ci-dessus puis cliquez sur « Voir le résultat ».",
                )
            else:
                try:
                    with st.spinner("Calcul en cours..."):
                        payload = build_payload(
                            regime, persojuri, gctax, typedecl, conformite,
                            minca23, nbprestation, typedemarche, montant, dsf23,
                        )
                        response = requests.post(
                            f"{API_BASE}/predict_one",
                            params={"mode": mode},
                            json=payload,
                            timeout=15,
                        )

                    if response.status_code == 200:
                        result = response.json()
                        col_v, col_p = st.columns([1.1, 1])
                        with col_v:
                            render_verdict_card(result["prediction"], result["probabilites"])
                        with col_p:
                            st.markdown(
                                """
                                <div class="info-callout">
                                  <span class="material-symbols-rounded">bar_chart</span>
                                  <div><strong>Détail du résultat.</strong> Chance estimée pour chaque niveau de risque.</div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            st.plotly_chart(
                                plot_probabilities(result["probabilites"]),
                                use_container_width=True,
                                config=dict(displayModeBar=False),
                            )
                    else:
                        show_error(
                            "Le résultat n'a pas pu être calculé. Vérifiez les informations saisies et réessayez.",
                            f"{response.status_code} : {response.text}",
                        )

                except requests.exceptions.ConnectionError:
                    show_error(SERVICE_UNAVAILABLE)
                except Exception as e:
                    show_error("Une erreur inattendue est survenue. Réessayez.", e)

        # -----------------------------------------
        # Mode 2 : liste de profils
        # -----------------------------------------
        else:
            uploaded_file = st.file_uploader(
                ":material/upload_file: Importez votre liste de profils fictifs (fichier CSV, pouvant être créé avec Excel)",
                type=["csv"],
            )
            mode = st.selectbox(
                "Type de lecture du risque",
                ["binary", "multiclass"],
                format_func=lambda v: MODE_LABELS[v],
            )

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
                st.markdown(
                    f'<div class="info-callout"><span class="material-symbols-rounded">table_rows</span>'
                    f"<div><strong>{len(df)} profil(s) chargé(s).</strong> Voici les premiers de la liste.</div></div>",
                    unsafe_allow_html=True,
                )
                st.dataframe(df.head(), use_container_width=True, hide_index=True)

                run_batch = st.button(
                    "Évaluer tous les profils",
                    icon=":material/dataset:",
                    use_container_width=True,
                )

                if run_batch:
                    try:
                        with st.spinner("Évaluation des profils en cours..."):
                            records = df.to_dict(orient="records")
                            response = requests.post(
                                f"{API_BASE}/predict_batch",
                                params={"mode": mode},
                                json=records,
                                timeout=60,
                            )

                        if response.status_code == 200:
                            result = response.json()
                            preds = result["resultats"]

                            pred_labels = [r["prediction"] for r in preds]
                            pred_probs = [max(r["probabilites"].values()) for r in preds]

                            result_df = df.copy()
                            result_df["Niveau de risque"] = pred_labels
                            result_df["Degré de certitude (%)"] = [round(p * 100, 1) for p in pred_probs]

                            st.success(
                                f"{len(result_df)} profil(s) évalué(s).",
                                icon=":material/check_circle:",
                            )
                            st.dataframe(result_df, use_container_width=True, hide_index=True)

                            col_chart, col_dl = st.columns([2, 1])
                            with col_chart:
                                counts = result_df["Niveau de risque"].value_counts()
                                st.plotly_chart(
                                    plot_batch_distribution(counts),
                                    use_container_width=True,
                                    config=dict(displayModeBar=False),
                                )
                            with col_dl:
                                st.write("")
                                st.write("")
                                csv_buffer = io.StringIO()
                                result_df.to_csv(csv_buffer, index=False)
                                st.download_button(
                                    "Télécharger les résultats",
                                    data=csv_buffer.getvalue(),
                                    file_name="resultats_niveaux_de_risque.csv",
                                    mime="text/csv",
                                    icon=":material/download:",
                                    use_container_width=True,
                                )
                        else:
                            show_error(
                                "Les résultats n'ont pas pu être calculés. Vérifiez que le fichier "
                                "contient bien toutes les informations attendues.",
                                f"{response.status_code} : {response.text}",
                            )

                    except requests.exceptions.ConnectionError:
                        show_error(SERVICE_UNAVAILABLE)
                    except Exception as e:
                        show_error("Une erreur inattendue est survenue. Réessayez.", e)
            else:
                empty_result_message(
                    "Aucun fichier importé",
                    "Importez un fichier contenant un ou plusieurs profils fictifs pour les évaluer tous en une fois.",
                )

    # -------------------------------------------------------------------
    # Footer
    # -------------------------------------------------------------------
    st.markdown(
        """
        <div class="footer-container">
          <div class="footer-body">
            Travail de recherche sur les comportements à risque des contribuables camerounais,
            réalisé à partir de données entièrement fictives.
          </div>
          <div class="footer-strip">
            <strong>Comportements à risque des contribuables</strong> · Données fictives · À des fins de recherche uniquement
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
