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

# --- ESTILO CSS ESTABLE PARA PAREJAS ---
st.markdown("""
  <style>
  /* Forzamos el contenedor de columnas a mantener el orden horizontal en celulares */
  [data-testid="stHorizontalBlock"] {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    width: 100% !important;
  }
  [data-testid="stHorizontalBlock"] > div {
    flex: 1 1 50% !important;
    min-width: 0 !important;
  }
    
  /* Configuración de tamaño para todos los botones */
  div.stButton > button {
    height: 85px !important;
    border-radius: 10px !important;
  }
  /* 🔴 Pintamos el botón de Salir de rojo con letras blancas */
  div.stButton > button:has(div:contains("Cerrar")) {
    background-color: #C62828 !important;
    color: white !important;
    height: 50px !important;
  }

  </style>
""", unsafe_allow_html=True)


# --- CONEXIÓN CON TU EXCEL (URL QUE ME PASASTE) ---
URL_GOOGLE = "https://script.google.com/macros/s/AKfycbxoXYuo0IkMCmEHKKWEnecUfQs7dZlm7604eaVV3ep0GrgxInveg_Me-AyjJjxYhfVR/exec"

# --- SISTEMA DE SEGURIDAD ---
def check_password():
 # 1. Verificamos si la URL del navegador ya tiene guardado el acceso exitoso
 if st.query_params.get("login") == "exitoso":
    st.session_state["password_correct"] = True
    return True

# 2. Respaldo por si acaso está en la sesión interna
 if st.session_state.get("password_correct", False):
    return True

 # 3. Si no hay credenciales registradas, pintamos el formulario de entrada
 st.subheader("🔑 Inicio de Sesión")
    
 usuario_ingresado = st.text_input("Usuario", key="input_usuario")
 clave_ingresada = st.text_input("Contraseña", type="password", key="input_clave")
    
 if st.button("Iniciar Sesión", use_container_width=True):
 # Mantenemos tus mismas credenciales de validación
    if usuario_ingresado == "AYG2017" and clave_ingresada == "AyG2017.":
       st.session_state["password_correct"] = True
       # Guardamos el estado directamente en la barra de navegación del teléfono
       st.query_params["login"] = "exitoso"
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

@st.dialog("🛒 Registrar Venta Detal")
def formulario_venta_detal(clientes_lista, URL_GOOGLE):
    with st.form("detal_flotante"):
      c = st.selectbox("Cliente", clientes_lista)
      n = st.number_input("Monto Total $", min_value=0.0)
      cond = st.selectbox("Condición", ["Contado", "Crédito"])
        
      if st.form_submit_button("REGISTRAR VENTA"):
         import pytz
         from datetime import datetime
         import requests
         import time
            
         zona_ve = pytz.timezone('America/Caracas')
         fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')
         payload = {"fecha": fecha_ve, "tipo": cond, "cliente": c, "monto": n}
            
         requests.post(URL_GOOGLE, json=payload)
         st.success("✅ Venta guardada con éxito")
         time.sleep(1)
         st.rerun()
        
@st.dialog("📦 Registro de Venta al Mayor")
def formulario_venta_mayor(clientes_lista, productos_dict, URL_GOOGLE):
    import requests
    import pytz
    from datetime import datetime
    import base64
    
    st.subheader("🛒 Selector de Pedido al Mayor")
    
    # Inicializamos el carrito en la sesión si no existe para que no se borre
    if 'carro_mayor' not in st.session_state:
        st.session_state.carro_mayor = []
        
    cli_m = st.selectbox("Seleccionar Cliente:", clientes_lista, key="mayor_cli_sel")
    
    # 1. AGREGAR PRODUCTOS (Fuera de un formulario para que actualice el stock dinámico)
    c1, c2 = st.columns(2)
    prod_nom = c1.selectbox("Producto:", list(productos_dict.keys()), key="mayor_prod_sel")
    
    stock_actual = productos_dict[prod_nom]['stock']
    precio_u = productos_dict[prod_nom]['precio']
    
    st.info(f"💰 Precio: ${precio_u:.2f} | 📦 Stock Disponible: {stock_actual}")
    
    max_cant = float(stock_actual) if stock_actual > 0 else 1.0
    cant = c2.number_input("Cantidad:", min_value=1.0, max_value=max_cant, step=1.0, key="mayor_cant")
    
    if st.button("➕ Agregar al Carrito", use_container_width=True):
        subtotal = cant * precio_u
        st.session_state.carro_mayor.append({
            "Producto": prod_nom,
            "Cant": cant,
            "Precio": precio_u,
            "Subtotal": subtotal
        })
        st.toast(f"¡{prod_nom} agregado!")
        
    # 2. MOSTRAR EL CARRITO ACTUAL
    if st.session_state.carro_mayor:
        st.write("---")
        st.markdown("**📋 Contenido del Carrito:**")
        import pandas as pd
        st.table(pd.DataFrame(st.session_state.carro_mayor))
        
        t_final = sum(item['Subtotal'] for item in st.session_state.carro_mayor)
        st.markdown(f"### 🧾 Total a Facturar: **${t_final:.2f}**")
        
        c_btn1, c_btn2 = st.columns(2)
        
        if c_btn1.button("🗑️ Vaciar Carrito", use_container_width=True):
            st.session_state.carro_mayor = []
            st.rerun()
            
        # 3. PROCESAR Y ENVIAR LA VENTA
        if c_btn2.button("💾 CONSOLIDAR Y CREAR PDF", type="primary", use_container_width=True):
            zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime("%d/%m/%Y")
            
            # Preparamos el paquete para Google Sheets
            payload = {
                "fecha": fecha_ve,
                "tipo": "Crédito",
                "cliente": cli_m,
                "monto": t_final
            }
            
            try:
                # Enviamos los datos a Excel
                res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                
                # Generamos el archivo PDF de la factura (Llamando a tu función crear_pdf)
                pdf_b = crear_pdf(cli_m, st.session_state.carro_mayor, t_final)
                b64 = base64.b64encode(pdf_b).decode()
                
                st.success("🟢 ¡Venta registrada en Google Sheets!")
                
                # Creamos el botón de descarga automática para el teléfono
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="Factura_{cli_m}.pdf" style="text-decoration:none;"><button style="width:100%; background-color:#4CAF50; color:white; padding:10px; border:none; border-radius:5px;">📥 Descargar Factura PDF</button></a>'
                st.markdown(href, unsafe_allow_html=True)
                
                # Limpiamos el carrito para la próxima venta
                st.session_state.carro_mayor = []
                
            except Exception as e:
                st.error(f"❌ Error al procesar la venta: {e}")
    else:
        st.write("El carrito está vacío. Agrega productos para comenzar.")

          
@st.dialog("💰 Registrar Abono")
def formulario_cuentas_abonos(clientes_lista, URL_GOOGLE):
    import requests
    import pytz
    from datetime import datetime
    import time
    
    st.subheader("🧾 Registro Rápido de Abono")
    
    # Solo dos campos: cliente y cuánto paga
    c = st.selectbox("Seleccionar Cliente", clientes_lista, key="abono_cli_sel")
    monto = st.number_input("Monto $", min_value=0.0, step=0.01, key="abono_monto")
    
    if st.button("💾 Guardar Operación", use_container_width=True, type="primary"):
        if monto > 0:
            zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')
            
            # El "tipo" siempre es "Abono" y el monto va en negativo para restar
            payload = {
                "fecha": fecha_ve, 
                "tipo": "Abono", 
                "cliente": c, 
                "monto": -float(monto)
            }
            
            try:
                respuesta = requests.post(URL_GOOGLE, json=payload, timeout=10)
                if respuesta.status_code == 200:
                    st.success(f"✅ Abono de ${monto:.2f} registrado con éxito")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Error al conectar con Google Sheets.")
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Escribe un monto mayor a cero.")


@st.dialog("📦 Gestión Integral de Inventario")
def formulario_inventario(productos_dict, clientes_lista, URL_GOOGLE):
    # 📑 Creamos las 5 pestañas organizadas para el teléfono
    tab_almacen, tab_insumos, tab_productos, tab_clientes, tab_imprimir = st.tabs([
        "📊 Estado del Almacén",
        "🍎 Materia Prima",
        "✏️ Nuevos Productos",
        "👤 Nuevos Clientes",
        "🖨️ Imprimir Lista"
    ])
    
    # === PESTAÑA 1: ESTADO DEL ALMACÉN ===
    with tab_almacen:
        st.subheader("📦 Estado del Almacén")
        if 'productos_dict' in locals() or 'productos_dict' in globals():
            import pandas as pd
            df_inv = pd.DataFrame([{"Producto": k, "Precio": f"${v['precio']:.2f}", "Stock": v['stock']} for k, v in productos_dict.items()])
            st.table(df_inv)
        else:
            st.info("Cargando datos del almacén...")
        st.write("⚠️ Las cantidades se actualizan según las Entradas/Salidas de tu Excel.")

    # === PESTAÑA 2: REGISTRO DE MATERIA PRIMA (COSTOS) ===
    with tab_insumos:
        st.subheader("📑 Registro de Costo de Insumos")
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
                    import requests
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_COSTO":
                        st.success(f"🟢 ¡{insumo} guardado! Costo calculado: ${costo_por_unidad:.4f} por Kg/Lt.")
                    else:
                        st.error(f"❌ Error del servidor: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Por favor, rellene todos los campos con valores mayores a cero.")

    # === PESTAÑA 3: REGISTRO DE NUEVOS PRODUCTOS ===
    with tab_productos:
        st.subheader("✨ Agregar Nuevo Producto al Sistema")
        with st.form("form_productos", clear_on_submit=True):
            nuevo_prod = st.text_input("Nombre del Producto:", placeholder="Ej: Pan Camilla, Pan de Tunja")
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
                    import requests
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_PRODUCTO":
                        st.success(f"🟢 ¡Producto '{nuevo_prod}' registrado con éxito!")
                        st.info("💡 Reinicia o refresca la app para que aparezca en tus listas de venta.")
                    else:
                        st.error(f"❌ Error del servidor: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Ingresa el nombre del producto y sus precios válidos.")

    # === PESTAÑA 4: REGISTRO DE NUEVOS CLIENTES ===
    with tab_clientes:
        st.subheader("🤝 Registrar Nuevo Cliente / Bodega")
        with st.form("form_clientes", clear_on_submit=True):
            nuevo_cliente = st.text_input("Nombre completo del Cliente o Bodega:", placeholder="Ej: Bodega Ereau")
            btn_guardar_cliente = st.form_submit_button("Registrar Cliente")
            
        if btn_guardar_cliente:
            if nuevo_cliente:
                payload = {
                    "accion": "guardar_cliente",
                    "nombre_cliente": nuevo_cliente
                }
                try:
                    import requests
                    res = requests.post(URL_GOOGLE, json=payload, timeout=10)
                    if res.text == "OK_CLIENTE":
                        st.success(f"🟢 ¡Cliente '{nuevo_cliente}' guardado correctamente!")
                        st.info("💡 Refresca la app para que figure en la lista de deudores.")
                    else:
                        st.error(f"❌ Error del servidor: {res.text}")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
            else:
                st.warning("⚠️ Por favor, escribe un nombre válido.")

    # === PESTAÑA 5: IMPRIMIR LISTA DE PRECIOS ===
    with tab_imprimir:
        st.subheader("🖨️ Generar Catálogo en PDF")
        st.write("Presiona el botón para descargar la lista de precios vigente basada en la hoja **Productos**.")
        
        if st.button("📄 Generar PDF de Precios"):
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "LISTA DE PRECIOS VIGENTE", ln=True, align="C")
            pdf.ln(10)
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(100, 10, "PRODUCTO", 1)
            pdf.cell(40, 10, "PRECIO", 1, align="C")
            pdf.cell(40, 10, "STOCK", 1, ln=True, align="C")
            
            pdf.set_font("Arial", "", 12)
            for prod, datos in productos_dict.items():
                pdf.cell(100, 10, str(prod), 1)
                pdf.cell(40, 10, f"${datos['precio']:.2f}", 1, align="C")
                pdf.cell(40, 10, str(datos['stock']), 1, ln=True, align="C")
            
            pdf_bytes = pdf.output(dest="S").encode("latin-1")
            st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="lista_precios.pdf", mime="application/pdf", use_container_width=True)

@st.dialog("📋 Resumen de Deudas Activas")
def formulario_cuentas_por_cobrar(clientes_lista, URL_GOOGLE):
    import requests
    import pandas as pd
    
    st.subheader("💰 Resumen de Deudas Activas")
    
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
                saldo_historico = df_c['MONTO($)'].sum()
                if saldo_historico > 0:
                    gran_total_en_calle += saldo_historico
                    
        st.subheader("💰 Capital Total por Cobrar")
        st.info(f"Actualmente tienes un total de **${gran_total_en_calle:.2f}** en la calle (solo deudas vigentes).")
        st.divider()
        
        # --- SECCIÓN DETALLE POR CLIENTE ---
        if clientes_lista:
            cliente_sel = st.selectbox("Ver deudor específico:", clientes_lista, key="cobrar_cliente_sel")
            df_cli = df_v[df_v['CLIENTE'] == cliente_sel].copy()
            saldo_real_neto = round(df_cli['MONTO($)'].sum(), 2)
            
            # --- EVALUAMOS SI DEBE O ESTÁ AL DÍA ---
            if 0.00 <= saldo_real_neto <= 0.01:
                c1, c2 = st.columns(2)
                c1.metric("TOTAL ABONADO (DEUDA ACTUAL)", "$0.00")
                c2.metric("SALDO PENDIENTE NETO", "$0.00")
                st.write("---")
                st.success("🟢 Este cliente está al día. Ambos marcadores están en $0.00")
            elif saldo_real_neto < 0.00:
                c1, c2 = st.columns(2)
                c1.metric("TOTAL ABONADO", f"${abs(saldo_real_neto):.2f}")
                c2.metric("SALDO A FAVOR NETO", f"${abs(saldo_real_neto):.2f}")
                st.write("---")
                st.info(f"🔵 El cliente tiene un saldo a favor de ${abs(saldo_real_neto):.2f}")
            else:
                movimientos_cliente = df_cli.to_dict('records')
                historial_ciclo_activo = []
                saldo_acumulado_inverso = 0.0
                
                for mov in reversed(movimientos_cliente):
                    monto = float(mov['MONTO($)'])
                    saldo_acumulado_inverso += monto
                    historial_ciclo_activo.append(mov)
                    if saldo_acumulado_inverso >= saldo_real_neto:
                        break
                        
                total_abonos_ciclo = sum(float(n['MONTO($)']) for n in historial_ciclo_activo if n['TIPO'] == 'Abono')
                abonos_mostrar = abs(total_abonos_ciclo)
                
                c1, c2 = st.columns(2)
                c1.metric("TOTAL ABONADO (DEUDA ACTUAL)", f"${abonos_mostrar:.2f}")
                c2.metric("SALDO PENDIENTE NETO", f"${saldo_real_neto:.2f}")
                st.write("---")
                
                st.error(f"🔴 Este cliente tiene una cuenta activa por ${saldo_real_neto:.2f}")
                st.write("**Detalle de movimientos de la cuenta vigente:**")
                
                df_mostrar = pd.DataFrame(historial_ciclo_activo)[['FECHA', 'TIPO', 'MONTO($)']]
                df_mostrar = df_mostrar.iloc[::-1]
                st.table(df_mostrar)

@st.dialog("🔒 Control y Cierre de Caja Diario")
def formulario_cierre_de_caja(URL_GOOGLE):
    import requests
    import pandas as pd
    import pytz
    from datetime import datetime
    import time
    
    st.subheader("🏁 Control y Cierre de Caja Diario")
    
    # Pedimos los movimientos de ventas del día actual
    resp = requests.get(f"{URL_GOOGLE}?tipo=Ventas")
    datos_recibidos = resp.json()
    
    if isinstance(datos_recibidos, list):
        df_v = pd.DataFrame(datos_recibidos)
    else:
        df_v = pd.DataFrame()
        
    # --- AJUSTE DE FECHA ---
    zona_ve = pytz.timezone('America/Caracas')
    fecha_hoy = datetime.now(zona_ve).strftime('%Y-%m-%d')
    fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')
    
    st.write(f"📅 **Resumen de Operaciones:** {fecha_ve}")
    
    if not df_v.empty:
        # Forzamos la limpieza de la fecha para tomar solo AÑO-MES-DÍA
        df_v['FECHA_CORTA'] = df_v['FECHA'].astype(str).str.slice(0, 10)
        df_hoy = df_v[df_v['FECHA_CORTA'] == fecha_hoy]
        
        if not df_hoy.empty:
            # # 1. Ventas del día clasificadas correctamente
            # Detal (Siempre entra a caja si es de Contado)
            df_detal_contado = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] == 'CLIENTE DETAL')]
            total_detal = df_detal_contado['MONTO($)'].sum() if not df_detal_contado.empty else 0.0
            
            # Separamos el Mayor de Contado del Mayor de Crédito
            df_mayor_contado = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]
            total_mayor_contado = df_mayor_contado['MONTO($)'].sum() if not df_mayor_contado.empty else 0.0
            
            df_mayor_credito = df_hoy[(df_hoy['TIPO'] == 'Crédito') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]
            total_mayor_credito = df_mayor_credito['MONTO($)'].sum() if not df_mayor_credito.empty else 0.0
            
            total_mayor = total_mayor_contado + total_mayor_credito
            
            # Abonos recibidos hoy
            df_abonos = df_hoy[df_hoy['TIPO'] == 'Abono']
            total_abonos = df_abonos['MONTO($)'].sum() if not df_abonos.empty else 0.0
            efectivo_abonos = abs(total_abonos)
            
            # --- LA MATEMÁTICA REAL DE TU CAJA FÍSICA ---
            total_liquido_caja = total_detal + total_mayor_contado + efectivo_abonos
            
            # --- MUESTRA LOS RECUADROS EN LA PANTALLA ---
            c1, c2, c3 = st.columns(3)
            c1.metric("Venta Detal Hoy", f"${total_detal:.2f}")
            c2.metric("Venta Mayor Hoy", f"${total_mayor:.2f}")
            c3.metric("Abonos Recibidos Hoy", f"${efectivo_abonos:.2f}")
            
            st.markdown(f"### 💵 Total General Estimado en Caja: **${total_liquido_caja:.2f}**")
            st.caption("Este monto representa el dinero total que debió ingresar entre ventas directas y pagos de deudas.")
            st.write("---")
            
            # Formulario para confirmar el cierre físico
            with st.form("form_cierre", clear_on_submit=True):
                st.write("¿Todo cuadra con el dinero físico en mano?")
                observaciones = st.text_area("Notas o novedades del día (Opcional):", placeholder="Ej: Dejamos $20 para base...")
                boton_cierre = st.form_submit_button("🔒 CONSOLIDAR Y CERRAR CAJA")
                
            if boton_cierre:
                payload_cierre = {
                    "fecha": fecha_ve,
                    "tipo": "CierreCaja",
                    "venta_detal": float(total_detal),
                    "venta_mayor": float(total_mayor),
                    "abonos": float(efectivo_abonos),
                    "total_caja": float(total_liquido_caja),
                    "notas": observaciones
                }
                
                try:
                    respuesta = requests.post(URL_GOOGLE, json=payload_cierre, timeout=10)
                    if respuesta.status_code == 200:
                        st.success("🏁 ¡Cierre de caja guardado con éxito en el sistema!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Hubo un inconveniente al conectar con Google Sheets. Intenta de nuevo.")
                except Exception as e:
                    st.error(f"❌ Error de conexión: {e}")
        else:
            st.info("Aún no se han registrado ventas ni abonos en la jornada de hoy.")
    else:
        st.info("No se encontraron registros históricos de ventas.")

@st.dialog("⚖️ Simulador Unificado de Costos e Insumos")
def formulario_simulador_costos():
    import pandas as pd
    import streamlit as st
    
    st.subheader("⚖️ Simulador Unificado de Costos e Insumos")
    st.write("Calcula en tiempo real el costo bruto, operativo y sugerencia de PVP para tu producción.")
    
    # # 1. Base de datos interna con tus recetas reales de Excel
    RECETAS_BASE = {
        "Pan Salado": {"HARINA": 45.0, "AGUA": 18.0, "AZUCAR": 3.0, "SAL": 1.0, "MANTECA": 2.0, "LEVADURA": 0.3, "peso_base": 0.50, "unidades_paquete": 1.0},
        "Pan de Perro": {"HARINA": 50.0, "AGUA": 18.0, "AZUCAR": 5.0, "SAL": 1.0, "MANTECA": 1.7, "LEVADURA": 0.25, "peso_base": 0.04, "unidades_paquete": 12.0},
        "Polvorosas": {"HARINA": 4.5, "PVP": 0.5, "AZUCAR": 2.0, "AGUA": 0.0, "MANTECA": 2.5, "peso_base": 0.04, "unidades_paquete": 1.0},
        "Catalinas": {"HARINA": 5.0, "SODA": 0.5, "MELINA": 3.5, "MELAO PAPELON": 2.0, "AGUA": 2.0, "ESENCIAS": 0.1, "peso_base": 0.06, "unidades_paquete": 6.0},
        "Receta Brownie": {"HARINA": 2.0, "AGUA": 1.0, "AZUCAR": 3.0, "MANTECA": 1.0, "CACAO": 1.0, "HUEVOS": 1.2, "peso_base": 0.05, "unidades_paquete": 1.0},
        "Pudin": {"HARINA": 10.0, "LECHE": 5.0, "AZUCAR": 4.0, "HUEVOS": 1.5, "ESENCIAS": 0.2, "peso_base": 0.50, "unidades_paquete": 1.0},
        "Banquete (50 und)": {"HARINA": 5.0, "AGUA": 2.0, "AZUCAR": 3.0, "MANTECA": 1.0, "SAL": 0.1, "MANTECA": 0.4, "LEVADURA": 0.05, "peso_base": 0.015, "unidades_paquete": 50.0},
        "Pan de Dulce": {"HARINA": 1.0, "AGUA": 1.0, "AZUCAR": 1.0, "ANIS-DULCE": 1.0, "MANTECA": 1.0, "LEVADURA": 0.1, "peso_base": 0.25, "unidades_paquete": 1.0}
    }
    
    # # Selección de receta en pantalla
    opciones_productos = list(RECETAS_BASE.keys())
    producto_seleccionado = st.selectbox("Selecciona el producto a producir:", opciones_productos, key="sim_prod_sel")
    receta = RECETAS_BASE[producto_seleccionado]
    
    st.subheader(f"⚖️ Ajustar Ingredientes para: {producto_seleccionado}")
    col1, col2 = st.columns(2)
    
    # # Intentar leer tu DataFrame real de costos desde la URL de descarga
    try:
        enlace_excel = "https://docs.google.com/spreadsheets/d/1UczgRQ5ewH3M5ZfykdTz3DizPxgUnS2jtaY-dvXmg1I"
        url_publica = enlace_excel + "/export?format=csv&gid=1138925550"
        df_costos_real = pd.read_csv(url_publica)
    except Exception as e:
        df_costos_real = pd.DataFrame(columns=['Insumo', 'Costo Por Unidad'])
        
    ingredientes_modificados = {}
    costo_materia_prima_total = 0.0
    
    with col1:
        st.markdown("**Cantidad de Insumos (Kg / Unidades):**")
        for ingrediente, cant_base in receta.items():
            if ingrediente not in ["peso_base", "unidades_paquete"]:
                cant_actual = st.number_input(f"{ingrediente}:", min_value=0.0, value=float(cant_base), step=0.1, key=f"sim_ing_{ingrediente}")
                ingredientes_modificados[ingrediente] = cant_actual
                
                costo_unitario = 1.0
                if not df_costos_real.empty:
                    df_term = df_costos_real.copy()
                    df_term.columns = df_term.columns.str.strip().str.replace(r'[^\w\s]', '', regex=True)
                    df_term['Insumo_clean'] = df_term.iloc[:, 0].astype(str).str.upper().str.strip()
                    busqueda = str(ingrediente).upper().str.strip()
                    
                    resultado = df_term[df_term['Insumo_clean'].str.contains(busqueda, na=False)]
                    if not resultado.empty:
                        try:
                            valor_crudo = str(resultado.iloc[0].iloc[4])
                            valor_limpio = valor_crudo.replace('$', '').replace(' ', '').strip()
                            costo_unitario = float(valor_limpio)
                        except:
                            costo_unitario = 1.0
                            
                costo_materia_prima_total += cant_actual * costo_unitario

    with col2:
        st.markdown("**Configuración Física del Producto:**")
        peso_pan = st.number_input("Peso por unidad en crudo (Kg):", min_value=0.001, value=receta["peso_base"], step=0.01, key="sim_peso_pan")
        unidades_por_paquete = st.number_input("Unidades por paquete terminado:", min_value=1, value=int(receta["unidades_paquete"]), step=1, key="sim_und_pack")
        
        st.markdown("**📊 Costos Operativos y Extras:**")
        costo_mano_obra = st.number_input("Mano de Obra de la tanda ($):", min_value=0.0, value=0.0, step=0.5, key="sim_mo")
        costo_gas = st.number_input("Costo de Gas / Energía ($):", min_value=0.0, value=0.0, step=0.5, key="sim_gas")
        costo_bolsa = st.number_input("Costo por cada Bolsa de empaque ($):", min_value=0.0, value=0.05, step=0.01, key="sim_bolsa")

    # # 2. Operaciones matemáticas (Lógica automatizada)
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

    # # 3. Reporte final en pantalla
    st.markdown("---")
    st.subheader("📋 Reporte Técnico de Rendimiento y Costo Real")
    
    c_res1, c_res2, c_res3 = st.columns(3)
    c_res1.metric("Masa Total Mezcla", f"{total_kilos_mezcla:.2f} Kg")
    c_res1.metric("Costo Neto Mezcla", f"${costo_materia_prima_total:.2f}")
    
    c_res2.metric("Rendimiento", f"{cantidad_unidades_totales} Unidades")
    c_res2.metric("Costo por Unidad", f"${costo_por_unidad_bruto:.3f}")
    
    c_res3.metric("Total Empacado", f"{total_paquetes:.1f} Paquetes")
    c_res3.metric("Costo por Paquete", f"${costo_por_paquete:.2f}")
    
    # # 4. Calculador interactivo de ganancias y PVP sugerido
    st.subheader("💰 Calculador de Ganancia Variable y PVP Sugerido")
    margen_deseado = st.slider("Selecciona tu porcentaje de ganancia ideal (%):", min_value=10, max_value=150, value=30, key="sim_margen")
    
    factor_ganancia = 1 + (margen_deseado / 100)
    pvp_unidad_sugerido = costo_por_unidad_bruto * factor_ganancia
    pvp_paquete_sugerido = costo_por_paquete * factor_ganancia
    
    col_pvp1, col_pvp2 = st.columns(2)
    col_pvp1.success(f"**PVP Sugerido por Unidad:**\n\n${pvp_unidad_sugerido:.2f}")
    col_pvp2.success(f"**PVP Sugerido por Paquete (Mayor):**\n\n${pvp_paquete_sugerido:.2f}")


# --- DISEÑO DE LA APP ---
if not check_password():
   st.stop()  # 🛑 Si la clave es incorrecta, el programa se frena aquí y no lee más abajo
  
# 🔓 Si el código pasa de la línea anterior, significa que la sesión está activa
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

   st.subheader("🎛️ SISTEMA AYG2017")
    
# 🏪 Fila 1: Ventas (Categoría en bloque Verde)
st.success("🏪 SECCIÓN DE VENTAS")
col1, col2 = st.columns(2)
with col1:
 if st.button("🏪\n\nVenta Detal", key="btn_detal", use_container_width=True):
    formulario_venta_detal(clientes_lista, URL_GOOGLE)

with col2:
 if st.button("🚗\n\nVenta Mayor", key="btn_mayor", use_container_width=True):
    formulario_venta_mayor(clientes_lista, productos_dict, URL_GOOGLE)


# 💰 Fila 2: Gestión (Categoría en bloque Azul)
st.info("💰 GESTIÓN E INVENTARIO")
col3, col4 = st.columns(2)
with col3:
 if st.button("💰\n\nCuentas y Abonos", key="btn_abonos", use_container_width=True):
    formulario_cuentas_abonos(clientes_lista, URL_GOOGLE)

with col4:
 if st.button("📦\n\nInventario", key="btn_inventario", use_container_width=True):
    formulario_inventario(productos_dict, clientes_lista, URL_GOOGLE)


# 🗂️ Fila 3: Reportes y Cierre (Categoría en bloque Naranja)
st.warning("🗂️ REPORTES Y CIERRE")
col5, col6 = st.columns(2)
with col5:
 if st.button("📝\n\nCuentas por Cobrar", key="btn_cobrar", use_container_width=True):
    formulario_cuentas_por_cobrar(clientes_lista, URL_GOOGLE)

with col6:
 if st.button("🔒\n\nCierre de Caja", key="btn_cierre", use_container_width=True):
    formulario_cierre_de_caja(URL_GOOGLE)


# 🧮 Fila 4: Herramientas (Categoría en bloque Rojo/Rosa)
st.error("🧮 HERRAMIENTAS ADICIONALES")
col7, col8 = st.columns(2)
with col7: # O el identificador de columna que le corresponda en tu fila 4
 if st.button("🧮\n\nSimulador Costos", key="btn_simulador", use_container_width=True):
    formulario_simulador_costos()

   
st.markdown("---")
    
# 🕵️ Línea de diagnóstico temporal para ver las variables en la pantalla
st.write(f"Estado actual: password_correct={st.session_state.get('password_correct')}, usuario={st.session_state.get('input_usuario')}")
    
# 🚪 Botón de salida
        
if st.button("🚪 Cerrar Sesión / Salir", key="btn_salir", use_container_width=True, type="primary"):
   st.session_state["password_correct"] = False
   # Limpiamos el parámetro de la URL para bloquear el acceso de nuevo
   st.query_params.clear()
   st.rerun()

 

# =========================================================
# 📲 CONTROL DE LAS VENTANAS DE TRABAJO
# =========================================================
#else:
if st.session_state.pantalla != "Menu Principal":
   #st.stop()
    # Botón de salida arriba en las pantallas secundarias
 if st.button("⬅️ Volver al Menú Principal", key="btn_volver"):
    st.session_state.pantalla = "Menu Principal"
    st.rerun()
    st.markdown("---")

    

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
elif st.session_state.pantalla == "Venta Mayor (SAYG)":

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
elif st.session_state.pantalla == "Cuentas por Cobrar":
#elif menu == "Cuentas por Cobrar":
   # st.heade-("📊 Resumen de Deudas Activas")
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
        if 0.00 <= saldo_real_neto <= 0.01:
            # SI ESTÁ AL DÍA: Forzamos todo a cero limpio y barra verde
            c1, c2 = st.columns(2)
            c1.metric("TOTAL ABONADO (DEUDA ACTUAL)", "$0.00")
            c2.metric("SALDO PENDIENTE NETO", "$0.00")
            st.write("---")
            st.success("🟢 Este cliente está al día. Ambos marcadores están en $0.00")
        elif saldo_real_neto < 0.00:
           # 🔵 SI TIENE SALDO A FAVOR: El cliente pagó de más
            c1, c2 = st.columns(2)
           # Mostramos el abono real positivo usando abs()
            c1.metric("TOTAL ABONADO", f"${abs(saldo_real_neto):.2f}")
            c2.metric("SALDO A FAVOR NETO", f"${abs(saldo_real_neto):.2f}")
            st.write("---")
            st.info(f"🔵 El cliente tiene un saldo a favor de ${abs(saldo_real_neto):.2f}")
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
elif st.session_state.pantalla == "Cierre de Caja":

#elif menu == "Cierre de Caja":
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

elif st.session_state.pantalla == "Simulador Costo":

#elif menu == "Simulador Costos":
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
