import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import requests
from datetime import datetime
import pytz
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inversiones AYG 2017", page_icon="🥖", layout="centered")

# --- CONEXIÓN CON TU EXCEL (URL QUE ME PASASTE) ---
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbxoXYuo0IkMCmEHKKWEnecUfQs7dZlm7604eaVV3ep0GrgxInveg_Me-AyjJjxYhfVR/exec"

# --- SISTEMA DE SEGURIDAD ---
def check_password():
    # Inicializamos la sesión directo en Verdadero para que entres sin clave
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = True
    return True

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
st.image("1000317144.jpg.png", use_container_width=True)

with st.sidebar:
    st.write("---") # Línea divisoria elegante
    
    # Creamos el menú moderno con sus íconos
    menu = option_menu(
        menu_title="MENÚ AYG 2017",
        options=["Venta Detal", "Venta Mayor (SAYG)", "Cuentas y Abonos", "Inventario", "Cuentas por Cobrar", "Cierre de Caja"],
        icons=["shop", "truck", "wallet2", "box-seam", "cash-stack"], 
        menu_icon="building-gear", 
        default_index=0, 
        styles={
            "container": {"padding": "5px", "background-color": "#f8f9fa", "border-radius": "10px"},
            "icon": {"color": "#FF4B4B", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "border-radius": "8px","color": "#1e1e1e"},
            "nav-link-selected": {"background-color": "#FF4B4B", "color": "white", "font-weight": "bold"},
        }
    )

# 1. VENTA DETAL
if menu == "Venta Detal":
    st.header("🏪 Venta Rápida (Detal)")
    with st.form("detal"):
        c = st.selectbox("Cliente", clientes_lista)
        m = st.number_input("Monto Total $", min_value=0.0)
        cond = st.selectbox("Condición", ["Contado", "Crédito"])
        if st.form_submit_button("REGISTRAR VENTA"):
              zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime("%d/%m/%Y")
            payload = {"fecha": fecha_ve, "tipo": cond, "cliente": c, "monto": m}
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
            zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime("%d/%m/%Y")
            payload = {"fecha": fecha_ve, "tipo": "Crédito", "cliente": cli_m, "monto": t_final}
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
        zona_ve = pytz.timezone('America/Caracas')
        fecha_ve = datetime.now(zona_ve).strftime("%d/%m/%Y")
        payload = {"fecha": fecha_ve, "tipo": "Abono", "cliente": cli_a, "monto": -monto_a}
        requests.post(URL_GOOGLE, json=payload)
        st.success(f"✅ Abono de {monto_a}$ registrado")
        
# # 4. INVENTARIO
elif menu == "Inventario":
    st.header("📦 Gestión de Almacén, Costos y Registros")
    
    # Creamos las 4 pestañas para organizar todo sin amontonar el teléfono
    tab_almacen, tab_insumos, tab_productos, tab_clientes = st.tabs([
        "📋 Estado del Almacén",
        "🍎 Materia Prima", 
        "🥖 Nuevos Productos", 
        "🤝 Nuevos Clientes"
    ])
    
    # ---------------------------------------------------------------------
    # PESTAÑA 1: TU TABLA ORIGINAL (ESTADO DEL ALMACÉN)
    # ---------------------------------------------------------------------
    with tab_almacen:
        st.subheader("📦 Estado del Almacén")
        # Tu fórmula original exacta adaptada a la pestaña
        if 'productos_dict' in locals() or 'productos_dict' in globals():
            df_inv = pd.DataFrame([{"Producto": k, "Precio": f"{v['precio']:.4f}", "Stock": v['stock']} for k,v in productos_dict.items()])
            st.table(df_inv)
        else:
            st.info("Cargando datos del almacén...")
        st.write("🟢 Las cantidades se actualizan según las Entradas/Salidas de tu Excel.")

    # ---------------------------------------------------------------------
    # PESTAÑA 2: REGISTRO DE MATERIA PRIMA (COSTOS)
    # ---------------------------------------------------------------------
    with tab_insumos:
        st.subheader("🛒 Registro de Costo de Insumos")
        
        with st.form("form_costos", clear_on_submit=True):
            insumo = st.text_input("Nombre del Insumo:", placeholder="Ej: Harina de Trigo, Manteca, Azúcar")
            costo_compra = st.number_input("Costo Total de Compra ($):", min_value=0.0, step=0.01, format="%.2f")
            presentacion = st.text_input("Presentación / Empaque:", placeholder="Ej: Saco, Bulto, Caja, Litro")
            unidad_medida = st.number_input("Cantidad total en Unidades (Kg o Lt):", min_value=0.0, step=0.01, format="%.2f")
            
            btn_guardar_costo = st.form_submit_button("Guardar Insumo")
            
        if btn_guardar_costo:
            if insumo and costo_compra > 0 and unidad_medida > 0:
                costo_por_unidad = round(costo_compra / unidad_medida, 4)
                
                payload = {
                    "accion": "guardar_costo",
                    "insumo": insumo,
                    "costo": costo_compra,
                    "presentacion": presentacion,
                    "unidad": unidad_medida,
                    "costo_unidad": costo_por_unidad
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_COSTO":
                        st.success(f"🟢 ¡{insumo} guardado! Costo calculado: ${costo_por_unidad:.4f} por Kg/Lt.")
                    else:
                        st.error(f"❌ Error del servidor: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Por favor, rellene todos los campos con valores mayores a cero.")

    # ---------------------------------------------------------------------
    # PESTAÑA 3: REGISTRO DE NUEVOS PRODUCTOS
    # ---------------------------------------------------------------------
    with tab_productos:
        st.subheader("✨ Agregar Nuevo Producto al Sistema")
        
        with st.form("form_productos", clear_on_submit=True):
            nuevo_prod = st.text_input("Nombre del Producto:", placeholder="Ej: Pan Canilla, Pan de Tunja, Pan de Guayaba")
            p_detal = st.number_input("Precio de Venta Detal ($):", min_value=0.0, step=0.01, format="%.2f")
            p_mayor = st.number_input("Precio de Venta Mayor ($):", min_value=0.0, step=0.01, format="%.2f")
            
            btn_guardar_prod = st.form_submit_button("Registrar Producto")
            
        if btn_guardar_prod:
            if nuevo_prod and p_detal > 0 and p_mayor > 0:
                payload = {
                    "accion": "guardar_producto",
                    "nombre_producto": nuevo_prod,
                    "precio_detal": p_detal,
                    "precio_mayor": p_mayor
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_PRODUCTO":
                        st.success(f"🟢 ¡Producto '{nuevo_prod}' registrado con éxito!")
                        st.info("💡 Reinicia o refresca la app para que aparezca en tus listas de venta.")
                    else:
                        st.error(f"❌ Error: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Ingresa el nombre del producto y sus precios válidos.")

    # ---------------------------------------------------------------------
    # PESTAÑA 4: REGISTRO DE NUEVOS CLIENTES
    # ---------------------------------------------------------------------
    with tab_clientes:
        st.subheader("🤝 Registrar Nuevo Cliente / Bodega")
        
        with st.form("form_clientes", clear_on_submit=True):
            nuevo_cliente = st.text_input("Nombre completo del Cliente o Bodega:", placeholder="Ej: Bodega Ereau, Cliente Nuevo")
            btn_guardar_cliente = st.form_submit_button("Registrar Cliente")
            
        if btn_guardar_cliente:
            if nuevo_cliente:
                payload = {
                    "accion": "guardar_cliente",
                    "nombre_cliente": nuevo_cliente
                }
                
                try:
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_CLIENTE":
                        st.success(f"🟢 ¡Cliente '{nuevo_cliente}' guardado correctamente!")
                        st.info("💡 Refresca la app para que figure en la lista de deudores.")
                    else:
                        st.error(f"❌ Error: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Por favor, escribe un nombre válido.")
 
# --- 5. CUENTAS POR COBRAR ---
elif menu == "Cuentas por Cobrar":
    st.header("📊 Resumen de Deudas Activas")
    
    # 1. Pedimos los datos a Google Sheets
    resp = requests.get(f"{URL_GOOGLE}?tipo=Ventas")
    datos_recibidos = resp.json()
    
    if isinstance(datos_recibidos, list):
        df_v = pd.DataFrame(datos_recibidos)
    else:
        df_v = pd.DataFrame()

    if not df_v.empty:
        # --- CÁLCULO DEL DINERO TOTAL REAL EN LA CALLE ---
        gran_total_en_calle = 0.0
        if clientes_lista:
            for c in clientes_lista:
                df_c = df_v[df_v['CLIENTE'] == c]
                # Saldo histórico total neto de este cliente
                saldo_historico = df_c['MONTO($)'].sum()
                if saldo_historico > 0:
                    gran_total_en_calle += saldo_historico

        st.subheader("💰 Capital Total por Cobrar")
        st.info(f"Actualmente tienes un total de **${gran_total_en_calle:.2f}** en la calle (solo deudas vigentes).")
        st.divider() 

        # --- SECCIÓN DETALLE POR CLIENTE ---
        if clientes_lista:
            cliente_sel = st.selectbox("Ver deudor específico:", clientes_lista)
            
            # Filtramos los movimientos del cliente seleccionado
            df_cli = df_v[df_v['CLIENTE'] == cliente_sel].copy()
            
                    # Calculamos el saldo real neto de toda su historia redondeado
        saldo_real_neto = round(df_cli['MONTO($)'].sum(), 2)

        # === EVALUAMOS SI DEBE O ESTÁ AL DÍA ===
        if saldo_real_neto <= 0.01:
            # SI ESTÁ AL DÍA: Forzamos todo a cero limpio y barra verde
            c1, c2 = st.columns(2)
            c1.metric("TOTAL ABONADO (DEUDA ACTUAL)", "$0.00")
            c2.metric("SALDO PENDIENTE NETO", "$0.00")
            st.write("---")
            st.success("🟢 Este cliente está al día. Ambos marcadores están en $0.00")
            
        else:
            # SI DEBE: Aislamos únicamente el último ciclo de deuda activa
            movimientos_cliente = df_cli.to_dict('records')
            historial_ciclo_activo = []
            saldo_acumulado_inverso = 0.0
            
            # Recorremos de lo más nuevo a lo más viejo
            for mov in reversed(movimientos_cliente):
                monto = float(mov['MONTO($)'])
                saldo_acumulado_inverso += monto
                historial_ciclo_activo.append(mov)
                
                # Si ya sumamos lo suficiente para cubrir la deuda actual, paramos
                if saldo_acumulado_inverso >= saldo_real_neto:
                    break
            
            # Calculamos los abonos reales del ciclo que quedó abierto
            total_abonos_ciclo = sum(float(n['MONTO($)']) for n in historial_ciclo_activo if n['TIPO'] == 'Abono')
            abonos_mostrar = abs(total_abonos_ciclo)
            
            # --- INTERFAZ EN COLUMNAS ---
            c1, c2 = st.columns(2)
            c1.metric("TOTAL ABONADO (DEUDA ACTUAL)", f"${abonos_mostrar:.2f}")
            c2.metric("SALDO PENDIENTE NETO", f"${saldo_real_neto:.2f}")
            st.write("---")
            
            st.error(f"🔴 Este cliente tiene una cuenta activa por ${saldo_real_neto:.2f}")
            st.write("**Detalle de movimientos de la cuenta vigente:**")
            
            # Mostramos la tabla limpia en pantalla
            df_mostrar = pd.DataFrame(historial_ciclo_activo)[['FECHA', 'TIPO', 'MONTO($)']]
            df_mostrar = df_mostrar.iloc[::-1]
            st.table(df_mostrar)

               
    
# --- 6. CIERRE DE CAJA ---
elif menu == "Cierre de Caja":
        st.header("🗄️ Control y Cierre de Caja Diario")
        
        # Pedimos los movimientos de ventas del dia actual
        resp = requests.get(f"{URL_GOOGLE}?tipo=Ventas")
        datos_recibidos = resp.json()
        
        if isinstance(datos_recibidos, list):
            df_v = pd.DataFrame(datos_recibidos)
        else:
            df_v = pd.DataFrame()
            
        # === AJUSTE DE FECHA ===
        fecha_hoy = datetime.now().strftime('%Y-%m-%d')
        st.subheader(f"Resumen de Operaciones: {fecha_hoy}")
        
        if not df_v.empty:
            # Forzamos la limpieza de la fecha para tomar solo AÑO-MES-DÍA
            df_v['FECHA_CORTA'] = df_v['FECHA'].astype(str).str.slice(0, 10)
            df_hoy = df_v[df_v['FECHA_CORTA'] == fecha_hoy]
            
            if not df_hoy.empty:
                # 1. Ventas del día clasificadas correctamente
                total_detal = df_hoy[(df_hoy['TIPO'] != 'Abono') & (df_hoy['CLIENTE'] == 'CLIENTE DETAL')]['MONTO($)'].sum()
                total_mayor = df_hoy[(df_hoy['TIPO'] != 'Abono') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]['MONTO($)'].sum()
                total_abonos_hoy = df_hoy[df_hoy['TIPO'] == 'Abono']['MONTO($)'].sum()
                
                # Pasamos los abonos a valor positivo para sumarlos limpiamente
                efectivo_abonos = abs(total_abonos_hoy)
                
                # === LA MATEMÁTICA REAL DE TU CAJA FÍSICA ===
                total_liquido_caja = total_detal + efectivo_abonos
                
                # === MUESTRA LOS RECUADROS EN LA PANTALLA DEL CELULAR ===
                coll, col2, col3 = st.columns(3)
                coll.metric("Venta Detal Hoy", f"${total_detal:.2f}")
                col2.metric("Venta Mayor Hoy", f"${total_mayor:.2f}")
                col3.metric("Abonos Recibidos Hoy", f"${efectivo_abonos:.2f}")
                
                st.markdown(f"### 💵 Total General Estimado en Caja: **${total_liquido_caja:.2f}**")
                st.caption("Este monto representa el dinero total que debió ingresar entre ventas directas y pagos de deudas.")
                
                st.write("---")
                
                # Formulario para confirmar el cierre físico
                with st.form("form_cierre"):
                    st.write("¿Todo cuadra con el dinero físico en mano?")
                    observaciones = st.text_area("Notas o novedades del día (Opcional):", placeholder="Ej: Dejamos $20 de cambio...")
                    
                    boton_cierre = st.form_submit_button("🔒 CONSOLIDAR Y CERRAR CAJA")
                    
                    if boton_cierre:
                     # 1. Calculamos la fecha real de Venezuela justo al pisar el botón
                     zona_ve = pytz.timezone('America/Caracas')
                     fecha_ve = datetime.now(zona_ve).strftime("%d/%m/%Y")
            
                     # 2. Preparamos los datos usando la nueva fecha corregida
                     payload_cierre = {
                      "fecha": fecha_ve,  # <--- Cambiado aquí para que use tu hora real
                      "tipo": "CierreCaja",
                      "detal": total_detal,
                      "mayor": total_mayor,
                      "abonos": efectivo_buenos, # Mantén el nombre exacto de tu variable de abonos
                      "total": total_liquido_caja,
                      "notas": observaciones
                     }

                        
                        # Enviamos los datos a tu script de Google
                        respuesta = requests.post(URL_GOOGLE, json=payload_cierre)
                        
                        if respuesta.status_code == 200:
                            st.success("🎉 ¡Cierre de caja guardado con éxito en el sistema!")
                        else:
                            st.error("Hubo un inconveniente al conectar con Google Sheets. Intenta de nuevo.")
            else:
                st.info("Aún no se han registrado ventas ni abonos en la jornada de hoy.")
        else:
            st.info("No se encontraron registros históricos de ventas.")
