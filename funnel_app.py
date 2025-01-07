import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

# File CSV per salvare i dati
DATA_FILE = "funnel_data.csv"

# Funzione per caricare i dati esistenti
def load_data():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if "Note" not in df.columns:
            df["Note"] = ""  # Aggiungi colonna "Note" se mancante
        return df
    else:
        return pd.DataFrame(columns=["Mese", "Canale", "Investimento", "Impression", "Click", "Lead", 
                                     "Assessment Fissati", "Assessment Fatti", 
                                     "Accordi Inviati", "Vendite", "Note"])

# Funzione per salvare i dati
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# Carica i dati esistenti
data = load_data()

# Funzione per modificare un record
def modifica_dati(index, valori_modificati):
    global data
    for key, value in valori_modificati.items():
        data.loc[index, key] = value
    save_data(data)

# Funzione per calcolare le metriche
def calcola_metriche(dati, globale=False):
    investimento_totale = dati["Investimento"].sum()
    lead_totali = dati["Lead"].sum()
    vendite_totali = dati["Vendite"].sum()

    cpl = investimento_totale / lead_totali if lead_totali > 0 else None
    cac = investimento_totale / vendite_totali if vendite_totali > 0 else None

    metriche = {
        "Investimento Totale": investimento_totale,
        "CPL (Costo per Lead)": cpl,
        "CAC (Costo Cliente)": cac,
    }

    if not globale:
        click_totali = dati["Click"].sum()
        conversione_landing = (click_totali / dati["Impression"].sum()) * 100 if dati["Impression"].sum() > 0 else None
        cpc = investimento_totale / click_totali if click_totali > 0 else None
        metriche["CPC (Costo per Click)"] = cpc
        metriche["Tasso di conversione Landing"] = conversione_landing

    # Tassi di conversione
    conversione_lead = (lead_totali / dati["Click"].sum()) * 100 if dati["Click"].sum() > 0 else None
    conversione_assessment_fissati = (dati["Assessment Fissati"].sum() / lead_totali) * 100 if lead_totali > 0 else None
    conversione_assessment_fatti = (dati["Assessment Fatti"].sum() / dati["Assessment Fissati"].sum()) * 100 if dati["Assessment Fissati"].sum() > 0 else None
    conversione_accordi = (dati["Accordi Inviati"].sum() / dati["Assessment Fatti"].sum()) * 100 if dati["Assessment Fatti"].sum() > 0 else None
    conversione_vendite = (vendite_totali / dati["Accordi Inviati"].sum()) * 100 if dati["Accordi Inviati"].sum() > 0 else None

    metriche["Tassi Conversione"] = [
        conversione_lead,
        conversione_assessment_fissati,
        conversione_assessment_fatti,
        conversione_accordi,
        conversione_vendite,
    ]

    return metriche

# Funzione per visualizzare metriche in stile card
def mostra_metriche_in_card(metriche):
    st.markdown(
        """
        <style>
        .card {
            background-color: #2C2C2C;
            color: white;
            padding: 15px;
            margin: 10px;
            border-radius: 10px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
        }
        .card-title {
            font-size: 18px;
            font-weight: bold;
        }
        .card-value {
            font-size: 24px;
            font-weight: bold;
            color: #4CAF50;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(3)
    i = 0
    for key, value in metriche.items():
        if isinstance(value, list):  # Ignora i tassi di conversione
            continue
        formatted_value = f"{value:.2f}" if value is not None else "N/A"
        with cols[i % 3]:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-title">{key}</div>
                    <div class="card-value">{formatted_value if "€" in key else f"€{formatted_value}"}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        i += 1

# Funzione per creare un grafico a imbuto
def crea_grafico_funnel(dati, titolo, tassi_conversione):
    stages = ["Lead", "Assessment Fissati", "Assessment Fatti", "Accordi Inviati", "Vendite"]
    values = dati[["Lead", "Assessment Fissati", "Assessment Fatti", "Accordi Inviati", "Vendite"]].sum().values

    fig = go.Figure()

    fig.add_trace(go.Funnel(
        y=stages,
        x=values,
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(color=["#4CAF50", "#2196F3", "#FFC107", "#FF5722", "#9C27B0"])
    ))

    # Aggiunta delle percentuali sulla destra
    for i, percentage in enumerate(tassi_conversione):
        fig.add_annotation(
            x=values[i],
            y=stages[i],
            text=f"{percentage:.2f}%" if percentage is not None else "N/A",
            showarrow=False,
            xanchor="left",
            font=dict(size=14, color="white")
        )

    fig.update_layout(
        title=titolo,
        font=dict(size=16),
        plot_bgcolor="#2C2C2C",
        paper_bgcolor="#2C2C2C",
        font_color="white",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig

# Sidebar per selezionare il canale
st.sidebar.title("Menu Canali")
menu_opzioni = ["Inserisci dati", "Modifica dati"] + ["Google Ads", "Facebook Ads", "LinkedIn Ads", "Email Marketing", "Altro", "Globale"]
sezione_selezionata = st.sidebar.radio("Seleziona un'opzione", options=menu_opzioni)

# Sezione per modificare i dati
if sezione_selezionata == "Modifica dati":
    st.title("Modifica o Elimina Dati Salvati")
    
    if data.empty:
        st.warning("Nessun dato disponibile da modificare o eliminare.")
    else:
        # Seleziona il record da modificare o eliminare
        indice_record = st.selectbox("Seleziona il record da modificare o eliminare", data.index, format_func=lambda i: f"{data.loc[i, 'Mese']} - {data.loc[i, 'Canale']}")

        if indice_record is not None:
            record_selezionato = data.loc[indice_record]
            
            # Mostra un form precompilato con i dati del record selezionato
            mese_modificato = st.text_input("Mese", record_selezionato["Mese"])
            canale_modificato = st.selectbox("Canale", ["Google Ads", "Facebook Ads", "LinkedIn Ads", "Email Marketing", "Altro"], index=["Google Ads", "Facebook Ads", "LinkedIn Ads", "Email Marketing", "Altro"].index(record_selezionato["Canale"]))
            investimento_modificato = st.number_input("Investimento (€)", value=record_selezionato["Investimento"])
            impression_modificate = st.number_input("Impression", value=record_selezionato["Impression"])
            click_modificati = st.number_input("Click", value=record_selezionato["Click"])
            lead_modificati = st.number_input("Lead", value=record_selezionato["Lead"])
            assessment_fissati_modificati = st.number_input("Assessment Fissati", value=record_selezionato["Assessment Fissati"])
            assessment_fatti_modificati = st.number_input("Assessment Fatti", value=record_selezionato["Assessment Fatti"])
            accordi_inviati_modificati = st.number_input("Accordi Inviati", value=record_selezionato["Accordi Inviati"])
            vendite_modificate = st.number_input("Vendite", value=record_selezionato["Vendite"])
            note_modificate = st.text_area("Note", record_selezionato["Note"])

            # Bottone per salvare le modifiche
            if st.button("Aggiorna"):
                nuovi_valori = {
                    "Mese": mese_modificato,
                    "Canale": canale_modificato,
                    "Investimento": investimento_modificato,
                    "Impression": impression_modificate,
                    "Click": click_modificati,
                    "Lead": lead_modificati,
                    "Assessment Fissati": assessment_fissati_modificati,
                    "Assessment Fatti": assessment_fatti_modificati,
                    "Accordi Inviati": accordi_inviati_modificati,
                    "Vendite": vendite_modificate,
                    "Note": note_modificate
                }
                modifica_dati(indice_record, nuovi_valori)
                st.success("Record aggiornato con successo! Ricarica manualmente la pagina per vedere i dati aggiornati.")

            # Bottone per eliminare il record selezionato
            if st.button("Elimina"):
                data = data.drop(indice_record).reset_index(drop=True)  # Rimuove il record
                save_data(data)  # Salva il dataframe aggiornato
                st.success("Record eliminato con successo! Ricarica manualmente la pagina per vedere i dati aggiornati.")

# Scheda per inserimento dati
elif sezione_selezionata == "Inserisci dati":
    st.title("Inserisci Dati")

    # Form per l'inserimento dei dati
    mesi = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    anno = st.sidebar.number_input("Anno", min_value=2020, max_value=2100, value=2025, step=1)
    mese = st.sidebar.selectbox("Seleziona il mese", options=mesi)
    mese_selezionato = f"{mese} {anno}"
    canali_disponibili = ["Google Ads", "Facebook Ads", "LinkedIn Ads", "Email Marketing", "Altro"]
    canale = st.sidebar.selectbox("Seleziona il canale", options=canali_disponibili)

    investimento = st.number_input("Investimento (€)", min_value=0.0, step=50.0)
    impression = st.number_input("Impression", min_value=0, step=100)
    click = st.number_input("Click", min_value=0, step=10)
    lead = st.number_input("Lead", min_value=0, step=1)
    assessment_fissati = st.number_input("Assessment Fissati", min_value=0, step=1)
    assessment_fatti = st.number_input("Assessment Fatti", min_value=0, step=1)
    accordi_inviati = st.number_input("Accordi Inviati", min_value=0, step=1)
    vendite = st.number_input("Vendite", min_value=0, step=1)
    note = st.text_area("Aggiungi una nota (opzionale)")

    if st.button("Salva"):
        nuovo_dato = pd.DataFrame({
            "Mese": [mese_selezionato],
            "Canale": [canale],
            "Investimento": [investimento],
            "Impression": [impression],
            "Click": [click],
            "Lead": [lead],
            "Assessment Fissati": [assessment_fissati],
            "Assessment Fatti": [assessment_fatti],
            "Accordi Inviati": [accordi_inviati],
            "Vendite": [vendite],
            "Note": [note],
        })
        data = pd.concat([data, nuovo_dato], ignore_index=True)
        save_data(data)
        st.success("Dati salvati con successo!")

    # Visualizzazione dei dati salvati
    st.subheader("Dati Salvati")
    st.dataframe(data)

# Schede per visualizzare metriche e grafici
else:
    st.title(f"Visualizzazione {sezione_selezionata}")

    globale = sezione_selezionata == "Globale"
    if not globale:
        dati_canale = data[data["Canale"] == sezione_selezionata]
    else:
        dati_canale = data

    mesi_disponibili = dati_canale["Mese"].unique()
    mese_selezionato = st.selectbox("Seleziona mese", options=["Tutti"] + list(mesi_disponibili))

    if mese_selezionato != "Tutti":
        dati_canale = dati_canale[dati_canale["Mese"] == mese_selezionato]

    if dati_canale.empty:
        st.warning(f"Nessun dato disponibile per {sezione_selezionata}.")
    else:
        metriche = calcola_metriche(dati_canale, globale=globale)
        st.subheader("Metriche")
        mostra_metriche_in_card(metriche)
        st.subheader("Grafico Funnel")
        fig = crea_grafico_funnel(dati_canale, f"Funnel per {sezione_selezionata}", metriche["Tassi Conversione"])
        st.plotly_chart(fig)

        # Mostra le note
        st.subheader("Note")
        for _, row in dati_canale.iterrows():
            if pd.notna(row["Note"]) and row["Note"].strip():
                st.markdown(f"- **{row['Mese']}**: {row['Note']}")
