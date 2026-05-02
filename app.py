import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="SAYG 2017 - Gestión", page_icon="🥖")
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbwnn4rvOYQC8G7USLsxQS5dzdyI_5AGZBLXkBlYOOytq0xFP2NkZ-hP3_fPb2c8RY4b/exec"

# --- FUNCIONES DE DATOS ---
def enviar_datos(datos):
    try:
        res = requests.post(URL_GOOGLE, json=datos, timeout=10)
        return res.text == "OK"
    except: return False

# --- INTERFAZ ---
st.sidebar.title("🏢 AYG 2017")
menu = st.sidebar.radio("Ir a:", ["Venta Detal", "Venta Mayor (SAYG)", "Inventario"])

if menu == "Venta Detal":
    st.header("🏪 Registro de Panadería")
    with st.form("detal"):
        cliente = st.text_input("Cliente", "GENERAL").upper()
        monto = st.number_input("Total $", min_value=0.0)
        pago = st.selectbox("Método", ["Contado", "Crédito"])
        if st.form_submit_button("REGISTRAR"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": pago, "cliente": cliente, "monto": monto}
            if enviar_datos(payload): st.success("¡Venta Guardada!")
            else: st.error("Error de conexión")

elif menu == "Venta Mayor (SAYG)":
    st.header("📦 Sistema de Ventas al Mayor")
    
    # Lista de productos (En el futuro la traeremos del Excel automáticamente)
    productos_lista = ["CATALINAS", "POLVOROSAS", "PAN DULCE", "HOJALDRE"]
    
    cliente_m = st.text_input("Nombre del Cliente").upper()
    col1, col2 = st.columns(2)
    prod_sel = col1.selectbox("Producto", productos_lista)
    cant = col2.number_input("Cantidad", min_value=1)
    
    if st.button("➕ Añadir al pedido"):
        if 'pedido' not in st.session_state: st.session_state.pedido = []
        st.session_state.pedido.append({"Producto": prod_sel, "Cant": cant})

    if 'pedido' in st.session_state and st.session_state.pedido:
        df = pd.DataFrame(st.session_state.pedido)
        st.table(df)
        
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.pedido = []
            st.rerun()
            
        # BOTÓN DE IMPRIMIR (Simulado con texto para copiar/pegar)
        st.subheader("Generar Comprobante")
        ticket_txt = f"INVERSIONES AYG 2017\nCliente: {cliente_m}\nFecha: {datetime.now().strftime('%d/%m/%Y')}\n"
        ticket_txt += "-"*20 + "\n"
        for item in st.session_state.pedido:
            ticket_txt += f"{item['Producto']} x{item['Cant']}\n"
        
        st.download_button("📥 DESCARGAR TICKET (TXT)", ticket_txt, file_name="ticket_ayg.txt")

elif menu == "Inventario":
    st.header("🏗️ Precios y Almacén")
    st.info("Para que la lista de productos se actualice, agrégalos en tu hoja de Google Sheets en la pestaña 'Productos'.")
