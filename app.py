import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖", layout="wide")

# URL de tu Google Apps Script (la que ya tienes conectada a tu Excel)
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbwnn4rvOYQC8G7USLsxQS5dzdyI_5AGZBLXkBlYOOytq0xFP2NkZ-hP3_fPb2c8RY4b/exec"

# --- INICIALIZACIÓN DE DATOS ---
if 'productos' not in st.session_state:
    st.session_state.productos = {"CATALINA": 1.30, "POLVOROSA": 1.00, "PAN DULCE": 2.50, "HOJALDRE": 3.00}
if 'clientes' not in st.session_state:
    st.session_state.clientes = ["GENERAL", "ABASTO EL SOL", "CLIENTE EJEMPLO"]
if 'carro' not in st.session_state:
    st.session_state.carro = []

# --- FUNCIÓN GENERADORA DE PDF ---
def crear_pdf_factura(cliente, pedido, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "INVERSIONES AYG 2017 C.A.", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, "RIF: J-40982649-7 | Barquisimeto, Edo. Lara", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"FACTURA DE VENTA - {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    pdf.cell(0, 10, f"CLIENTE: {cliente}", ln=True)
    pdf.ln(5)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, "PRODUCTO", 1, 0, 'C', True)
    pdf.cell(30, 10, "CANT", 1, 0, 'C', True)
    pdf.cell(40, 10, "PRECIO U.", 1, 0, 'C', True)
    pdf.cell(40, 10, "SUBTOTAL", 1, 1, 'C', True)
    pdf.set_font("Arial", '', 11)
    for item in pedido:
        pdf.cell(80, 10, item['Producto'], 1)
        pdf.cell(30, 10, str(item['Cant']), 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Precio']:.2f}$", 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Subtotal']:.2f}$", 1, 1, 'C')
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(150, 10, "TOTAL A PAGAR:", 0, 0, 'R')
    pdf.cell(40, 10, f"{total:.2f}$", 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- MENÚ LATERAL ---
st.sidebar.title("🏢 Sistema AYG 2017")
menu = st.sidebar.selectbox("Ir a:", ["Venta Detal", "Venta Mayor (SAYG)", "Cuentas por Cobrar", "Lista de Precios", "Clientes e Inventario"])

# --- 1. VENTA DETAL ---
if menu == "Venta Detal":
    st.header("🏪 Registro de Panadería (Detal)")
    with st.form("form_detal"):
        cli = st.selectbox("Cliente", st.session_state.clientes)
        monto = st.number_input("Total Venta $", min_value=0.0, format="%.2f")
        metodo = st.selectbox("Condición", ["Contado", "Crédito"])
        if st.form_submit_button("REGISTRAR"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": metodo, "cliente": cli, "monto": monto}
            requests.post(URL_GOOGLE, json=payload)
            st.success(f"Venta de {cli} guardada en Excel")

# --- 2. VENTA MAYOR (SAYG) CON PDF ---
elif menu == "Venta Mayor (SAYG)":
    st.header("📦 Sistema de Ventas al Mayor")
    c_m = st.selectbox("Cliente Mayorista", st.session_state.clientes)
    col1, col2 = st.columns(2)
    p_sel = col1.selectbox("Producto", list(st.session_state.productos.keys()))
    cant = col2.number_input("Cantidad", min_value=1, value=20)
    
    if st.button("➕ Añadir al Pedido"):
        p_u = st.session_state.productos[p_sel]
        st.session_state.carro.append({"Producto": p_sel, "Cant": cant, "Precio": p_u, "Subtotal": cant * p_u})

    if st.session_state.carro:
        df_c = pd.DataFrame(st.session_state.carro)
        st.table(df_c)
        total_m = df_c["Subtotal"].sum()
        st.subheader(f"Total: {total_m:.2f}$")
        
        if st.button("🔒 GENERAR FACTURA PDF Y GUARDAR"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": "Crédito", "cliente": c_m, "monto": total_m}
            requests.post(URL_GOOGLE, json=payload)
            pdf_bytes = crear_pdf_factura(c_m, st.session_state.carro, total_m)
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Factura_{c_m}.pdf" style="padding:10px;background-color:#FF4B4B;color:white;text-decoration:none;border-radius:5px;">📥 DESCARGAR PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.session_state.carro = []

# --- 3. CUENTAS POR COBRAR Y ABONOS ---
elif menu == "Cuentas por Cobrar":
    st.header("💰 Control de Deudas y Abonos")
    cli_deuda = st.selectbox("Consultar Cliente", st.session_state.clientes)
    # [span_0](start_span)Aquí puedes conectar la lógica para sumar créditos del Excel[span_0](end_span)
    st.info("Sincronizado con: Ventas Inversiones AYG 2017 - Reporte Filtrable")
    
    with st.expander("Registrar Abono"):
        m_abono = st.number_input("Monto del Abono $", min_value=0.0)
        if st.button("Guardar Abono"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": "ABONO", "cliente": cli_deuda, "monto": -m_abono}
            requests.post(URL_GOOGLE, json=payload)
            st.success(f"Abono de {m_abono}$ registrado exitosamente")

# --- 4. LISTA DE PRECIOS ---
elif menu == "Lista de Precios":
    st.header("📋 Precios Vigentes")
    df_p = pd.DataFrame(list(st.session_state.productos.items()), columns=["Producto", "Precio $"])
    st.table(df_p)
    with st.expander("Actualizar Precio"):
        prod_u = st.selectbox("Producto a editar", list(st.session_state.productos.keys()))
        nuevo_p = st.number_input("Nuevo Precio $", value=st.session_state.productos[prod_u])
        if st.button("Actualizar"):
            st.session_state.productos[prod_u] = nuevo_p
            st.rerun()

# --- 5. CLIENTES E INVENTARIO ---
elif menu == "Clientes e Inventario":
    st.header("👥 Gestión de Base de Datos")
    new_c = st.text_input("Nuevo Cliente").upper()
    if st.button("Añadir Cliente"):
        st.session_state.clientes.append(new_c)
        st.success(f"Cliente {new_c} añadido")
