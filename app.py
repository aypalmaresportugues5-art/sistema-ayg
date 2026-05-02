import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import urllib.parse

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖")
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbwnn4rvOYQC8G7USLsxQS5dzdyI_5AGZBLXkBlYOOytq0xFP2NkZ-hP3_fPb2c8RY4b/exec"

# --- BASE DE DATOS LOCAL (Se puede conectar al Excel luego) ---
if 'productos' not in st.session_state:
    st.session_state.productos = {
        "CATALINA": 1.30,
        "POLVOROSA": 1.00,
        "PAN DULCE": 2.50,
        "HOJALDRE": 3.00
    }

if 'carro' not in st.session_state:
    st.session_state.carro = []

# --- NAVEGACIÓN ---
st.sidebar.title("🏢 AYG 2017")
menu = st.sidebar.radio("MENÚ", ["Venta Mayor (SAYG)", "Lista de Precios", "Venta Detal", "Cuentas"])

# --- 1. VENTA MAYOR (SAYG) ---
if menu == "Venta Mayor (SAYG)":
    st.header("📦 Pedido Mayorista")
    
    cliente = st.text_input("Nombre del Cliente").upper()
    telefono = st.text_input("Teléfono del Cliente (Ej: 58412...)", help="Sin el +")
    
    col1, col2 = st.columns(2)
    prod_sel = col1.selectbox("Producto", list(st.session_state.productos.keys()))
    cant = col2.number_input("Cantidad", min_value=1, value=20)
    
    if st.button("➕ Agregar al Pedido"):
        precio_u = st.session_state.productos[prod_sel]
        st.session_state.carro.append({
            "Producto": prod_sel, 
            "Cant": cant, 
            "Precio": precio_u, 
            "Subtotal": cant * precio_u
        })

    if st.session_state.carro:
        df = pd.DataFrame(st.session_state.carro)
        st.table(df)
        total = df["Subtotal"].sum()
        st.subheader(f"TOTAL: {total:.2f}$")

        # --- GENERADOR DE TEXTO PARA WHATSAPP ---
        texto_ws = f"*INVERSIONES AYG 2017 C.A.*\n"
        texto_ws += f"━━━━━━━━━━━━━━━━━━\n"
        texto_ws += f"*CLIENTE:* {cliente}\n"
        texto_ws += f"*FECHA:* {datetime.now().strftime('%d/%m/%Y')}\n"
        texto_ws += f"━━━━━━━━━━━━━━━━━━\n"
        for item in st.session_state.carro:
            texto_ws += f"• {item['Producto']} {item['Cant']} * {item['Precio']:.2f}$ = {item['Subtotal']:.2f}$\n"
        texto_ws += f"━━━━━━━━━━━━━━━━━━\n"
        texto_ws += f"*TOTAL A PAGAR: {total:.2f}$*\n"
        texto_ws += f"━━━━━━━━━━━━━━━━━━\n"
        texto_ws += f"_¡Gracias por su compra!_"
        
        # Botón de WhatsApp
        texto_encode = urllib.parse.quote(texto_ws)
        ws_url = f"https://wa.me/{telefono}?text={texto_encode}"
        
        if st.button("📱 ENVIAR RECIBO POR WHATSAPP"):
            st.markdown(f'<a href="{ws_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366;color:white;padding:10px;border-radius:5px;text-align:center;">ABRIR WHATSAPP</div></a>', unsafe_allow_html=True)
            # Aquí también enviamos al Excel
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": "Crédito", "cliente": cliente, "monto": total}
            requests.post(URL_GOOGLE, json=payload)
            st.session_state.carro = []

# --- 2. LISTA DE PRECIOS ---
elif menu == "Lista de Precios":
    st.header("📋 Catálogo de Productos")
    
    # Mostrar tabla actual
    df_precios = pd.DataFrame(list(st.session_state.productos.items()), columns=["Producto", "Precio $"])
    st.table(df_precios)
    
    # Editar o agregar
    with st.expander("Añadir o Editar Producto"):
        n_p = st.text_input("Nombre").upper()
        p_p = st.number_input("Precio $", min_value=0.0, format="%.2f")
        if st.button("Guardar"):
            st.session_state.productos[n_p] = p_p
            st.success("¡Precio actualizado!")
            st.rerun()

# (Las otras secciones se mantienen igual...)
