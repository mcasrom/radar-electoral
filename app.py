#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
import io
import os

st.set_page_config(page_title="Radar Electoral 🇪🇸", layout="wide")

# =====================
# Función para cargar datos de manera segura
# =====================
@st.cache_data
def load_data():
    hist_path = "data/hist.csv"
    latest_path = "data/latest.csv"
    if not os.path.exists(hist_path) or not os.path.exists(latest_path):
        st.error("❌ No se encontraron los archivos CSV necesarios en 'data/'.")
        return pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos"]), pd.DataFrame(columns=["Fecha","Provincia","Partido","Votos"])
    
    df_hist = pd.read_csv(hist_path, parse_dates=["Fecha"], dayfirst=True)
    df_latest = pd.read_csv(latest_path, parse_dates=["Fecha"], dayfirst=True)
    
    return df_hist, df_latest

df_hist, df_latest = load_data()

# =====================
# Filtros laterales
# =====================
st.sidebar.title("Filtros")
fecha_sel = st.sidebar.date_input("Fecha", value=date.today())
partido_sel = st.sidebar.multiselect(
    "Partidos", df_latest["Partido"].unique(), df_latest["Partido"].unique()
)
provincia_sel = st.sidebar.multiselect(
    "Provincias", df_latest["Provincia"].unique(), df_latest["Provincia"].unique()
)

# =====================
# Filtrado seguro
# =====================
df_filtered = df_latest[
    (df_latest["Partido"].isin(partido_sel)) &
    (df_latest["Provincia"].isin(provincia_sel)) &
    (df_latest["Fecha"] == pd.to_datetime(fecha_sel))
]

if df_filtered.empty:
    st.warning("⚠️ No hay datos para los filtros seleccionados.")
else:
    # =====================
    # Métricas
    # =====================
    st.title("Radar Electoral 🇪🇸 - Métricas Avanzadas")
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Votos Totales", f"{df_filtered['Votos'].sum():,}")
    col2.metric("Partido Mayoritario", df_filtered.groupby("Partido")["Votos"].sum().idxmax())
    col3.metric("Provincia con más votos", df_filtered.groupby("Provincia")["Votos"].sum().idxmax())
    col4.metric("Número de Partidos", df_filtered["Partido"].nunique())

    # =====================
    # Gráfico de barras
    # =====================
    st.subheader("Distribución de Votos por Partido")
    df_barras = df_filtered.groupby("Partido")["Votos"].sum().reset_index()
    fig_barras = px.bar(df_barras, x="Partido", y="Votos", text="Votos", color="Partido")
    st.plotly_chart(fig_barras, use_container_width=True)

    # =====================
    # Pie hemiciclo
    # =====================
    st.subheader("Hemiciclo Parlamentario")
    df_pie = df_filtered.groupby("Partido")["Votos"].sum().reset_index()
    fig_pie = px.pie(df_pie, names="Partido", values="Votos", color="Partido")
    st.plotly_chart(fig_pie, use_container_width=True)

    # =====================
    # Heatmap provincial
    # =====================
    st.subheader("Heatmap Provincial")
    df_heat = df_filtered.pivot_table(index="Partido", columns="Provincia", values="Votos", aggfunc="sum").fillna(0)
    fig_heat = px.imshow(df_heat, text_auto=True, aspect="auto", color_continuous_scale="Blues")
    st.plotly_chart(fig_heat, use_container_width=True)

    # =====================
    # Evolución temporal
    # =====================
    st.subheader("Evolución Temporal por Partido")
    df_time = df_hist[df_hist["Partido"].isin(partido_sel)]
    df_time = df_time.groupby(["Fecha", "Partido"])["Votos"].sum().reset_index()
    fig_time = px.line(df_time, x="Fecha", y="Votos", color="Partido", markers=True)
    st.plotly_chart(fig_time, use_container_width=True)

    # =====================
    # Export PDF
    # =====================
    def generate_pdf(df):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        story.append(Paragraph("Radar Electoral - Resumen", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Fecha: {fecha_sel}", styles['Normal']))
        story.append(Spacer(1, 12))

        for partido in df["Partido"].unique():
            df_partido = df[df["Partido"]==partido]
            total_votos = df_partido["Votos"].sum()
            story.append(Paragraph(f"{partido}: {total_votos:,} votos", styles['Normal']))
            story.append(Spacer(1, 6))

        doc.build(story)
        buffer.seek(0)
        return buffer

    st.subheader("Exportar PDF")
    if st.button("Generar PDF"):
        pdf_buffer = generate_pdf(df_filtered)
        st.download_button("Descargar PDF", data=pdf_buffer, file_name=f"radar_{fecha_sel}.pdf", mime="application/pdf")

    # =====================
    # Export CSV
    # =====================
    st.subheader("Exportar CSV")
    csv_data = df_filtered.to_csv(index=False)
    st.download_button("Descargar CSV", data=csv_data, file_name=f"radar_{fecha_sel}.csv", mime="text/csv")

st.success("Dashboard cargado correctamente ✅")
