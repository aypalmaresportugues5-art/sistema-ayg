import streamlit as st
import pandas as pd
from supabase import create_client
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

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()



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


# --- CARGA DE DATOS DESDE SUPABASE ---
@st.cache_data(ttl=10)
def cargar_clientes():
    try:
        res = supabase.table("clientes").select("NOMBRE").execute()
        df = pd.DataFrame(res.data) if res.data else pd.DataFrame()
        if not df.empty:
            # Buscar la columna sin importar si está en mayúsculas o minúsculas
            col_nombre = "NOMBRE" if "NOMBRE" in df.columns else "nombre"
            if col_nombre in df.columns:
                return df[col_nombre].dropna().tolist()
        return ["CLIENTE DETAL"]
    except Exception:
        return ["CLIENTE DETAL"]

@st.cache_data(ttl=10)
def cargar_productos_dict():
    try:
        # Nota: Asegúrate de que el nombre de la tabla sea 'productos' en minúsculas
        res = supabase.table("productos").select("NOMBRE, PRECIO, ENTRADA, SALIDA").execute()
        if not res.data:
            return {} # Retorna vacío si no hay datos
            
        diccionario = {}
        for p in res.data:
            nombre = str(p.get("NOMBRE", ""))
            if nombre:
                # Calculamos el stock como ENTRADA - SALIDA (considerando SALIDA puede ser None)
                entrada = float(p.get("ENTRADA") or 0.0)
                salida = float(p.get("SALIDA") or 0.0)
                diccionario[nombre] = {
                    "precio": float(p.get("PRECIO") or 0.0),
                    "stock": entrada - salida
                }
        return diccionario
    except Exception as e:
        st.error(f"Error de Supabase: {e}")
        return {}
# Obtener las variables para los selectores del sistema
clientes_lista = cargar_clientes()
productos_dict = cargar_productos_dict()

# --- FUNCIÓN GENERADORA DE PDF SEGURO ---
def crear_pdf(cliente, pedido, total, *args, **kwargs):
    # Rescatamos las variables que vienen del botón de abajo
    fecha_vencimiento = kwargs.get('fecha_vencimiento', 'A consultar')
    tasa_bcv = kwargs.get('tasa_bcv', 45.0)
    
    pdf = FPDF()
    pdf.add_page()
    
    # Membrete principal de la empresa
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "INVERSIONES AYG 2017 C.A.", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 7, "RIF: J-40982649-7 | Barquisimeto, Edo. Lara", ln=True, align='C')
    pdf.ln(10)
    
    # Sección de Encabezados con Vencimiento
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"FACTURA DE VENTA - {datetime.now().strftime('%d/%m/%Y')}", ln=True)
    
    # 📆 IMPRIMIMOS EL VENCIMIENTO EN EL PDF
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(55, 8, "FECHA DE VENCIMIENTO: ")
    pdf.set_text_color(255, 0, 0) # Color Rojo para alertar
    pdf.cell(0, 8, f"{fecha_vencimiento}", ln=True)
    pdf.set_text_color(0, 0, 0) # Regresamos el texto a color negro
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 8, f"CLIENTE: {cliente}", ln=True)
    pdf.ln(5)
    
    # Encabezados de la Tabla de Productos
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, "PRODUCTO", 1, 0, 'C', True)
    pdf.cell(30, 10, "CANT", 1, 0, 'C', True)
    pdf.cell(40, 10, "PRECIO U.", 1, 0, 'C', True)
    pdf.cell(40, 10, "SUBTOTAL", 1, 1, 'C', True)
    
    # Listado de productos comprados
    pdf.set_font("Arial", '', 11)
    for item in pedido:
        pdf.cell(80, 10, item['Producto'], 1)
        pdf.cell(30, 10, str(item['Cant']), 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Precio']:.2f}$", 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Subtotal']:.2f}$", 1, 1, 'C')
    pdf.ln(5)
    
    # Totales en Dólares
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(150, 10, "TOTAL A PAGAR:", 0, 0, 'R')
    pdf.cell(40, 10, f"{total:.2f}$", 1, 1, 'C')
    pdf.ln(5)
    
    # 📊 CÁLCULO EN BS. Y MENSAJE DE CONCIENTIZACIÓN (FPDF NUEVO)
    total_en_bs = total * tasa_bcv
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, f"Tasa de Cambio Oficial aplicada (BCV): {tasa_bcv:.2f} Bs./$", ln=True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 128, 0) # Color Verde para los Bolívares
    pdf.cell(0, 8, f"TOTAL NETO A PAGAR EN BOLIVARES: {total_en_bs:.2f} Bs.", ln=True)
    pdf.set_text_color(0, 0, 0) # Volvemos a negro
    pdf.ln(5)
    
    # Párrafo legal del horario (MultiCell maneja saltos de línea automáticos)
    pdf.set_font("Arial", '', 9)
    nota_bcv = (
        "NOTA DE PAGO: Los pagos en bolivares se reciben estrictamente a la tasa oficial "
        "BCV vigente al momento de la transaccion. Todo pago realizado despues de las 5:00 pm "
        "(o fines de semana) se calculara obligatoriamente a la tasa actualizada emitida por "
        "el BCV para el dia habil siguiente. Evite recargos pagando antes de su vencimiento."
    )
    pdf.multi_cell(0, 5, nota_bcv, 1) # El 1 le hace un recuadro de advertencia
    
    return pdf.output(dest='S').encode('latin-1')



@st.dialog("🛒 Registro de Venta al Detal")
def formulario_venta_detal(clientes_lista):
    with st.form("detal_flotante"):
        c = st.selectbox("Cliente", clientes_lista)
        m = st.number_input("Monto Total $", min_value=0.0)
        cond = st.selectbox("Condición", ["Contado", "Crédito"])

        if st.form_submit_button("REGISTRAR VENTA"):
            import time
            zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')

            payload = {
                "FECHA": fecha_ve,
                "TIPO": cond,
                "CLIENTE": c,
                "MONTO($)": float(m)
            }

            supabase.table("ventas").insert(payload).execute()
            st.cache_data.clear()

            st.success("💾 Venta guardada con éxito")
            time.sleep(1)
            st.rerun()

        
elif st.session_state.pantalla == "Venta Mayor (SAYG)":
        # Simplemente llama a tu función, ya no es un diálogo
    formulario_venta_mayor(clientes_lista, productos_dict)
    
   
    st.subheader("🛒 Selector de Pedido al Mayor")

    # Inicializamos el carrito en la sesión si no existe para que no se borre
    if 'carro_mayor' not in st.session_state:
        st.session_state.carro_mayor = []

    cli_m = st.selectbox("Seleccionar Cliente:", clientes_lista, key="mayor_cli_sel")
    
    # CONTROL MANUAL DE TASA BCV EN VENTA AL MAYOR
    tasa_bcv = st.number_input("💵 Especificar Tasa Oficial BCV (Bs./$):", min_value=1.0, value=45.0, step=0.01, key="mayor_tasa_bcv")
    
    # SELECTOR DE CONDICIÓN DE PAGO
    condicion_pago = st.selectbox("💳 Condición de Pago:", ["Crédito", "Contado"], key="mayor_condicion_pago")

    # 1. AGREGAR PRODUCTOS
    c1, c2 = st.columns(2)
    prod_nom = c1.selectbox("Producto:", list(productos_dict.keys()), key="mayor_prod_sel")
    
    # Manejo seguro si productos_dict solo tiene el precio directo
    producto_info = productos_dict.get(prod_nom, {})
    precio_u = float(producto_info.get('precio', 0.0)) if isinstance(producto_info, dict) else float(producto_info or 0.0)

    st.info(f"💵 Precio: ${precio_u:.2f}")

    cant = c2.number_input("Cantidad:", min_value=1.0, step=1.0, key="mayor_cant")

    if st.button("➕ Agregar al Carrito", use_container_width=True):
        subtotal = cant * precio_u
        st.session_state.carro_mayor.append({
            "Producto": prod_nom,
            "Cant": cant,
            "Precio": precio_u,
            "Subtotal": subtotal
        })
        st.toast(f"✅ {prod_nom} agregado!")

    # 2. MOSTRAR EL CARRITO ACTUAL
    if st.session_state.carro_mayor:
        st.write("---")
        st.markdown("**🛒 Contenido del Carrito:**")
        import pandas as pd
        st.table(pd.DataFrame(st.session_state.carro_mayor))

        t_final = sum(item['Subtotal'] for item in st.session_state.carro_mayor)
        st.markdown(f"### 💰 Total a Facturar: **${t_final:.2f}**")

        # ELIMINAR UN PRODUCTO ESPECÍFICO
        st.write("---")
        st.markdown("**🗑️ Modificar Contenido del Carrito:**")
        productos_en_carro = [item["Producto"] for item in st.session_state.carro_mayor]
        
        col_borrar1, col_borrar2 = st.columns([2, 1])
        prod_a_eliminar = col_borrar1.selectbox("Selecciona el producto que deseas sacar del pedido:", productos_en_carro, key="prod_borrar_mayor")
        
        if col_borrar2.button("🗑️ Eliminar Producto", use_container_width=True):
            for item in st.session_state.carro_mayor:
                if item["Producto"] == prod_a_eliminar:
                    st.session_state.carro_mayor.remove(item)
                    st.toast(f"🗑️ {prod_a_eliminar} eliminado del carrito")
                    st.rerun()

        st.write("---")
        c_btn1, c_btn2 = st.columns(2)

        if c_btn1.button("🧹 Vaciar Carrito", use_container_width=True):
            st.session_state.carro_mayor = []
            st.rerun()

        # 3. PROCESAR Y ENVIAR LA VENTA
        if c_btn2.button("💾 CONSOLIDAR Y CREAR PDF", type="primary", use_container_width=True):
            try:
                zona_ve = pytz.timezone('America/Caracas')
                ahora_ve = datetime.now(zona_ve)
                fecha_ve = ahora_ve.strftime("%d/%m/%Y")
                ts_actual = ahora_ve.timestamp()

                if condicion_pago == "Contado":
                    fecha_vencimiento = fecha_ve
                else:
                    ts_vencimiento = ts_actual + (5 * 24 * 3600)
                    vencimiento_dt = datetime.fromtimestamp(ts_vencimiento, zona_ve)
                    fecha_vencimiento = vencimiento_dt.strftime("%d/%m/%Y")

                # Guardado en Supabase (Tabla ventas)
                payload = {
                    "FECHA": fecha_ve,
                    "TIPO": condicion_pago,
                    "CLIENTE": cli_m,
                    "MONTO($)": float(t_final)
                }

                supabase.table("ventas").insert(payload).execute()
                st.cache_data.clear()

                # Generación de PDF
                pdf_b = crear_pdf(cli_m, st.session_state.carro_mayor, t_final, fecha_vencimiento=fecha_vencimiento, tasa_bcv=tasa_bcv)
                b64 = base64.b64encode(pdf_b).decode()

                st.success("✅ Venta registrada con éxito en Supabase!")

                # Botón para descargar factura
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="Factura_{cli_m}.pdf" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">📥 Descargar Factura PDF</a>'
                st.markdown(href, unsafe_allow_html=True)

                st.session_state.carro_mayor = []

            except Exception as e:
                st.error(f"🚨 Error al procesar la venta: {e}")

    else:
        st.write("El carrito está vacío. Agrega productos para comenzar.")
          
@st.dialog("💵 Registrar Abono")
def formulario_cuentas_abonos(clientes_lista):
    import pytz
    from datetime import datetime
    import time

    st.subheader("💵 Registro Rápido de Abono")

    # Solo dos campos: cliente y cuánto paga
    c = st.selectbox("Seleccionar Cliente", clientes_lista, key="abono_cli_sel")
    monto = st.number_input("Monto $", min_value=0.0, step=0.01, key="abono_monto")

    if st.button("💾 Guardar Operación", use_container_width=True, type="primary"):
        if monto > 0:
            try:
                zona_ve = pytz.timezone('America/Caracas')
                fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')

                # El "TIPO" siempre es "Abono" y el monto va en negativo para restar la deuda
                payload = {
                    "FECHA": fecha_ve,
                    "TIPO": "Abono",
                    "CLIENTE": c,
                    "MONTO($)": -float(monto)
                }

                # Inserción directa en la tabla ventas de Supabase
                supabase.table("ventas").insert(payload).execute()
                st.cache_data.clear()

                st.success(f"✅ Abono de ${monto:.2f} registrado con éxito")
                time.sleep(1)
                st.rerun()

            except Exception as e:
                st.error(f"🚨 Error al registrar abono: {e}")
        else:
            st.warning("⚠️ Escribe un monto mayor a cero.")

@st.dialog("📦 Gestión Integral de Inventario")
def formulario_inventario(productos_dict, clientes_lista):
    # Creamos las 5 pestañas organizadas para el teléfono
    tab_almacen, tab_insumos, tab_productos, tab_clientes, tab_imprimir = st.tabs([
        "📦 Estado del Almacén",
        "📦 Materia Prima",
        "➕ Nuevos Productos",
        "👤 Nuevos Clientes",
        "📄 Imprimir Lista"
    ])

    # === PESTAÑA 1: ESTADO DEL ALMACÉN ===
    with tab_almacen:
        st.subheader("📦 Estado del Almacén")
        if productos_dict:
            import pandas as pd
            filas_inv = []
            for k, v in productos_dict.items():
                precio_v = v.get('precio', 0.0) if isinstance(v, dict) else v
                stock_v = v.get('stock', 0) if isinstance(v, dict) else 0
                filas_inv.append({
                    "Producto": k,
                    "Precio": f"${precio_v:.2f}",
                    "Stock": stock_v
                })
            df_inv = pd.DataFrame(filas_inv)
            st.table(df_inv)
        else:
            st.info("Cargando datos del almacén...")

    # === PESTAÑA 2: REGISTRO DE MATERIA PRIMA (COSTOS) ===
    with tab_insumos:
        st.subheader("📦 Registro de Costo de Insumos")
        with st.form("form_costos", clear_on_submit=True):
            insumo = st.text_input("Nombre del Insumo:", placeholder="Ej: Harina de Trigo, Manteca, Azúcar")
            costo_compra = st.number_input("Costo Total de Compra ($):", min_value=0.0, step=0.01, format="%.2f")
            presentacion = st.text_input("Presentación / Empaque:", placeholder="Ej: Saco, Bulto, Caja, Litro")
            unidad_medida = st.number_input("Cantidad total en Unidades (Kg o Lt):", min_value=0.0, step=0.01, format="%.2f")
            
            btn_guardar_costo = st.form_submit_button("Guardar Insumo")

        if btn_guardar_costo:
            if insumo and costo_compra > 0 and unidad_medida > 0:
                costo_por_unidad = round(costo_compra / unidad_medida, 4)
                try:
                    payload = {
                        "insumo": insumo,
                        "costo_compra": float(costo_compra),
                        "presentacion": presentacion,
                        "unidad_medida": float(unidad_medida),
                        "costo_unidad": float(costo_por_unidad)
                    }
                    supabase.table("insumos").insert(payload).execute()
                    st.cache_data.clear()
                    st.success(f"✅ ¡{insumo} guardado! Costo calculado: ${costo_por_unidad:.4f} por Kg/Lt")
                except Exception as e:
                    st.error(f"🚨 Error de conexión o guardado: {e}")
            else:
                st.warning("⚠️ Por favor, rellene todos los campos con valores mayores a cero.")

    # === PESTAÑA 3: REGISTRO DE NUEVOS PRODUCTOS ===
    with tab_productos:
        st.subheader("📦 Agregar Nuevo Producto al Sistema")
        with st.form("form_productos", clear_on_submit=True):
            nuevo_prod = st.text_input("Nombre del Producto:", placeholder="Ej: Pan Camilla, Pan de Tunja")
            p_mayor = st.number_input("Precio de Venta Mayor ($):", min_value=0.0, step=0.01, format="%.2f")
            cant_inicial = st.number_input("Cantidad o Inventario Inicial:", min_value=0, step=1, value=20)
            
            btn_guardar_prod = st.form_submit_button("Registrar Producto")

        if btn_guardar_prod:
            if nuevo_prod and p_mayor > 0:
                try:
                    payload = {
                        "nombre": nuevo_prod,
                        "precio": float(p_mayor),
                        "stock": int(cant_inicial)
                    }
                    supabase.table("productos").insert(payload).execute()
                    st.cache_data.clear()
                    st.success(f"✅ ¡Producto '{nuevo_prod}' registrado con éxito!")
                    st.info("🔄 Reinicia o refresca la app para que aparezca en tus listas de venta.")
                except Exception as e:
                    st.error(f"🚨 Error al registrar producto: {e}")
            else:
                st.warning("⚠️ Ingresa el nombre del producto y sus precios válidos.")

    # === PESTAÑA 4: REGISTRO DE NUEVOS CLIENTES ===
    with tab_clientes:
        st.subheader("👤 Registrar Nuevo Cliente / Bodega")
        with st.form("form_clientes", clear_on_submit=True):
            nuevo_cliente = st.text_input("Nombre completo del Cliente o Bodega:", placeholder="Ej: Bodega Ereau")
            btn_guardar_cliente = st.form_submit_button("Registrar Cliente")

        if btn_guardar_cliente:
            if nuevo_cliente:
                try:
                    payload = {"nombre": nuevo_cliente}
                    supabase.table("clientes").insert(payload).execute()
                    st.cache_data.clear()
                    st.success(f"✅ ¡Cliente '{nuevo_cliente}' guardado correctamente!")
                    st.info("🔄 Refresca la app para que figure en la lista de deudores.")
                except Exception as e:
                    st.error(f"🚨 Error al registrar cliente: {e}")
            else:
                st.warning("⚠️ Por favor, escribe un nombre válido.")

    # === PESTAÑA 5: IMPRIMIR LISTA DE PRECIOS ===
    with tab_imprimir:
        st.subheader("📄 Generar Catálogo en PDF")
        st.write("Presiona el botón para descargar la lista de precios vigente.")
        
        if st.button("📄 Generar PDF de Precios", use_container_width=True):
            try:
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
                    precio_val = datos.get('precio', 0.0) if isinstance(datos, dict) else datos
                    stock_val = datos.get('stock', 0) if isinstance(datos, dict) else 0
                    
                    pdf.cell(100, 10, str(prod), 1)
                    pdf.cell(40, 10, f"${precio_val:.2f}", 1, align="C")
                    pdf.cell(40, 10, str(stock_val), 1, ln=True, align="C")

                pdf_bytes = pdf.output(dest="S").encode("latin-1")
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_bytes,
                    file_name="lista_precios.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"🚨 Error al generar PDF: {e}")

@st.dialog("📋 Resumen de Deudas Activas")
def formulario_cuentas_por_cobrar(clientes_lista):
    import pandas as pd
    
    st.subheader("💰 Resumen de Deudas Activas")
    
    # 1. Consulta directa a la tabla 'ventas' de Supabase
    try:
        res = supabase.table("ventas").select("*").execute()
        datos_recibidos = res.data if res.data else []
        df_v = pd.DataFrame(datos_recibidos)
    except Exception as e:
        st.error(f"🚨 Error al cargar datos de Supabase: {e}")
        df_v = pd.DataFrame()
        
    if not df_v.empty:
        # Aseguramos el tipo numérico en MONTO($)
        df_v['MONTO($)'] = pd.to_numeric(df_v['MONTO($)'], errors='coerce').fillna(0.0)
        
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
            tasa_bcv = st.number_input("💵 Especificar Tasa Oficial BCV (Bs./$)", min_value=1.0, value=45.0, step=0.01)
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
                # Totales históricos de la base de datos
                movimientos_dict = df_cli.to_dict('records')
                total_creditos = sum(float(m['MONTO($)']) for m in movimientos_dict if str(m.get('TIPO', '')).strip().lower() in ['credito', 'crédito'])
                total_abonos_historicos = abs(sum(float(m['MONTO($)']) for m in movimientos_dict if str(m.get('TIPO', '')).strip().lower() in ['abono']))

                # =========================================================
                # 1. MOTOR INVERSO (CORTE PERFECTO DE CICLO)
                # =========================================================
                historial_recuadro = []
                saldo_acumulado_inverso = 0.0

                # Recorremos de lo más nuevo a lo más viejo para aislar el ciclo activo
                for mov in reversed(movimientos_dict):
                    tipo_mov = str(mov.get('TIPO', '')).strip().lower()
                    monto = float(mov.get('MONTO($)', 0.0))

                    # Formatear fecha corta
                    fecha_completa = str(mov.get('FECHA', ''))
                    fecha_factura = fecha_completa[:10] if " " in fecha_completa or "T" in fecha_completa else fecha_completa

                    mov['fecha'] = fecha_factura
                    if tipo_mov in ['crédito', 'credito']:
                        mov['original'] = abs(monto)
                        mov['abono'] = 0.0
                    elif tipo_mov == 'abono':
                        mov['original'] = 0.0
                        mov['abono'] = abs(monto)
                    else:
                        mov['original'] = 0.0
                        mov['abono'] = 0.0

                    saldo_acumulado_inverso += monto
                    historial_recuadro.append(mov)

                    # Si la suma inversa alcanza o supera la deuda actual, realizamos el corte
                    if saldo_acumulado_inverso >= saldo_real_neto:
                        break

                # Orden cronológico (de más viejo a más nuevo)
                historial_recuadro = historial_recuadro[::-1]

                # Recálculo de la columna 'pendiente'
                saldo_run = 0.0
                for item in historial_recuadro:
                    if str(item.get('TIPO', '')).strip().lower() in ['crédito', 'credito']:
                        saldo_run += float(item.get('MONTO($)', 0.0))
                    else:
                        saldo_run -= abs(float(item.get('MONTO($)', 0.0)))
                    item['pendiente'] = saldo_run

                total_abonos_ciclo = sum(float(n['abono']) for n in historial_recuadro)
                abonos_mostrar = total_abonos_ciclo if total_abonos_ciclo > 0 else 0.0

                # =========================================================
                # 2. MÉTRICAS EN PANTALLA
                # =========================================================
                saldo_en_bs = saldo_real_neto * tasa_bcv

                c1, c2, c3 = st.columns(3)
                c1.metric("TOTAL ABONADO (CICLO)", f"${abonos_mostrar:.2f}")
                c2.metric("SALDO PENDIENTE ($)", f"${saldo_real_neto:.2f}")
                c3.metric("EQUIVALENTE EN BS", f"{saldo_en_bs:,.2f} Bs.")
                st.write("---")

                # =========================================================
                # 3. RECUADRO INTERACTIVO EN PANTALLA
                # =========================================================
                st.markdown("### 📋 Historial Actual de la Cuenta")
                if historial_recuadro:
                    df_mostrar = pd.DataFrame(historial_recuadro)[['FECHA', 'TIPO', 'MONTO($)']]
                    st.table(df_mostrar)
                else:
                    st.info("No hay movimientos activos en este ciclo.")

                # =========================================================
                # 4. BOTÓN PARA GENERAR COMPROBANTE DE COBRO (PDF)
                # =========================================================
                st.write("---")
                st.write("### 📥 Opciones de Exportación:")

                import io
                from reportlab.lib.pagesizes import letter
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib import colors

                def crear_pdf_ayg(cliente, fecha, lineas, saldo_neto, *args, **kwargs):
                    tasa_bcv_val = kwargs.get('tasa_bcv', args[0] if args else 45.0)

                    buffer = io.BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
                    story = []

                    styles = getSampleStyleSheet()

                    title_style = ParagraphStyle(
                        'TitleStyle',
                        parent=styles['Heading1'],
                        fontSize=18,
                        leading=22,
                        alignment=1,
                        spaceAfter=10
                    )
                    subtitle_style = ParagraphStyle(
                        'SubTitleStyle',
                        parent=styles['Normal'],
                        fontSize=12,
                        leading=14,
                        alignment=1,
                        spaceAfter=20
                    )
                    normal_style = ParagraphStyle(
                        'NormalStyle',
                        parent=styles['Normal'],
                        fontSize=11,
                        leading=15,
                        spaceAfter=6
                    )

                    story.append(Paragraph("<b>INVERSIONES AYG 2017 C.A.</b>", title_style))
                    story.append(Paragraph("<b>ESTADO DE CUENTA</b>", subtitle_style))
                    story.append(Spacer(1, 10))

                    story.append(Paragraph(f"<b>FECHA DE EMISIÓN:</b> {fecha}", normal_style))
                    story.append(Paragraph(f"<b>CLIENTE:</b> {cliente}", normal_style))
                    story.append(Spacer(1, 15))
                    story.append(Paragraph("<b>DETALLE DE CUENTAS VIGENTES:</b>", normal_style))
                    story.append(Spacer(1, 5))

                    tabla_datos = [['Fecha', 'Crédito Original', 'Abono Aplicado', 'Saldo Restante']]

                    for item in lineas:
                        abono_str = f"${item['abono']:,.2f}" if item['abono'] > 0 else "$0.00"
                        tabla_datos.append([
                            item['fecha'],
                            f"${item['original']:,.2f}",
                            abono_str,
                            f"${item['pendiente']:,.2f}"
                        ])

                    t = Table(tabla_datos, colWidths=[90, 130, 130, 130])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#fcfcfc')),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 20))

                    total_style = ParagraphStyle(
                        'TotalStyle',
                        parent=styles['Normal'],
                        fontSize=13,
                        leading=16,
                        alignment=2,
                        spaceAfter=25
                    )
                    story.append(Paragraph(f"<b>TOTAL PENDIENTE NETO: ${saldo_neto:,.2f}</b>", total_style))

                    footer_style = ParagraphStyle(
                        'FooterStyle',
                        parent=styles['Normal'],
                        fontSize=10,
                        alignment=1,
                        textColor=colors.gray
                    )
                    story.append(Paragraph("<i>Gracias por su confianza y puntualidad.</i>", footer_style))
                    
                    saldo_en_bs_pdf = saldo_neto * tasa_bcv_val

                    story.append(Spacer(1, 15))
                    story.append(Paragraph(f"<b>Tasa de Cambio Oficial aplicada (BCV):</b> {tasa_bcv_val:.2f} Bs./$", total_style))
                    story.append(Spacer(1, 8))
                    story.append(Paragraph(f"<b>TOTAL NETO A PAGAR EN BOLÍVARES:</b> <font color='green'><b>{saldo_en_bs_pdf:,.2f} Bs.</b></font>", total_style))
                    story.append(Spacer(1, 15))

                    nota_bcv = (
                        "<b>⚠️⚠️ NOTA DE PAGO⚠️⚠️ :</b> Los pagos en bolívares se reciben estrictamente a la tasa oficial "
                        "BCV vigente al momento de la transacción. Todo pago realizado <b>después de las 5:00 pm</b> "
                        "(o durante el fin de semana) se calculará obligatoriamente a la <b>tasa actualizada</b> emitida por "
                        "el BCV para el día hábil siguiente. Evite recargos en su saldo manteniendo sus cuentas al día antes de la hora señalada."
                    )
                    story.append(Paragraph(nota_bcv, footer_style))
                    story.append(Spacer(1, 15))

                    doc.build(story)
                    buffer.seek(0)
                    return buffer.getvalue()

                try:
                    import datetime
                    fecha_pdf = datetime.datetime.now().strftime("%Y-%m-%d")
                    pdf_data = crear_pdf_ayg(cliente_sel, fecha_pdf, historial_recuadro, saldo_real_neto, tasa_bcv)
                    nombre_pdf = f"Estado_Cuenta_{cliente_sel.replace(' ', '_')}_{fecha_pdf}.pdf"

                    st.download_button(
                        label="📥 Descargar Reporte en PDF Profesional",
                        data=pdf_data,
                        file_name=nombre_pdf,
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.warning(f"Error al generar reporte PDF: {e}")
   

@st.dialog("🔒 Control y Cierre de Caja Diario")
def formulario_cierre_de_caja():
    import pandas as pd
    import pytz
    from datetime import datetime
    import time

    st.subheader("🏁 Control y Cierre de Caja Diario")

    # 1. Consulta directa a la tabla 'ventas' en Supabase
    try:
        res = supabase.table("ventas").select("*").execute()
        datos_recibidos = res.data if res.data else []
        df_v = pd.DataFrame(datos_recibidos)
    except Exception as e:
        st.error(f"🚨 Error al cargar datos de Supabase: {e}")
        df_v = pd.DataFrame()

    # --- AJUSTE DE FECHA LOCAL ---
    zona_ve = pytz.timezone('America/Caracas')
    fecha_hoy = datetime.now(zona_ve).strftime('%Y-%m-%d')
    fecha_ve = datetime.now(zona_ve).strftime('%d/%m/%Y')

    st.write(f"📅 **Resumen de Operaciones:** {fecha_ve}")

    if not df_v.empty:
        # Forzamos la conversión a numérico del monto y la extracción limpia de fecha (YYYY-MM-DD)
        df_v['MONTO($)'] = pd.to_numeric(df_v['MONTO($)'], errors='coerce').fillna(0.0)
        df_v['FECHA_CORTA'] = df_v['FECHA'].astype(str).str.slice(0, 10)
        
        # Filtrar operaciones de la jornada de hoy
        df_hoy = df_v[df_v['FECHA_CORTA'] == fecha_hoy]

        if not df_hoy.empty:
            # 1. Clasificación de ventas del día
            # Detal (Entra a caja si es de Contado)
            df_detal_contado = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] == 'CLIENTE DETAL')]
            total_detal = df_detal_contado['MONTO($)'].sum() if not df_detal_contado.empty else 0.0

            # Mayor: Separación entre Contado y Crédito
            df_mayor_contado = df_hoy[(df_hoy['TIPO'] == 'Contado') & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]
            total_mayor_contado = df_mayor_contado['MONTO($)'].sum() if not df_mayor_contado.empty else 0.0

            df_mayor_credito = df_hoy[(df_hoy['TIPO'].isin(['Crédito', 'Credito'])) & (df_hoy['CLIENTE'] != 'CLIENTE DETAL')]
            total_mayor_credito = df_mayor_credito['MONTO($)'].sum() if not df_mayor_credito.empty else 0.0

            total_mayor = total_mayor_contado + total_mayor_credito

            # Abonos recibidos hoy
            df_abonos = df_hoy[df_hoy['TIPO'] == 'Abono']
            total_abonos = df_abonos['MONTO($)'].sum() if not df_abonos.empty else 0.0
            efectivo_abonos = abs(total_abonos)

            # --- MATEMÁTICA REAL DE CAJA FÍSICA ---
            total_liquido_caja = total_detal + total_mayor_contado + efectivo_abonos

            # --- VISUALIZACIÓN EN PANTALLA ---
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
                # Payload para Supabase (se puede guardar en una tabla 'cierres' o 'ventas' según tu diseño)
                payload_cierre = {
                    "fecha": fecha_hoy,
                    "tipo": "CierreCaja",
                    "cliente": "CIERRE DE CAJA",
                    "monto_mismo": float(total_liquido_caja),
                    "monto($)": float(total_liquido_caja),
                    "descripcion": f"Cierre Caja | Detal: ${total_detal:.2f} | Mayor: ${total_mayor:.2f} | Abonos: ${efectivo_abonos:.2f} | Notas: {observaciones}"
                }

                try:
                    # Guardar el registro del cierre en Supabase (ejemplo en la tabla 'cierres' o 'ventas')
                    res_insert = supabase.table("cierres").insert(payload_cierre).execute()
                    
                    if res_insert.data:
                        st.success("🏁 ¡Cierre de caja guardado con éxito en Supabase!")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("Hubo un inconveniente al registrar el cierre. Intenta de nuevo.")
                except Exception as e:
                    st.error(f"❌ Error al guardar en Supabase: {e}")
        else:
            st.info("Aún no se han registrado ventas ni abonos en la jornada de hoy.")
    else:
        st.info("No se encontraron registros históricos de ventas.")


@st.dialog("🍞 Simulador Unificado de Costos e Insumos")
def formulario_simulador_costos():
    import pandas as pd
    import streamlit as st
    
    st.subheader("🍞 Simulador Unificado de Costos e Insumos")
    st.write("Calcula en tiempo real el costo bruto, operativo y sugerencia de PVP para tu producción.")

    RECETAS_BASE = {
        "Pan Salado": {"HARINA": 45.0, "AGUA": 18.0, "AZUCAR": 3.0, "SAL": 1.0, "MANTECA": 2.0, "LEVADURA": 0.3, "peso_base": 0.25, "unidades_paquete": 1},
        "Pan de Perro": {"HARINA": 50.0, "AGUA": 19.0, "AZUCAR": 5.0, "SAL": 1.0, "MANTECA": 1.7, "LEVADURA": 0.25, "peso_base": 0.05, "unidades_paquete": 12},
        "Polvorosas": {"HARINA": 4.5, "PVP": 0.5, "AZUCAR": 2.0, "AGUA": 0.0, "MANTECA": 2.5, "peso_base": 0.04, "unidades_paquete": 1},
        "Catalinas": {"HARINA": 5.0, "SODA": 0.5, "MIELINA": 3.5, "MELAO PAPELON": 2.0, "AGUA": 2.0, "ESENCIAS": 0.1, "peso_base": 0.04, "unidades_paquete": 6},
        "Receta Brownie": {"HARINA": 2.0, "AGUA": 1.0, "AZUCAR": 3.0, "MANTECA": 1.0, "CACAO": 1.0, "HUEVOS": 1.2, "peso_base": 0.5, "unidades_paquete": 1},
        "Pudín": {"HARINA": 10.0, "LECHE": 5.0, "AZUCAR": 4.0, "HUEVOS": 1.5, "ESENCIAS": 0.2, "peso_base": 0.50, "unidades_paquete": 1},
        "Banquete (50 und)": {"HARINA": 5.0, "AGUA": 2.0, "AZUCAR": 0.5, "SAL": 0.1, "MANTECA": 0.4, "LEVADURA": 0.1, "peso_base": 0.03, "unidades_paquete": 50},
        "Pan de Dulce": {"HARINA": 1.0, "AGUA": 1.0, "AZUCAR": 1.0, "ANIS-DULCE": 1.0, "MANTECA": 1.0, "LEVADURA": 0.1, "peso_base": 0.25, "unidades_paquete": 1}
    }

    opciones_productos = list(RECETAS_BASE.keys())
    producto_con_clave = st.selectbox("Selecciona el producto a producir:", opciones_productos, key="sim_prod_sel")
    receta = RECETAS_BASE[producto_con_clave]

    st.subheader(f"🥣 Ajustar Ingredientes para: {producto_con_clave}")

    # 🟢 1. CÓDIGO SUPABASE: Cargar tabla de insumos desde la base de datos
    try:
        res = supabase.table("costos").select("*").execute()
        datos_recibidos = res.data if res.data else []
        df_costos_real = pd.DataFrame(datos_recibidos)
    except Exception as e:
        st.error(f"🚨 Error al consultar la tabla de insumos en Supabase: {e}")
        df_costos_real = pd.DataFrame()

    ingredientes_modificados = {}

    # Interfaz en dos columnas para adaptarse a dispositivos móviles
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📝 Cantidad de Insumos (Kg / Unidades):**")
        for ingrediente, cant_base in receta.items():
            if ingrediente not in ["peso_base", "unidades_paquete"]:
                cant_actual = st.number_input(
                    f"{ingrediente}:",
                    min_value=0.0,
                    value=float(cant_base),
                    step=0.1,
                    key=f"input_sim_{ingrediente}"
                )
                ingredientes_modificados[ingrediente] = cant_actual

    with col2:
        st.markdown("**📦 Configuración Física del Producto:**")
        peso_pan = st.number_input("Peso por unidad en crudo (Kg):", min_value=0.001, value=float(receta["peso_base"]), step=0.01, key="sim_peso_pan")
        unidades_paquete = st.number_input("Unidades por paquete terminado:", min_value=1, value=int(receta["unidades_paquete"]), step=1, key="sim_und_paquete")

        st.markdown("**💰 Costos Operativos y Extras:**")
        costo_mano_obra = st.number_input("Mano de Obra de la tanda ($):", min_value=0.0, value=0.0, step=0.5, key="sim_mo")
        costo_gas = st.number_input("Costo de Gas / Energía ($):", min_value=0.0, value=0.0, step=0.5, key="sim_gas")
        costo_bolsa = st.number_input("Costo por cada Bolsa de empaque ($):", min_value=0.0, value=0.05, step=0.01, key="sim_bolsa")

    # 🟢 2. CÁLCULO MATEMÁTICO CON CONSULTA DE PRECIOS EN SUPABASE
    costo_materia_prima_total = 0.0

    if not df_costos_real.empty:
        # Pre-procesamiento de nombres de insumos para búsqueda insensible a mayúsculas/espacios
        df_costos_real['insumo_clean'] = df_costos_real['nombre'].astype(str).str.upper().str.strip()

    for ingrediente, cant_actual in ingredientes_modificados.items():
        costo_unitario = 1.0  # Valor base por defecto

        if not df_costos_real.empty:
            busqueda = str(ingrediente).upper().strip()
            resultado = df_costos_real[df_costos_real['insumo_clean'].str.contains(busqueda, na=False)]

            if not resultado.empty:
                try:
                    # Toma el costo unitario/kg registrado en la columna 'precio_unitario' o 'costo'
                    col_costo = 'costo_unitario' if 'costo_unitario' in resultado.columns else 'precio'
                    val_costo = resultado.iloc[0][col_costo]
                    costo_unitario = float(val_costo)
                except Exception:
                    costo_unitario = 1.0

        costo_materia_prima_total += cant_actual * costo_unitario

    # Operaciones de Rendimiento Automatizadas
    total_kilos_mezcla = sum(ingredientes_modificados.values())
    cantidad_unidades_totales = int(total_kilos_mezcla / peso_pan) if peso_pan > 0 else 0
    total_paquetes = cantidad_unidades_totales / unidades_paquete if unidades_paquete > 0 else 0
    costo_operativo_total = costo_materia_prima_total + costo_mano_obra + costo_gas

    if cantidad_unidades_totales > 0:
        costo_por_unidad_bruto = costo_operativo_total / cantidad_unidades_totales
        costo_por_paquete = (costo_por_unidad_bruto * unidades_paquete) + costo_bolsa
    else:
        costo_por_unidad_bruto = 0.0
        costo_por_paquete = 0.0

    # 🟢 3. REPORTE FINAL EN PANTALLA
    st.write("---")
    st.subheader("📊 Reporte Técnico de Rendimiento y Costo Real")

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

    # Calculador interactivo de ganancias y PVP sugerido
    st.subheader("💰 Calculador Interactivo de Ganancias")
    margen_deseado = st.slider("Selecciona tu porcentaje de ganancia ideal (%):", min_value=10, max_value=150, value=30, key="sim_margen")

    factor_ganancia = 1 + (margen_deseado / 100)
    pvp_unidad_sugerido = costo_por_unidad_bruto * factor_ganancia
    pvp_paquete_sugerido = costo_por_paquete * factor_ganancia

    col_pvp1, col_pvp2 = st.columns(2)
    with col_pvp1:
        st.success(f"**PVP Sugerido por Unidad:**\n\n${pvp_unidad_sugerido:.2f}")
    with col_pvp2:
        st.success(f"**PVP Sugerido por Paquete (Mayor):**\n\n${pvp_paquete_sugerido:.2f}")


import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# =========================================================
# 🔒 VALIDACIÓN DE SESIÓN Y LOGO
# =========================================================
if not check_password():
    st.stop()

st.image("1000317144.jpg.png", use_container_width=True)

if "pantalla" not in st.session_state:
    st.session_state.pantalla = "Menu Principal"

st.markdown("---")

# =========================================================
# 🔄 CARGA GLOBAL DE DATOS DESDE SUPABASE
# =========================================================
try:
    res_cli = supabase.table("clientes").select("nombre").execute()
    clientes_lista = [c['nombre'] for c in res_cli.data] if res_cli.data else []
except Exception:
    clientes_lista = []

try:
    res_prod = supabase.table("productos").select("nombre, precio, stock").execute()
    productos_dict = {p['nombre']: {'precio': p['precio'], 'stock': p['stock']} for p in res_prod.data} if res_prod.data else {}
except Exception:
    productos_dict = {}

# =========================================================
# 🔲 PANTALLA PRINCIPAL: TABLERO DE BOTONES
# =========================================================
if st.session_state.pantalla == "Menu Principal":

    st.subheader("🎛️ SISTEMA AYG2017")
    
    # 🏪 Fila 1: Ventas
    st.success("🏪 SECCIÓN DE VENTAS")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏪\n\nVenta Detal", key="btn_detal", use_container_width=True):
            formulario_venta_detal(clientes_lista)

    with col2:
        if st.button("🚗\n\nVenta Mayor", key="btn_mayor", use_container_width=True):
            formulario_venta_mayor(clientes_lista, productos_dict)

    # 💰 Fila 2: Gestión e Inventario
    st.info("💰 GESTIÓN E INVENTARIO")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("💰\n\nCuentas y Abonos", key="btn_abonos", use_container_width=True):
            formulario_cuentas_abonos(clientes_lista)

    with col4:
        if st.button("📦\n\nInventario", key="btn_inventario", use_container_width=True):
            formulario_inventario(productos_dict, clientes_lista)

    # 🗂️ Fila 3: Reportes y Cierre
    st.warning("🗂️ REPORTES Y CIERRE")
    col5, col6 = st.columns(2)
    with col5:
        if st.button("📝\n\nCuentas por Cobrar", key="btn_cobrar", use_container_width=True):
            formulario_cuentas_por_cobrar(clientes_lista)

    with col6:
        if st.button("🔒\n\nCierre de Caja", key="btn_cierre", use_container_width=True):
            formulario_cierre_de_caja()

    # 🛠️ Fila 4: Herramientas
    st.error("🛠️ HERRAMIENTAS ADICIONALES")
    if st.button("📊\n\nSimulador Costos", key="btn_simulador", use_container_width=True):
        formulario_simulador_costos()

    st.markdown("---")
    
    if st.button("🚪 Cerrar Sesión / Salir", key="btn_salir", use_container_width=True, type="primary"):
        st.session_state["password_correct"] = False
        st.query_params.clear()
        st.rerun()



# =========================================================
# 📲 NAVEGACIÓN SECUNDARIA (PANTALLAS INTERNAS)
# =========================================================
else:
    if st.button("⬅️ Volver al Menú Principal", key="btn_volver"):
        st.session_state.pantalla = "Menu Principal"
        st.rerun()
    st.markdown("---")

    # 1. VENTA DETAL
    if st.session_state.pantalla == "Venta Detal":
        st.header("🏪 Venta Rápida (Detal)")
        with st.form("detal"):
            c = st.selectbox("Cliente", clientes_lista) if clientes_lista else st.selectbox("Cliente", ["CLIENTE DETAL"])
            m = st.number_input("Monto Total $", min_value=0.0)
            cond = st.selectbox("Condición", ["Contado", "Crédito"])
            if st.form_submit_button("REGISTRAR VENTA"):
                zona_ve = pytz.timezone('America/Caracas')
                fecha_ve = datetime.now(zona_ve).strftime("%Y-%m-%d")
                supabase.table("ventas").insert({
                    "fecha": fecha_ve,
                    "tipo": cond,
                    "cliente": c,
                    "monto": m
                }).execute()
                st.success("✅ Venta guardada correctamente en Supabase")

    # 2. VENTA MAYOR (SAYG)
    elif st.session_state.pantalla == "Venta Mayor (SAYG)":
        st.header("📦 Pedido al Mayor")
        cli_m = st.selectbox("Seleccionar Cliente", clientes_lista) if clientes_lista else st.selectbox("Seleccionar Cliente", ["CLIENTE GENERAL"])
        
        col1, col2 = st.columns(2)
        
        if isinstance(productos_dict, dict) and len(productos_dict) > 0:
            prod_nom = col1.selectbox("Producto", list(productos_dict.keys()))
            
            if prod_nom and prod_nom in productos_dict:
                val = productos_dict[prod_nom]
                
                if isinstance(val, dict):
                    precio_u = float(val.get('precio', 0.0))
                    stock_actual = float(val.get('stock', 0.0))
                else:
                    precio_u = float(val) if val is not None else 0.0
                    stock_actual = 0.0

                st.info(f"💰 Precio: ${precio_u:.2f} | 📦 Stock: {stock_actual:.2f}")
                
                cant = col2.number_input(
                    "Cantidad", 
                    min_value=0.0, 
                    max_value=max(stock_actual, 1.0), 
                    step=0.001, 
                    format="%.3f"
                )

                if st.button("➕ Agregar al Carrito"):
                    if 'carro' not in st.session_state: 
                        st.session_state.carro = []
                    st.session_state.carro.append({
                        "Producto": prod_nom, 
                        "Cant": cant, 
                        "Precio": precio_u, 
                        "Subtotal": cant * precio_u
                    })
        else:
            st.warning("⚠️ No hay productos registrados en la base de datos de Supabase.")

        if 'carro' in st.session_state and st.session_state.carro:
            st.table(pd.DataFrame(st.session_state.carro))
            t_final = sum(i['Subtotal'] for i in st.session_state.carro)
            st.subheader(f"Total: ${t_final:.2f}")

            if st.button("🗑️ Vaciar Carrito"):
                st.session_state.carro = []
                st.rerun()

            if st.button("🔒 FINALIZAR VENTA"):
                zona_ve = pytz.timezone('America/Caracas')
                fecha_ve = datetime.now(zona_ve).strftime("%Y-%m-%d")
                supabase.table("ventas").insert({
                    "fecha": fecha_ve,
                    "tipo": "Crédito",
                    "cliente": cli_m,
                    "monto": t_final
                }).execute()
                st.success("✅ Venta registrada con éxito")
                st.session_state.carro = []

    # 3. CUENTAS Y ABONOS
    elif st.session_state.pantalla == "Cuentas y Abonos":
        st.header("💰 Registro de Abonos")
        cli_a = st.selectbox("Cliente", clientes_lista) if clientes_lista else st.selectbox("Cliente", ["CLIENTE GENERAL"])
        monto_a = st.number_input("Monto del Abono $", min_value=0.0)
        if st.button("REGISTRAR ABONO"):
            zona_ve = pytz.timezone('America/Caracas')
            fecha_ve = datetime.now(zona_ve).strftime("%Y-%m-%d")
            supabase.table("ventas").insert({
                "fecha": fecha_ve,
                "tipo": "Abono",
                "cliente": cli_a,
                "monto": -monto_a
            }).execute()
            st.success(f"✅ Abono de ${monto_a:.2f} registrado")

    # 4. INVENTARIO
    elif st.session_state.pantalla == "Inventario":
        st.header("📦 Gestión de Almacén, Costos y Registros")
        tab_almacen, tab_insumos, tab_productos, tab_clientes = st.tabs([
            "📋 Estado del Almacén", "🍎 Materia Prima", "🥖 Nuevos Productos", "🤝 Nuevos Clientes"
        ])
        
        with tab_almacen:
            res = supabase.table("productos").select("nombre, precio, stock").execute()
            if res.data:
                st.table(pd.DataFrame(res.data))
            else:
                st.info("Sin productos registrados.")

        with tab_clientes:
            with st.form("form_cli", clear_on_submit=True):
                nom_c = st.text_input("Nombre de la Bodega o Cliente:")
                if st.form_submit_button("Guardar Cliente") and nom_c:
                    supabase.table("clientes").insert({"nombre": nom_c}).execute()
                    st.success("🟢 Cliente guardado")

    # 5. CIERRE DE CAJA
    elif st.session_state.pantalla == "Cierre de Caja":
        st.header("🗄️ Control y Cierre de Caja Diario")
        zona_ve = pytz.timezone('America/Caracas')
        fecha_hoy = datetime.now(zona_ve).strftime('%Y-%m-%d')
        
        res_v = supabase.table("ventas").select("*").eq("fecha", fecha_hoy).execute()
        df_hoy = pd.DataFrame(res_v.data) if res_v.data else pd.DataFrame()

        if not df_hoy.empty:
            total_detal = df_hoy[(df_hoy['tipo'] == 'Contado') & (df_hoy['cliente'] == 'CLIENTE DETAL')]['monto'].sum()
            total_mayor_contado = df_hoy[(df_hoy['tipo'] == 'Contado') & (df_hoy['cliente'] != 'CLIENTE DETAL')]['monto'].sum()
            total_mayor_credito = df_hoy[(df_hoy['tipo'] == 'Crédito') & (df_hoy['cliente'] != 'CLIENTE DETAL')]['monto'].sum()
            total_abonos = abs(df_hoy[df_hoy['tipo'] == 'Abono']['monto'].sum())

            total_liquido = total_detal + total_mayor_contado + total_abonos

            c1, c2, c3 = st.columns(3)
            c1.metric("Venta Detal Hoy", f"${total_detal:.2f}")
            c2.metric("Venta Mayor Hoy", f"${(total_mayor_contado + total_mayor_credito):.2f}")
            c3.metric("Abonos Recibidos", f"${total_abonos:.2f}")

            st.markdown(f"### 💵 Total Efectivo Esperado: **${total_liquido:.2f}**")
        else:
            st.info("No hay ventas ni abonos registrados el día de hoy.")
