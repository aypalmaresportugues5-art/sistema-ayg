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
    # 1. Si el usuario ya inició sesión antes, entra directo
    if st.session_state.get("password_correct", False):
        return True

    # 2. Si no ha iniciado sesión, muestra la pantalla según tu boceto
    # Colocamos la imagen de marca arriba
    st.image("1000357144.jpg", use_container_width=True)
    
    st.subheader("🔑 Inicio de Sesión")
    
    # Campos para ingresar los datos
    usuario_ingresado = st.text_input("Usuario")
    clave_ingresada = st.text_input("Contraseña", type="password")
    
    # Botón para verificar
    if st.button("Iniciar Sesión"):
        if usuario_ingresado == "AYG2017" and clave_ingresada == "Admin":
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
            
    return False


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
# --- SISTEMA DE NAVEGACIÓN ---
if "pantalla" not in st.session_state:
   st.session_state.pantalla = "Menu Principal"

# Separador debajo del logo
st.markdown("---")

# =========================================================
# 🔲 PANTALLA PRINCIPAL: EL TABLERO DE BOTONES
# =========================================================
if st.session_state.pantalla == "Menu Principal":
   st.subheader("🎛️ Tablero de Control")
    
    # Fila 1: Ventas
   col1, col2 = st.columns(2)
   with col1:
    if st.button("🏪\n\nVenta Detal", key="btn_detal"):
       st.session_state.pantalla = "Venta Detal"
       st.rerun()
   with col2:
    if st.button("🚚\n\nVenta Mayor", key="btn_mayor"):
       st.session_state.pantalla = "Venta Mayor (SAYG)"
       st.rerun()
            
    st.write("*(Pronto activaremos los demás botones)*")

# =========================================================
# 📲 CONTROL DE LAS VENTANAS DE TRABAJO
# =========================================================
else:
    # Botón de salida arriba en las pantallas secundarias
    if st.button("⬅️ Volver al Menú Principal", key="btn_volver"):
       st.session_state.pantalla = "Menu Principal"
       st.rerun()
    st.markdown("---")

    # --- 1. VENTA DETAL ---
    # ⚠️ ¡OJO! Aquí es donde conectas con tu código actual:
    #if st.session_state.pantalla == "Venta Detal":

#with st.sidebar:
   # st.write("---") # Línea divisoria elegante
    
    # Creamos el menú moderno con sus íconos
  #  menu = option_menu(
     #   menu_title="MENÚ AYG 2017",
   #     options=["Venta Detal", "Venta Mayor (SAYG)", "Cuentas y Abonos", "Inventario", "Cuentas por Cobrar", "Cierre de Caja","Simulador Costos"],
    #    icons=["shop", "truck", "wallet2", "box-seam", "cash-stack"], 
    #    menu_icon="building-gear", 
    #    default_index=0, 
       # styles={
       #     "container": {"padding": "5px", "background-color": "#f8f9fa", "border-radius": "10px"},
        #    "icon": {"color": "#FF4B4B", "font-size": "18px"}, 
        #    "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "border-radius": "8px","color": "#1e1e1e"},
         #   "nav-link-selected": {"background-color": "#FF4B4B", "color": "white", "font-weight": "bold"},
       # }
   # )

# 1. VENTA DETAL

if st.session_state.pantalla == "Venta Detal":
#if menu == "Venta Detal":
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
elif st.session_state.pantalla == "Venta Mayor":

#elif menu == "Venta Mayor (SAYG)":
    st.header("📦 Pedido al Mayor")
    cli_m = st.selectbox("Seleccionar Cliente", clientes_lista)
    
    col1, col2 = st.columns(2)
    prod_nom = col1.selectbox("Producto", list(productos_dict.keys()))
    stock_actual = productos_dict[prod_nom]['stock']
    precio_u = productos_dict[prod_nom]['precio']
    
    st.info(f"💰 Precio: {precio_u}$ | 📦 Stock: {stock_actual}")
    cant = col2.number_input("Cantidad", min_value=0.0, max_value=float(stock_actual) if stock_actual > 0 else 1.0, step=0.001, format="%.3f")

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
elif st.session_state.pantalla == "Cuentas y Abonos":

#elif menu == "Cuentas y Abonos":
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
elif st.session_state.pantalla == "Inventario":
#elif menu == "Inventario":
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
            p_mayor = st.number_input("Precio de Venta Mayor ($):", min_value=0.0, step=0.01, format="%.2f")
            cant_inicial = st.number_input("Cantidad o Inventario Inicial:", min_value=1, step=1, value=20)

            btn_guardar_prod = st.form_submit_button("Registrar Producto")

        if btn_guardar_prod:
            if nuevo_prod and p_mayor > 0 and cant_inicial > 0:
                payload = {
                    "accion": "guardar_producto",
                    "nombre_producto": nuevo_prod,
                    "precio_mayor": p_mayor,
                    "cantidad_inicial": cant_inicial
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
elif st.session_state.pantalla == "Cuentas por Cobrar"
#elif menu == "Cuentas por Cobrar":
    st.heade-("📊 Resumen de Deudas Activas")
    
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
        zona_ve = pytz.timezone('America/Caracas')
        fecha_hoy = datetime.now(zona_ve).strftime('%Y-%m-%d')
        st.subheader(f"Resumen de Operaciones: {fecha_hoy}")
        
        if not df_v.empty:
            # Forzamos la limpieza de la fecha para tomar solo AÑO-MES-DÍA
            df_v['FECHA_CORTA'] = df_v['FECHA'].astype(str).str.slice(0, 10)
            df_hoy = df_v[df_v['FECHA_CORTA'] == fecha_hoy]
            
            if not df_hoy.empty:
                # # 1. Ventas del día clasificadas correctamente
                # Detal (Siempre entra a caja si es de Contado)
                total_detal = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] == 'CLIENTE DETAL')]['MONTO($)'].sum()
        
                # Separamos el Mayor de Contado del Mayor de Crédito
                total_mayor_contado = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]['MONTO($)'].sum()
                total_mayor_credito = df_hoy[(df_hoy['TIPO'] == 'Crédito') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]['MONTO($)'].sum()
        
                # El total de Mayor que se muestra en el recuadro gris sigue siendo la suma de ambos
                total_mayor = total_mayor_contado + total_mayor_credito
        
                # Abonos recibidos hoy
                total_abonados = df_hoy[df_hoy['TIPO'] == 'Abono']['MONTO($)'].sum()
                efectivo_abonos = abs(total_abonados)

                # === LA MATEMÁTICA REAL DE TU CAJA FÍSICA ===
                # Dinero real en mano = Detal de contado + Mayor de contado + Los abonos que pagaron hoy
                total_liquido_caja = total_detal + total_mayor_contado + efectivo_abonos
                
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
                      "fecha": fecha_ve,
                      "tipo": "CierreCaja",
                      "venta_detal": float(total_detal),
                      "venta_mayor": float(total_mayor),
                      "abonos": float(efectivo_abonos),
                      "total_caja": float(total_liquido_caja),
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
elif menu == "Simulador Costos":
        st.header("🥖 Simulador Unificado de Costos e Insumos")
        st.write("Calcula en tiempo real el costo bruto, operativo y sugerencia de PVP para tu producción.")

        # 1. Base de datos interna con tus recetas reales de Excel
        RECETAS_BASE = {
            "Pan Salado": {"HARINA": 45.0, "AGUA": 19.0, "AZUCAR": 3.0, "SAL": 1.0, "MANTECA": 2.0, "LEVADURA": 0.3, "ESENCIAS": 0.4, "peso_base": 0.05, "unidades_paquete": 12},
            "Pan de Perro": {"HARINA": 50.0, "AGUA": 19.0, "AZUCAR": 5.0, "SAL": 1.0, "MANTECA": 1.7, "LEVADURA": 0.25, "ESENCIAS": 0.4, "peso_base": 0.05, "unidades_paquete": 10},
            "Polvorosas": {"HARINA": 4.5, "PH": 0.5, "AZUCAR": 2.0, " AGUA":0.0, "MANTECA": 2.5, "peso_base": 0.04, "unidades_paquete": 1},
            "Catalinas": {"HARINA": 5.0, "SODA": 0.5, "MIELINA": 3.5, "MELAO PAPELÓN": 2.0, "AGUA": 2.0, "ESENCIAS": 0.1, "ANIS Y CANELA": 2.0, "peso_base": 0.06, "unidades_paquete": 1},
            "Receta Brownie": {"HARINA": 2.0, "AGUA":1.0, "AZUCAR": 3.0, "MANTECA": 1.0, "CACAO": 1.0, "HUEVOS": 1.2, "peso_base": 0.08, "unidades_paquete": 1},
            "PUDIN": {"HARINA": 10.0, "LECHE": 5.0, "AZUCAR": 4.0, "HUEVOS": 1.5, "ESENCIAS": 0.2, "peso_base": 0.50, "unidades_paquete": 1},
            "Banquete (50 und)": {"HARINA": 5.0, "AGUA": 2.0, "AZUCAR": 0.5, "SAL": 0.1, "MANTECA": 0.4, "LEVADURA": 0.1, "peso_base": 0.03, "unidades_paquete": 50}, 
            "PAN DE DULCE": {"HARINA": 1.0, "AGUA": 1.0, "AZUCAR": 1.0, "ANIS-CANELA": 1.0, "MANTECA": 1.0, "LEVADURA": 0.3, "ESENCIAS": 0.3, "GUAYABA": 0.4, "AREQUIPE": 0.4, "peso_base": 0.4, "unidades_paquete": 1}, 
        }

        # Selección de receta en pantalla
        opciones_productos = list(RECETAS_BASE.keys())
        producto_seleccionado = st.selectbox("Selecciona el producto a producir:", opciones_productos)
        receta = RECETAS_BASE[producto_seleccionado]

        st.subheader(f"📋 Ajustar Ingredientes para: {producto_seleccionado}")
        col1, col2 = st.columns(2)

        # Intentar leer tu DataFrame real de costos desde el estado de la sesión
        try:
          # Enlace directo de tu Google Sheets para la descarga de datos
          enlace_excel = "https://docs.google.com/spreadsheets/d/1UczgRQ5mvN3N5ZfykdTx3O4iPxgUVs2jtaV-dWXmgII"
    
          # Construcción de la URL de descarga para formato CSV
          url_publica = enlace_excel + "/export?format=csv&gid=1138925550"
          df_costos_real = pd.read_csv(url_publica)
          st.success("¡Conexión exitosa con la tabla de costos!")
        except Exception as e:
          st.error(f"Error de lectura: {e}")
          df_costos_real = st.session_state.get('df_costos', pd.DataFrame(columns=['Insumo', 'Costo Por Unidad']))


    
        ingredientes_modificados = {}
        costo_materia_prima_total = 0.0

        with col1:
            st.markdown("**Cantidad de Insumos (Kg / Unidades):**")
            for ingrediente, cant_base in receta.items():
                if ingrediente not in ["peso_base", "unidades_paquete"]:
                    cant_actual = st.number_input(f"{ingrediente}:", min_value=0.0, value=float(cant_base), step=0.1, format="%.2f")
                    ingredientes_modificados[ingrediente] = cant_actual
                    
                    # Buscador optimizado e integrado
                    # Buscador optimizado sin errores de columnas
                    costo_unitario = 1.0
                    if not df_costos_real.empty:
                    # Creamos una copia y limpiamos los nombres de las columnas del Excel
                        df_term = df_costos_real.copy()
                        # Limpiamos espacios y cualquier símbolo raro de los títulos
                        df_term.columns = df_term.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
        
                        # Leemos la primera columna de la tabla (posición 0), se llame como se llame
                        df_term['Insumo_clean'] = df_term.iloc[:, 0].astype(str).str.upper().str.strip()
                        busqueda = str(ingrediente).upper().strip()

    
                     
                        resultado = df_term[df_term['Insumo_clean'].str.contains(busqueda, na=False)]
                        if not resultado.empty:
                           try:
                              # Sacamos el texto crudo del precio (ej: '$1.36')
                              valor_crudo = str(resultado.iloc[0].iloc[4])
                              # Borramos el signo de dólar y espacios extras
                              valor_limpio = valor_crudo.replace('$', '').replace(' ', '').strip()
                              costo_unitario = float(valor_limpio)
                           except:
                              costo_unitario = 1.0  # Respaldo por si la celda está rota
                        else:
                          costo_unitario = 1.0

                        costo_materia_prima_total += cant_actual * costo_unitario

                           

        with col2:
            st.markdown("**Configuración Física del Producto:**")
            peso_pan = st.number_input("Peso por unidad en crudo (Kg):", min_value=0.001, value=receta["peso_base"], step=0.001, format="%.3f")
            unidades_por_paquete = st.number_input("Unidades por paquete terminado:", min_value=1, value=receta["unidades_paquete"], step=1)
            
            st.markdown("**📊 Costos Operativos y Extras:**")
            costo_mano_obra = st.number_input("Mano de Obra de la tanda ($):", min_value=0.0, value=0.0, step=0.5)
            costo_gas = st.number_input("Costo de Gas / Energía ($):", min_value=0.0, value=0.0, step=0.5)
            costo_bolsa = st.number_input("Costo por cada Bolsa de empaque ($):", min_value=0.0, value=0.05, step=0.01, format="%.2f")

        # 2. Operaciones matemáticas (Lógica automatizada)
        total_kilos_mezcla = sum(ingredientes_modificados.values())
        cantidad_unidades_totales = int(total_kilos_mezcla / peso_pan) if peso_pan > 0 else 0
        total_paquetes = cantidad_unidades_totales / unidades_por_paquete if unidades_por_paquete > 0 else 0
        costo_operativo_total = costo_materia_prima_total + costo_mano_obra + costo_gas

        if cantidad_unidades_totales > 0:
            costo_por_unidad_bruto = costo_operativo_total / cantidad_unidades_totales
            costo_por_paquete = (costo_por_unidad_bruto * unidades_por_paquete) + costo_bolsa
        else:
            costo_por_unidad_bruto = 0.0
            costo_por_paquete = 0.0

        # 3. Reporte final en pantalla
        st.markdown("---")
        st.subheader("🏁 Reporte Técnico de Rendimiento y Costo Real")

        c_res1, c_res2, c_res3 = st.columns(3)
        with c_res1:
            st.metric("Masa Total Mezcla", f"{total_kilos_mezcla:.2f} Kg")
            st.metric("Costo Neto Mezcla", f"${costo_materia_prima_total:.2f}")
        with c_res2:
            st.metric("Rendimiento", f"{cantidad_unidades_totales} Unidades")
            st.metric("Costo por Unidad", f"${costo_por_unidad_bruto:.3f}")
        with c_res3:
            st.metric("Total Empacado", f"{total_paquetes:.1f} Paquetes")
            st.metric("Costo por Paquete", f"${costo_por_paquete:.2f}")

        # 4. Calculador interactivo de ganancias y PVP sugerido
        st.subheader("💰 Calculador de Ganancia Variable y PVP Sugerido")
        margen_deseado = st.slider("Selecciona tu porcentaje de ganancia ideal (%):", min_value=10, max_value=150, value=40, step=5)

        factor_ganancia = 1 + (margen_deseado / 100)
        pvp_unidad_sugerido = costo_por_unidad_bruto * factor_ganancia
        pvp_paquete_sugerido = costo_por_paquete * factor_ganancia

        col_pvp1, col_pvp2 = st.columns(2)
        with col_pvp1:
            st.success(f"**PVP Sugerido por Unidad:** ${pvp_unidad_sugerido:.2f}")
        with col_pvp2:
            st.success(f"**PVP Sugerido por Paquete (Mayor):** ${pvp_paquete_sugerido:.2f}")
            
        st.info(f"💡 Al vender al mayor con un {margen_deseado}% de margen, tu ganancia neta estimada por horneada será de ${(pvp_paquete_sugerido - costo_por_paquete) * total_paquetes:.2f} $.")
