import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖")

# Tu URL de Google Apps Script (la misma que usas en Kivy)
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbwnn4rvOYQC8G7USLsxQS5dzdyI_5AGZBLXkBlYOOytq0xFP2NkZ-hP3_fPb2c8RY4b/exec"

# --- INTERFAZ DE USUARIO ---
st.title("🥖 INVERSIONES AYG 2017")

# Menú lateral para navegar
opcion = st.sidebar.selectbox("MENÚ", ["VENTAS", "SAYG (MAYOR)", "CUENTAS", "ALMACÉN"])

if opcion == "VENTAS":
    st.header("🛒 Registro de Ventas (Detal)")
    
    with st.form("form_ventas"):
        cliente = st.text_input("Cliente", value="GENERAL").upper()
        monto = st.number_input("Monto ($)", min_value=0.0, step=0.1, format="%.2f")
        tipo = st.selectbox("Método de Pago", ["Contado", "Crédito"])
        
        btn_registrar = st.form_submit_button("REGISTRAR VENTA")
        
        if btn_registrar:
            payload = {
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tipo": tipo,
                "cliente": cliente,
                "monto": monto
            }
            try:
                res = requests.post(URL_GOOGLE, json=payload, timeout=15)
                if res.text == "OK":
                    st.success(f"✅ ¡Venta de {cliente} por ${monto} registrada!")
                else:
                    st.error(f"❌ Error del servidor: {res.text}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

elif opcion == "SAYG (MAYOR)":
    st.header("📦 Sistema SAYG (Venta al Mayor)")
    st.info("Aquí puedes gestionar facturas más grandes y tickets PDF.")
    # Espacio para la lógica de mayoristas

elif opcion == "CUENTAS":
    st.header("💰 Cuentas por Cobrar")
    if st.button("Sincronizar con Google Sheets"):
        # Lógica para leer deudas actuales
        st.write("Obteniendo deudas...")
