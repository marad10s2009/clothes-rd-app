import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# =========================================================
# CONFIGURACIÓN DE LA PÁGINA
# =========================================================
st.set_page_config(
    page_title="Clothes.RD - Marketplace",
    page_icon="🏷️",
    layout="centered"
)

# =========================================================
# CONEXIÓN A GOOGLE SHEETS
# =========================================================
conexion = st.connection("gsheets", type=GSheetsConnection)

# =========================================================
# CLASE 2: FUNCIONES PROPIAS (Mínimo 4 funciones)
# =========================================================

def validar_datos(vendedor, prenda, imagen_url):
    """Función 1: Valida que los campos de texto obligatorios no estén vacíos."""
    if not vendedor.strip():
        return False, "El nombre del vendedor o tienda no puede estar vacío."
    if not prenda.strip():
        return False, "El nombre de la prenda es obligatorio."
    if not imagen_url.strip() or not imagen_url.startswith("http"):
        return False, "Ingresa una URL de imagen válida (debe comenzar con http)."
    return True, "Datos validados correctamente."


def calcular_precio_final(precio_original, es_cyber, Porcentaje_descuento):
    """Función 2: Aplica condicionales y operaciones matemáticas para el descuento."""
    if es_cyber:
        descuento = precio_original * (Porcentaje_descuento / 100)
        precio_final = int(precio_original - descuento)
        return precio_final
    return int(precio_original)


def guardar_registro(nuevo_registro_dict):
    """Función 3: Lee la base de datos, concatena el nuevo registro y actualiza Google Sheets."""
    datos_actuales = conexion.read(worksheet="Registros", ttl=0)
    nueva_fila = pd.DataFrame([nuevo_registro_dict])
    datos_actualizados = pd.concat([datos_actuales, nueva_fila], ignore_index=True)
    conexion.update(worksheet="Registros", data=datos_actualizados)
    st.cache_data.clear()


def obtener_estadisticas_inventario(df_productos):
    """Función 4: Recorre o procesa los datos para devolver métricas al usuario."""
    total_prendas = len(df_productos)
    if total_prendas == 0:
        return 0, 0
    precio_promedio = int(df_productos["PrecioOriginal"].mean())
    return total_prendas, precio_promedio


# =========================================================
# CLASE 4 & 5: INTERFAZ Y FLUJO PRINCIPAL
# =========================================================

st.title("🏷️ Clothes.RD")
st.write("Plataforma para registrar, gestionar y publicar ropa con ofertas dinámicas Cyber Day.")

# Pestañas de la aplicación
tab_catalogo, tab_publicar, tab_cyber = st.tabs(["🛒 Catálogo", "➕ Publicar Ropa", "⚙️ Panel Cyber"])

# ---------------------------------------------------------
# PESTAÑA 1: CATÁLOGO DE PRODUCTOS
# ---------------------------------------------------------
with tab_catalogo:
    st.subheader("Catálogo de Productos")
    try:
        df_productos = conexion.read(worksheet="Registros", ttl=0)
    except Exception as e:
        st.error("Error al cargar Google Sheets. Verifica tus credenciales en secrets.toml")
        df_productos = pd.DataFrame()

    # Métrica rápida
    total_items, promedio_precio = obtener_estadisticas_inventario(df_productos)
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total Prendas en Venta", total_items)
    col_m2.metric("Precio Promedio (Regular)", f"RD$ {promedio_precio:,}")

    st.divider()

    if df_productos.empty:
        st.info("No hay prendas registradas aún en Clothes.RD. ¡Sé el primero en publicar!")
    else:
        # Pestaña de filtrado por categoría
        categorias = ["Todas"] + list(df_productos["Categoria"].unique())
        cat_seleccionada = st.selectbox("Filtrar por categoría:", categorias)

        if cat_seleccionada != "Todas":
            df_filtrado = df_productos[df_productos["Categoria"] == cat_seleccionada]
        else:
            df_filtrado = df_productos

        # Mostrar prendas
        for idx, row in df_filtrado.iterrows():
            with st.container():
                col_img, col_det = st.columns([1, 2])
                with col_img:
                    st.image(row["Imagen"], use_container_width=True)
                with col_det:
                    st.markdown(f"### {row['Prenda']}")
                    st.write(f"**Vendedor:** {row['Vendedor']} | **Categoría:** {row['Categoria']} | **Talla:** {row['Talla']}")
                    
                    # Mostrar precio normal vs oferta
                    precio_orig = int(row["PrecioOriginal"])
                    precio_fin = int(row["PrecioFinal"])
                    if precio_fin < precio_orig:
                        st.write(f"~~RD$ {precio_orig:,}~~ ➔ **RD$ {precio_fin:,}** 🏷️ *(¡Oferta Cyber!)*")
                    else:
                        st.write(f"**Precio:** RD$ {precio_orig:,}")
                    
                    if st.button(f"Comprar {row['Prenda']}", key=f"btn_{idx}"):
                        st.success(f"¡Has seleccionado comprar **{row['Prenda']}**! Contacta al vendedor: {row['Vendedor']}.")
                st.divider()

# ---------------------------------------------------------
# PESTAÑA 2: FORMULARIO DE PUBLICACIÓN
# ---------------------------------------------------------
with tab_publicar:
    st.subheader("Publica una nueva prenda")
    
    # Formulario agrupado
    with st.form("form_nueva_prenda", clear_on_submit=True):
        vendedor = st.text_input("Nombre de la Tienda / Vendedor")
        prenda = st.text_input("Nombre de la Prenda (ej. Jacket de Mezclilla)")
        categoria = st.selectbox("Categoría", ["Poleras / Tops", "Pantalones / Jeans", "Vestidos", "Chaquetas", "Calzado", "Accesorios"])
        talla = st.selectbox("Talla", ["XS", "S", "M", "L", "XL", "Única"])
        precio_original = st.number_input("Precio Regular (RD$)", min_value=100, step=100, value=1500)
        
        # Cyber Activo Check en formulario
        es_cyber = st.checkbox("¿Aplicar oferta Cyber Day a esta publicación?", value=False)
        pct_descuento = st.slider("Porcentaje de Descuento si es Cyber (%)", 5, 80, 20)
        
        imagen_url = st.text_input(
            "URL de la imagen (debe ser un enlace público .jpg o .png)",
            value="https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500"
        )
        
        btn_submit = st.form_submit_button("Publicar en Clothes.RD")

    # Acción de guardado e integración
    if btn_submit:
        es_valido, mensaje_val = validar_datos(vendedor, prenda, imagen_url)
        if not es_valido:
            st.error(mensaje_val)
        else:
            precio_final = calcular_precio_final(precio_original, es_cyber, pct_descuento)
            
            registro_dict = {
                "Vendedor": vendedor.strip(),
                "Prenda": prenda.strip(),
                "Categoria": categoria,
                "Talla": talla,
                "PrecioOriginal": int(precio_original),
                "PrecioFinal": int(precio_final),
                "Imagen": imagen_url.strip()
            }
            
            with st.spinner("Guardando en Google Sheets..."):
                try:
                    guardar_registro(registro_dict)
                    st.success("¡Tu prenda se ha publicado y guardado exitosamente en la base de datos!")
                    st.balloons()
                except Exception as err:
                    st.error(f"Error al conectar con Google Sheets: {err}")

# ---------------------------------------------------------
# PESTAÑA 3: PANEL CYBER
# ---------------------------------------------------------
with tab_cyber:
    st.subheader("Configuración de Promociones")
    
    password_cyber = st.text_input("Ingresa la contraseña de administrador:", type="password")
    
    if password_cyber == "admin123":
        st.info("Utiliza este panel para calcular rápidamente precios con descuentos de temporada antes de subirlos.")
        
        p_demo = st.number_input("Simulador de Precio (RD$)", value=2000, step=100)
        desc_demo = st.slider("Descuento Cyber (%)", 5, 80, 25)
        
        precio_con_desc = calcular_precio_final(p_demo, True, desc_demo)
        ahorro = p_demo - precio_con_desc
        
        st.metric("Precio Original", f"RD$ {p_demo:,}")
        st.metric("Precio con Descuento Cyber", f"RD$ {precio_con_desc:,}", delta=f"-RD$ {ahorro:,}")
    elif password_cyber != "":
        st.error("Contraseña incorrecta.")
    else:
        st.info("Ingresa la contraseña para desplegar el panel.")
