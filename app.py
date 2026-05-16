import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
from datetime import datetime
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖", layout="centered")

# --- CONEXIÓN CON TU EXCEL (URL QUE ME PASASTE) ---
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbxoXYuo0IkMCmEHKKWEnecUfQs7dZlm7604eaVV3ep0GrgxInveg_Me-AyjJjxYhfVR/exec"

# --- SISTEMA DE SEGURIDAD ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if not st.session_state.password_correct:
        st.image("1000323326.png.png", width=200) # Tu logo circular
        st.title("🔐 Acceso Privado - AYG 2017")
        password = st.text_input("Introduce la clave del sistema", type="password")
        if st.button("ENTRAR"):
            if password == "AYG2026": # <--- Tu clave de acceso
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("❌ Clave incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- CARGA DE DATOS DESDE EL EXCEL ---
@st.cache_data(ttl=60) # Actualiza los datos cada minuto
def cargar_datos_vivos():
    try:
        r = requests.get(URL_GOOGLE)
        return r.json()
    except:
        return {"clientes": ["GENERAL"], "productos": {"CATALINA": {"precio": 1.30, "stock": 0}}}

datos = cargar_datos_vivos()
clientes_lista = datos['clientes']
productos_dict = datos['productos']

# --- FUNCIÓN GENERADORA DE PDF SEGURO ---
def crear_pdf(cliente, pedido, total):
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

# --- DISEÑO DE LA APP ---
st.image("1000317144.jpg.png", use_container_width=True) # Tu logo rectangular
    # --- AQUÍ EMPIEZA EL NUEVO MENÚ PREMIUM ---
    st.write("---") # Línea divisoria elegante en la barra lateral
    
    # Creamos el menú moderno con sus íconos
    menu = option_menu(
        menu_title="MENÚ AYG 2017",
        options=["Venta Detal", "Venta Mayor (SAYG)", "Cuentas y Abonos", "Inventario", "Cuentas por Cobrar"],
        icons=["shop", "truck", "wallet2", "box-seam", "cash-stack"], 
        menu_icon="building-gear", 
        default_index=0, 
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa", "border-radius": "10px"},
            "icon": {"color": "#FF4B4B", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "border-radius": "8px"},
            "nav-link-selected": {"background-color": "#FF4B4B", "color": "white", "font-weight": "bold"},
        }
    )
    # --- AQUÍ TERMINA EL MENÚ ---

# 1. VENTA DETAL
if menu == "Venta Detal":
    st.header("🏪 Venta Rápida (Detal)")
    with st.form("detal"):
        c = st.selectbox("Cliente", clientes_lista)
        m = st.number_input("Monto Total $", min_value=0.0)
        cond = st.selectbox("Condición", ["Contado", "Crédito"])
        if st.form_submit_button("REGISTRAR VENTA"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": cond, "cliente": c, "monto": m}
            requests.post(URL_GOOGLE, json=payload)
            st.success("✅ Venta guardada")

# 2. VENTA MAYOR (SAYG)
elif menu == "Venta Mayor (SAYG)":
    st.header("📦 Pedido al Mayor")
    cli_m = st.selectbox("Seleccionar Cliente", clientes_lista)
    
    col1, col2 = st.columns(2)
    prod_nom = col1.selectbox("Producto", list(productos_dict.keys()))
    stock_actual = productos_dict[prod_nom]['stock']
    precio_u = productos_dict[prod_nom]['precio']
    
    st.info(f"💰 Precio: {precio_u}$ | 📦 Stock: {stock_actual}")
    cant = col2.number_input("Cantidad", min_value=1, max_value=int(stock_actual) if stock_actual > 0 else 1)
    
    if st.button("➕ Agregar al Carrito"):
        if 'carro' not in st.session_state: st.session_state.carro = []
        st.session_state.carro.append({"Producto": prod_nom, "Cant": cant, "Precio": precio_u, "Subtotal": cant * precio_u})

    if 'carro' in st.session_state and st.session_state.carro:
        st.table(pd.DataFrame(st.session_state.carro))
        t_final = sum(i['Subtotal'] for i in st.session_state.carro)
        st.subheader(f"Total: {t_final:.2f}$")
    # Botón para borrar todo y empezar de nuevo si hay un error
        if st.button("🗑️ Vaciar Carrito"):
            st.session_state.carro = []
            st.rerun()
        if st.button("🔒 FINALIZAR Y CREAR PDF"):
            payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": "Crédito", "cliente": cli_m, "monto": t_final}
            requests.post(URL_GOOGLE, json=payload)
            pdf_b = crear_pdf(cli_m, st.session_state.carro, t_final)
            b64 = base64.b64encode(pdf_b).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Factura_{cli_m}.pdf" style="padding:10px;background-color:#FF4B4B;color:white;text-decoration:none;border-radius:5px;">📥 DESCARGAR FACTURA PDF</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.session_state.carro = []

# 3. CUENTAS Y ABONOS
elif menu == "Cuentas y Abonos":
    st.header("💰 Registro de Abonos")
    cli_a = st.selectbox("Cliente", clientes_lista)
    monto_a = st.number_input("Monto del Abono $", min_value=0.0)
    if st.button("REGISTRAR ABONO"):
        payload = {"fecha": datetime.now().strftime("%d/%m/%Y"), "tipo": "Abono", "cliente": cli_a, "monto": -monto_a}
        requests.post(URL_GOOGLE, json=payload)
        st.success(f"✅ Abono de {monto_a}$ registrado")

# 4. INVENTARIO
elif menu == "Inventario":
    st.header("📦 Estado del Almacén")
    df_inv = pd.DataFrame([{"Producto": k, "Precio": v['precio'], "Stock": v['stock']} for k,v in productos_dict.items()])
    st.table(df_inv)
    st.write("🟢 Las cantidades se actualizan según las Entradas/Salidas de tu Excel.")
# --- 5. CUENTAS POR COBRAR ---
elif menu == "Cuentas por Cobrar":
    st.header("📊 Resumen de Deudas")
    
    # 1. Pedimos los datos a Google
    resp = requests.get(f"{URL_GOOGLE}?tipo=Ventas")
    datos_recibidos = resp.json()
    
    if isinstance(datos_recibidos, list):
        df_v = pd.DataFrame(datos_recibidos)
    else:
        df_v = pd.DataFrame()

    if not df_v.empty:
        # --- SECCIÓN NUEVA: TOTAL GLOBAL (DINERO EN LA CALLE) ---
        # Sumamos todos los créditos y abonos de la hoja
        global_deuda = df_v[df_v['TIPO'] == 'Crédito']['MONTO($)'].sum()
        global_abonos = df_v[df_v['TIPO'] == 'Abono']['MONTO($)'].sum()
        total_en_calle = global_deuda + global_abonos
        
        st.subheader("💰 Capital Total por Cobrar")
        st.info(f"Actualmente tienes un total de **${total_en_calle:.2f}** distribuidos entre todos tus clientes.")
        st.divider() 

        # --- SECCIÓN DETALLE POR CLIENTE ---
        if clientes_lista:
            cliente_sel = st.selectbox("Ver detalle de un cliente específico:", clientes_lista)
            
            # Filtramos solo lo de este cliente
            df_cli = df_v[df_v['CLIENTE'] == cliente_sel]
            
            total_deuda = df_cli[df_cli['TIPO'] == 'Crédito']['MONTO($)'].sum()
            total_abonos = df_cli[df_cli['TIPO'] == 'Abono']['MONTO($)'].sum()
            saldo = total_deuda + total_abonos # Usamos + porque el abono es negativo
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Fiado", f"${total_deuda:.2f}")
            c2.metric("Total Pagado", f"${total_abonos:.2f}")
            c3.metric("SALDO PENDIENTE", f"${saldo:.2f}", delta_color="inverse")
            
            if saldo > 0:
                st.error(f"🔴 Este cliente debe ${saldo:.2f}")
            else:
                st.success("🟢 Este cliente está al día.")
    else:
        st.info("No hay registros de ventas para calcular.")

