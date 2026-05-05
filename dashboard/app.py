import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Benin Media Intelligence", layout="wide")

# -----------------------------
# 🎨 HEADER DESIGN
# -----------------------------
st.title("📊 Benin Media Intelligence Dashboard")
st.markdown("Analyse des événements GDELT sur le Bénin 🇧🇯")

st.markdown("""
<div style="
    background: linear-gradient(90deg, #0f2027, #203a43, #2c5364);
    padding: 15px;
    border-radius: 10px;
    color: white;
    text-align: center;
    font-size: 18px;
">
📡 Surveillance • 🌍 Analyse • 🧠 Détection de crises
</div>
""", unsafe_allow_html=True)

st.markdown("""
### 🎯 Objectif
Transformer des données médiatiques mondiales en insights utiles pour le Bénin.
""")

# -----------------------------
# 📥 LOAD DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("base_fusionnee.csv")

    df['SQLDATE'] = pd.to_datetime(df['SQLDATE'], errors='coerce')
    df = df.dropna(subset=['SQLDATE'])

    df = df[df['ActionGeo_CountryCode'] == 'BN']

    df['month_year'] = df['SQLDATE'].dt.to_period('M').astype(str)

    for col in ['AvgTone', 'GoldsteinScale', 'NumMentions']:
        df[col] = df[col].fillna(0)

    df['sensitivity_score'] = (-df['AvgTone']) * df['NumMentions'] * abs(df['GoldsteinScale'])

    def classify(q):
        if q == 4:
             return "Conflit matériel"
        elif q == 3:
            return "Conflit verbal"
        elif q == 2:
            return "Coopération matérielle"
        elif q == 1:
            return "Coopération verbale"
        else:
            return "Inconnu"

    df['event_type'] = df['QuadClass'].apply(classify)

    return df

df = load_data()

# -----------------------------
# 🎛️ SIDEBAR
# -----------------------------
st.sidebar.header("🔎 Filtres")

quick_filter = st.sidebar.selectbox(
    "📅 Période rapide",
    ["Personnalisé", "Dernier mois", "3 derniers mois", "6 derniers mois", "1 an"]
)

st.sidebar.subheader("📆 Période personnalisée")

col1, col2 = st.sidebar.columns(2)

min_date = df['SQLDATE'].min()
max_date = df['SQLDATE'].max()

with col1:
    start_date_input = st.date_input("Début", min_date)

with col2:
    end_date_input = st.date_input("Fin", max_date)

event_type = st.sidebar.multiselect(
    "Type d'événement",
    df['event_type'].unique(),
    #default=df['event_type'].unique()
)

max_score = int(df['sensitivity_score'].max())

threshold = st.sidebar.slider(
    "Seuil sensibilité",
    0, max_score, int(max_score * 0.2)
)

# -----------------------------
# 📆 LOGIQUE TEMPORELLE
# -----------------------------
if quick_filter == "Dernier mois":
    start_date = df['SQLDATE'].max() - pd.DateOffset(months=1)
    end_date = df['SQLDATE'].max()

elif quick_filter == "3 derniers mois":
    start_date = df['SQLDATE'].max() - pd.DateOffset(months=3)
    end_date = df['SQLDATE'].max()

elif quick_filter == "6 derniers mois":
    start_date = df['SQLDATE'].max() - pd.DateOffset(months=6)
    end_date = df['SQLDATE'].max()

elif quick_filter == "1 an":
    start_date = df['SQLDATE'].max() - pd.DateOffset(years=1)
    end_date = df['SQLDATE'].max()

else:
    start_date = pd.to_datetime(start_date_input)
    end_date = pd.to_datetime(end_date_input)

# -----------------------------
# 🔎 FILTRAGE
# -----------------------------
filtered_df = df[
    (df['SQLDATE'] >= start_date) &
    (df['SQLDATE'] <= end_date) &
    (df['event_type'].isin(event_type)) &
    (df['sensitivity_score'] >= threshold)
]

if filtered_df.empty:
    st.warning("Aucune donnée pour cette sélection")
    st.stop()

# -----------------------------
# 📊 KPI
# -----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("📊 Événements", len(filtered_df))
col2.metric("🌡️ Sentiment", f"{filtered_df['AvgTone'].mean():.2f}")
col3.metric("🧨 Intensité", f"{filtered_df['sensitivity_score'].max():.0f}")

# -----------------------------
# 📈 ÉVOLUTION
# -----------------------------
st.subheader("📈 Dynamique médiatique")

events_time = filtered_df.groupby('month_year').size().reset_index(name='count')
fig1 = px.line(events_time, x='month_year', y='count', markers=True)
st.plotly_chart(fig1, use_container_width=True)

# -----------------------------
# 🌡️ IMAGE
# -----------------------------
st.subheader("🌡️ Image du Bénin")

tone_time = filtered_df.groupby('month_year')['AvgTone'].mean().reset_index()
fig2 = px.line(tone_time, x='month_year', y='AvgTone', markers=True)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("🔵 Positif | ⚪ Neutre | 🔴 Négatif")

# Insight automatique
avg_tone = filtered_df['AvgTone'].mean()

if avg_tone < -2:
    st.error("🔴 Image globalement négative")
elif avg_tone < 1:
    st.warning("🟠 Image globalement neutre")
else:
    st.success("🟢 Image globalement positive")

# -----------------------------
# 🧨 STORYTELLING
# -----------------------------
st.subheader("🧨 Événements critiques")

top_events = filtered_df.sort_values(
    by='sensitivity_score', ascending=False
).drop_duplicates(subset=['SOURCEURL']).head(5)

st.success(f"{len(top_events)} événements critiques détectés")

def interpret_event(tone):
    if tone < -8:
        return "🔴 Situation critique"
    elif tone < -3:
        return "🟠 Tension modérée"
    else:
        return "🟢 Situation stable"

for _, row in top_events.iterrows():
    interpretation = interpret_event(row['AvgTone'])

    st.markdown(f"""
    ---
    ### 📰 {row['Actor1Name']} vs {row['Actor2Name']}

    📅 **Date :** {row['SQLDATE'].date()}  
    🌡️ **Sentiment :** {round(row['AvgTone'],2)}  
    🗞️ **Couverture :** {int(row['NumMentions'])} mentions  
    ⚠️ **Analyse :** {interpretation}

    🔗 [Lire l'article]({row['SOURCEURL']})
    """)

# -----------------------------
# 👥 ACTEURS
# -----------------------------
st.subheader("👥 Acteurs dominants")

top_actors = filtered_df['Actor1Name'].value_counts().head(10).reset_index()
top_actors.columns = ['Actor', 'Count']

fig3 = px.bar(top_actors, x='Actor', y='Count')
st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# 🌍 CARTE
# -----------------------------
st.subheader("🌍 Répartition géographique")

geo_df = filtered_df.dropna(subset=['ActionGeo_Lat','ActionGeo_Long'])

if not geo_df.empty:
    fig4 = px.scatter_mapbox(
        geo_df,
        lat="ActionGeo_Lat",
        lon="ActionGeo_Long",
        hover_name="Actor1Name",
        zoom=6
    )
    fig4.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.warning("Pas de données géographiques disponibles")