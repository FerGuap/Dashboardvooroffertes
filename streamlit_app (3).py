
import streamlit as st
import pandas as pd
import altair as alt

# Zet pagina-instellingen bovenaan
st.set_page_config(page_title="Offerteconversie Dashboard", layout="wide")

# Laad dataset met caching
@st.cache_data
def load_data():
    df = pd.read_csv("dashboard_data.csv", parse_dates=["Aanmaakdatum"])
    return df

df = load_data()

# TITEL EN INLEIDING
st.title("Offerteconversie Dashboard - REZ")
st.markdown("Interactief overzicht van offertes, conversieratio's, marges en modelvoorspellingen.")

# FILTERS
col1, col2, col3 = st.columns(3)
with col1:
    verkopers = df["Verkoper"].dropna().unique().tolist()
    selected_verkopers = st.multiselect("Selecteer verkoper(s)", verkopers, default=verkopers)
with col2:
    klanten = df["klant"].dropna().unique().tolist()
    selected_klanten = st.multiselect("Selecteer klant(en)", klanten, default=klanten)
with col3:
    min_date = df["Aanmaakdatum"].min().date()
    max_date = df["Aanmaakdatum"].max().date()
    selected_dates = st.date_input("Selecteer periode", [min_date, max_date], min_value=min_date, max_value=max_date)

# ZET DATUMEN OM
start_date = pd.to_datetime(selected_dates[0])
end_date = pd.to_datetime(selected_dates[1])

# FILTERING
mask = (
    df["Verkoper"].isin(selected_verkopers) &
    df["klant"].isin(selected_klanten) &
    df["Aanmaakdatum"].between(start_date, end_date)
)
filtered_df = df.loc[mask].copy()

# CHECK: DATA AANWEZIG?
if filtered_df.empty:
    st.warning("Geen gegevens beschikbaar voor de gekozen filters.")
    st.stop()

# KPI TEGELS
total = len(filtered_df)
converted = (filtered_df["voorspelling"] == "Conversie").sum()
ratio = converted / total if total > 0 else 0
avg_value = filtered_df["Totaal"].mean()
avg_prob = filtered_df["zekerheid_conversie"].mean()

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Aantal Offertes", f"{total}")
kpi2.metric("Conversieratio", f"{ratio:.0%}")
kpi3.metric("Gemiddelde Waarde", f"€ {avg_value:,.2f}")
kpi4.metric("Gem. Kans (Model)", f"{avg_prob:.0%}")

# GRAFIEK 1: Conversieratio per maand
st.markdown("### Conversieratio per maand")
monthly_df = (
    filtered_df
    .groupby(pd.Grouper(key="Aanmaakdatum", freq="M"))
    .agg(Conversieratio=("voorspelling", lambda x: (x == "Conversie").mean()))
    .reset_index()
)

line = alt.Chart(monthly_df).mark_line(point=True).encode(
    x=alt.X("Aanmaakdatum:T", title="Maand"),
    y=alt.Y("Conversieratio:Q", title="Conversieratio"),
    tooltip=[alt.Tooltip("Aanmaakdatum:T"), alt.Tooltip("Conversieratio:Q", format=".0%")]
).properties(width=750, height=300)

st.altair_chart(line, use_container_width=True)

# GRAFIEK 2: Kans op conversie vs. Marge %
st.markdown("### Offertes: Kans op conversie vs. Marge %")
scatter = alt.Chart(filtered_df).mark_circle(size=60, opacity=0.6).encode(
    x=alt.X("marge_%:Q", title="Marge %"),
    y=alt.Y("zekerheid_conversie:Q", title="Kans op conversie"),
    color="Verkoper:N",
    tooltip=["klant", "Totaal", "marge_%", "zekerheid_conversie"]
).interactive().properties(width=750, height=400)

st.altair_chart(scatter, use_container_width=True)
