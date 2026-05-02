import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖", layout="centered")
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbwnn4rvOYQC8G7USLsxQS5dzdyI_5AGZBLXkBlYOOytq0xFP2NkZ-hP3_fPb2c8RY4b/exec"

# --- ESTILOS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DE LA APP ---
if 'carrito' not in st.session_state: st.session_state.carrito = []

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["VENTA DETAL", "SAYG (MAYOR)", "ALMACÉN", "CUENTAS"])

# --- 1. VENTA DETAL (PANADERÍA) ---
if menu == "VENTA DETAL":
    st.header("🏪 Ventas al Detal")
    with st.form("detal"):
        cli = st.text_input("Cliente", value="GENERAL").upper()
        monto = st.number_input("Monto total $", min_value=0.0, format="%.2f")
        tipo = st.selectbox("Condición", ["Contado", "Crédito"])
        if st.form_submit_button("REGISTRAR VENTA"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "tipo": tipo, "cliente": cli, "monto": monto}
            res = requests.post(URL_GOOGLE, json=payload)
            if res.text == "OK": st.success("✅ Guardado en Google Sheets")
            else: st.error("Error al guardar")

# --- 2. SAYG (MAYORISTA) ---
elif menu == "SAYG (MAYOR)":
    st.header("📦 Sistema SAYG - Mayor")
    cli_m = st.text_input("Cliente Mayorista").upper()
    
    col1, col2 = st.columns(2)
    prod = col1.text_input("Producto")
    cant = col2.number_input("Cant", min_value=1)
    precio = st.number_input("Precio Unitario $", min_value=0.0)
    
    if st.button("➕ AGREGAR AL CARRITO"):
        st.session_state.carrito.append({"Producto": prod, "Cant": cant, "Precio": precio, "Subtotal": cant*precio})

    if st.session_state.carrito:
        df = pd.DataFrame(st.session_state.carrito)
        st.table(df)
        total = df["Subtotal"].sum()
        st.subheader(f"TOTAL A FACTURAR: ${total:.2f}")
        
        if st.button("🚀 FINALIZAR Y ENVIAR"):
            # Aquí enviamos el total al Excel
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "tipo": "Crédito", "cliente": cli_m, "monto": total}
            requests.post(URL_GOOGLE, json=payload)
            st.session_state.carrito = []
            st.success("Factura registrada")
            st.balloons()

# --- 3. ALMACÉN ---
elif menu == "ALMACÉN":
    st.header("🏗️ Gestión de Inventario")
    # Formulario para actualizar precios
    with st.expander("Añadir / Editar Producto"):
        n_prod = st.text_input("Nombre del Producto").upper()
        n_pree = st.number_input("Precio $", min_value=0.0)
        if st.button("Guardar en Almacén"):
            st.info(f"Producto {n_prod} actualizado localmente")

# --- 4. CUENTAS ---
elif menu == "CUENTAS":
    st.header("💰 Cuentas por Cobrar")
    if st.button("🔄 Sincronizar Deudas"):
        try:
            res = requests.post(URL_GOOGLE, json={"accion": "leer_deudas"})
            deudas = res.json()
            st.table(pd.DataFrame(list(deudas.items()), columns=["Cliente", "Deuda $"]))
        except:
            st.warning("No se pudieron cargar las deudas. Revisa la conexión.")
