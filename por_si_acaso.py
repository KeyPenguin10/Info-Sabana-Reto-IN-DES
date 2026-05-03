import io
import re
import unicodedata
from datetime import datetime, time

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="CertiDoc Ingeniería",
    page_icon="🎓",
    layout="wide"
)

SEMANAS_CICLO = 16

st.title("🎓 CertiDoc Ingeniería")
st.write(
    "Sistema automatizado para consultar, consolidar y procesar programación académica histórica por docente."
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    """
    Convierte texto a mayúsculas, sin tildes y sin espacios extra.
    Sirve para comparar columnas, nombres, materias, días, etc.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def limpiar_codigo(valor):
    """
    Limpia códigos como documento, id profesor, número de clase, sección combinada.
    Evita problemas tipo 80243251.0
    """
    if pd.isna(valor):
        return ""

    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    texto = re.sub(r"\s+", "", texto)
    return texto


def quitar_ceros_izquierda(codigo):
    """
    Permite que Id profesor funcione aunque Excel lo lea como número
    y pierda ceros a la izquierda.
    """
    codigo = limpiar_codigo(codigo)

    if codigo == "":
        return ""

    sin_ceros = codigo.lstrip("0")

    if sin_ceros == "":
        return "0"

    return sin_ceros


def valor_no_vacio(valor):
    if pd.isna(valor):
        return False

    texto = str(valor).strip()

    if texto == "":
        return False

    if texto.upper() in ["NAN", "NONE", "NULL"]:
        return False

    return True


def primero_no_vacio(serie):
    for valor in serie:
        if valor_no_vacio(valor):
            return valor
    return ""


def formatear_valor(valor):
    """
    Limpia valores para mostrarlos bien.
    """
    if pd.isna(valor):
        return ""

    if isinstance(valor, float) and valor.is_integer():
        return str(int(valor))

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def parsear_periodo(valor):
    """
    Convierte valores como:
    - PERIODO 2022-2
    - 2022-2
    - 2022.2
    - 2022/2
    - 20222

    En:
    - periodo_limpio: 2022-2
    - periodo_orden: 20222
    """
    if pd.isna(valor):
        return "", None

    texto_original = str(valor).strip()
    texto = normalizar_texto(texto_original)
    texto = texto.replace(",", ".")

    encontrado = re.search(r"(19\d{2}|20\d{2})\s*[-_/. ]\s*([1-2])", texto)

    if encontrado:
        anio = int(encontrado.group(1))
        ciclo = int(encontrado.group(2))
        return f"{anio}-{ciclo}", anio * 10 + ciclo

    encontrado = re.search(r"(19\d{2}|20\d{2})([1-2])", texto)

    if encontrado:
        anio = int(encontrado.group(1))
        ciclo = int(encontrado.group(2))
        return f"{anio}-{ciclo}", anio * 10 + ciclo

    return texto_original, None


def hora_a_minutos(valor):
    """
    Convierte horas a minutos desde medianoche.

    Soporta formatos como:
    - 02:00:PM
    - 02:00 PM
    - 02:00PM
    - 14:00
    - 14:00:00
    - datetime.time
    - números de Excel
    """
    if pd.isna(valor):
        return None

    if isinstance(valor, time):
        return valor.hour * 60 + valor.minute + valor.second / 60

    if isinstance(valor, datetime) or isinstance(valor, pd.Timestamp):
        return valor.hour * 60 + valor.minute + valor.second / 60

    if isinstance(valor, (int, float)):
        numero = float(valor)

        # Hora de Excel como fracción del día: 0.5 = 12:00
        if 0 <= numero < 1:
            return round(numero * 24 * 60)

        # Hora decimal: 14.5 = 14:30
        if 0 <= numero <= 24:
            return round(numero * 60)

        # Fecha serial de Excel con fracción horaria
        fraccion = numero % 1
        if fraccion > 0:
            return round(fraccion * 24 * 60)

        return None

    texto = str(valor).strip().upper()

    if texto in ["", "NAN", "NONE", "NULL"]:
        return None

    texto = texto.replace(" ", "")
    texto = texto.replace("A.M.", "AM")
    texto = texto.replace("P.M.", "PM")
    texto = texto.replace("A.M", "AM")
    texto = texto.replace("P.M", "PM")
    texto = texto.replace("A. M.", "AM")
    texto = texto.replace("P. M.", "PM")
    texto = texto.replace("A. M", "AM")
    texto = texto.replace("P. M", "PM")

    # Formato especial del Excel: 02:00:PM
    texto = re.sub(r"(\d{1,2}):(\d{2}):?(AM|PM)$", r"\1:\2\3", texto)

    # Formato: 02:00PM, 02:00:00PM, 14:00, 14:00:00
    encontrado = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?(AM|PM)?$", texto)

    if encontrado:
        hora = int(encontrado.group(1))
        minuto = int(encontrado.group(2))
        ampm = encontrado.group(4)

        if ampm == "PM" and hora != 12:
            hora += 12

        if ampm == "AM" and hora == 12:
            hora = 0

        if 0 <= hora <= 23 and 0 <= minuto <= 59:
            return hora * 60 + minuto

    # Formato simple: 2PM, 11AM
    encontrado = re.match(r"^(\d{1,2})(AM|PM)$", texto)

    if encontrado:
        hora = int(encontrado.group(1))
        ampm = encontrado.group(2)

        if ampm == "PM" and hora != 12:
            hora += 12

        if ampm == "AM" and hora == 12:
            hora = 0

        if 0 <= hora <= 23:
            return hora * 60

    # Formato simple: 14
    if re.match(r"^\d{1,2}$", texto):
        hora = int(texto)

        if 0 <= hora <= 23:
            return hora * 60

    return None


def minutos_a_hora(minutos):
    if minutos is None or pd.isna(minutos):
        return ""

    minutos = int(round(minutos))
    hora = minutos // 60
    minuto = minutos % 60

    return f"{hora:02d}:{minuto:02d}"


def unir_intervalos(intervalos):
    """
    Une intervalos solapados o consecutivos.

    Ejemplo:
    10:00-11:00
    11:00-12:00
    12:00-13:00
    => 10:00-13:00 = 3 horas

    Ejemplo:
    10:00-12:00
    11:00-13:00
    => 10:00-13:00 = 3 horas
    """
    intervalos_limpios = []

    for inicio, fin in intervalos:
        if inicio is None or fin is None:
            continue

        try:
            inicio = float(inicio)
            fin = float(fin)
        except Exception:
            continue

        if fin <= inicio:
            continue

        intervalos_limpios.append((inicio, fin))

    intervalos_limpios = sorted(intervalos_limpios, key=lambda x: x[0])

    unidos = []

    for inicio, fin in intervalos_limpios:
        if not unidos:
            unidos.append([inicio, fin])
        else:
            ultimo = unidos[-1]

            # Se solapan o se tocan
            if inicio <= ultimo[1]:
                ultimo[1] = max(ultimo[1], fin)
            else:
                unidos.append([inicio, fin])

    horas = sum((fin - inicio) / 60 for inicio, fin in unidos)

    return horas, unidos


def parsear_fecha(valor):
    if pd.isna(valor):
        return pd.NaT

    try:
        return pd.to_datetime(valor, errors="coerce", dayfirst=True)
    except Exception:
        return pd.NaT


def formatear_fecha(valor):
    fecha = parsear_fecha(valor)

    if pd.notna(fecha):
        return fecha.strftime("%d/%m/%Y")

    if valor_no_vacio(valor):
        return str(valor).strip()

    return ""


def combinar_fechas(grupo, col_fecha_inicial, col_fecha_final):
    """
    Une fecha inicial y fecha final en una sola columna:
    fecha inicial - fecha final
    """
    fechas_inicio = grupo[col_fecha_inicial].apply(parsear_fecha)
    fechas_final = grupo[col_fecha_final].apply(parsear_fecha)

    fecha_inicio_min = fechas_inicio.min()
    fecha_final_max = fechas_final.max()

    if pd.notna(fecha_inicio_min):
        inicio = fecha_inicio_min.strftime("%d/%m/%Y")
    else:
        inicio = formatear_fecha(primero_no_vacio(grupo[col_fecha_inicial]))

    if pd.notna(fecha_final_max):
        final = fecha_final_max.strftime("%d/%m/%Y")
    else:
        final = formatear_fecha(primero_no_vacio(grupo[col_fecha_final]))

    if inicio and final:
        return f"{inicio} - {final}"

    if inicio:
        return inicio

    if final:
        return final

    return ""


def normalizar_nombre_columna(columna):
    """
    Normalización especial para encontrar columnas ignorando:
    - tildes
    - mayúsculas/minúsculas
    - espacios extra
    - símbolos simples
    """
    texto = normalizar_texto(columna)
    texto = texto.replace("°", "")
    texto = texto.replace("º", "")
    texto = re.sub(r"[^A-Z0-9 ]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def encontrar_columna(df, nombres_posibles):
    """
    Busca una columna en el Excel usando nombres posibles.
    No le pide al usuario mapear columnas manualmente.
    """
    columnas = list(df.columns)

    mapa_columnas = {
        normalizar_nombre_columna(col): col
        for col in columnas
    }

    # Coincidencia exacta normalizada
    for nombre in nombres_posibles:
        nombre_norm = normalizar_nombre_columna(nombre)

        if nombre_norm in mapa_columnas:
            return mapa_columnas[nombre_norm]

    # Coincidencia parcial
    for nombre in nombres_posibles:
        nombre_norm = normalizar_nombre_columna(nombre)

        for col_norm, col_original in mapa_columnas.items():
            if nombre_norm in col_norm or col_norm in nombre_norm:
                return col_original

    return None


def validar_columnas_requeridas(df):
    """
    Define las columnas que el sistema espera encontrar automáticamente.
    """
    columnas_esperadas = {
        "Ciclo Lectivo": [
            "Ciclo Lectivo",
            "Periodo Lectivo",
            "Periodo"
        ],
        "Nombre del curso": [
            "Nombre del curso",
            "Nombre curso",
            "Curso",
            "Asignatura",
            "Materia"
        ],
        "Componente": [
            "Componente"
        ],
        "Descripción Materia": [
            "Descripción Materia",
            "Descripcion Materia",
            "Componente Descripción",
            "Componente Descripcion"
        ],
        "Fecha inicial": [
            "Fecha inicial",
            "Fecha Inicial",
            "F Inicial",
            "F Inicia",
            "Fecha Inicio"
        ],
        "Fecha final": [
            "Fecha final",
            "Fecha Final",
            "Fecha Fin",
            "F Final"
        ],
        "Número documento docente": [
            "Número documento docente",
            "Numero documento docente",
            "Documento docente",
            "Numero documento docent",
            "Número documento docent"
        ],
        "Id profesor": [
            "Id profesor",
            "Id profes",
            "ID Profesor",
            "ID Profes"
        ],
        "Nombre profesor": [
            "Nombre profesor",
            "Nombre Profesor",
            "Profesor",
            "Docente"
        ],
        "Número de Clase": [
            "Número de Clase",
            "Numero de Clase",
            "N° Clase",
            "Nº Clase",
            "N Clase",
            "No Clase",
            "Nro Clase"
        ],
        "ID Sección Combinada": [
            "ID Sección Combinada",
            "ID Seccion Combinada",
            "Sección Combinada",
            "Seccion Combinada"
        ],
        "Día": [
            "Día",
            "Dia"
        ],
        "Hora Inicio": [
            "Hora Inicio",
            "Hora Inicial",
            "Hora Inic",
            "Hora Ini"
        ],
        "Hora Final": [
            "Hora Final",
            "Hora Fin",
            "Hora Fini",
            "Hora Finalización"
        ],
        "ID Instalación": [
            "ID Instalación",
            "ID Instalacion",
            "Instalación",
            "Instalacion",
            "Salón",
            "Salon",
            "Aula"
        ],
    }

    columnas_detectadas = {}
    faltantes = []

    for nombre_logico, posibles in columnas_esperadas.items():
        columna = encontrar_columna(df, posibles)

        if columna is None:
            faltantes.append(nombre_logico)
        else:
            columnas_detectadas[nombre_logico] = columna

    return columnas_detectadas, faltantes


def dataframe_a_excel_bytes(df):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")

    return output.getvalue()


def formatear_numero(valor):
    try:
        numero = float(valor)

        if abs(numero - round(numero)) < 0.000001:
            return int(round(numero))

        return round(numero, 2)

    except Exception:
        return valor


# ============================================================
# 1. CARGAR EXCEL
# ============================================================

st.divider()
st.subheader("1. Cargar Excel")

archivo = st.file_uploader(
    "Sube el archivo Excel de programación académica",
    type=["xlsx", "xls"]
)

if archivo is None:
    st.info("Sube el archivo Excel para comenzar.")
    st.stop()

try:
    excel = pd.ExcelFile(archivo)
    hojas = excel.sheet_names
except Exception as e:
    st.error(f"No se pudo leer el archivo Excel. Error: {e}")
    st.stop()

col_hoja, col_fila = st.columns([2, 1])

with col_hoja:
    hoja_seleccionada = st.selectbox(
        "Selecciona la hoja del Excel",
        hojas
    )

with col_fila:
    fila_encabezado = st.number_input(
        "Fila de encabezados",
        min_value=1,
        max_value=50,
        value=1,
        step=1
    )

try:
    archivo.seek(0)

    df = pd.read_excel(
        archivo,
        sheet_name=hoja_seleccionada,
        header=fila_encabezado - 1
    )

    df = df.dropna(axis=1, how="all")

except Exception as e:
    st.error(f"No se pudo cargar la hoja seleccionada. Error: {e}")
    st.stop()

st.success("Excel cargado correctamente.")

st.markdown("### Vista previa del Excel")

m1, m2 = st.columns(2)
m1.metric("Filas detectadas", f"{len(df):,}")
m2.metric("Columnas detectadas", f"{len(df.columns):,}")

st.dataframe(
    df.head(20),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 2. DETECTAR COLUMNAS AUTOMÁTICAMENTE
# ============================================================

columnas_detectadas, columnas_faltantes = validar_columnas_requeridas(df)

if columnas_faltantes:
    st.error(
        "No se encontraron algunas columnas requeridas en el Excel. "
        "Revisa que los encabezados estén en la fila correcta."
    )

    st.write("Columnas faltantes:")
    st.write(columnas_faltantes)

    st.stop()


# Variables de columnas reales del Excel
COL_CICLO = columnas_detectadas["Ciclo Lectivo"]
COL_CURSO = columnas_detectadas["Nombre del curso"]
COL_COMPONENTE = columnas_detectadas["Componente"]
COL_DESCRIPCION = columnas_detectadas["Descripción Materia"]
COL_FECHA_INICIAL = columnas_detectadas["Fecha inicial"]
COL_FECHA_FINAL = columnas_detectadas["Fecha final"]
COL_DOC = columnas_detectadas["Número documento docente"]
COL_ID_PROF = columnas_detectadas["Id profesor"]
COL_NOMBRE_PROF = columnas_detectadas["Nombre profesor"]
COL_NUM_CLASE = columnas_detectadas["Número de Clase"]
COL_ID_SECCION = columnas_detectadas["ID Sección Combinada"]
COL_DIA = columnas_detectadas["Día"]
COL_HORA_INICIO = columnas_detectadas["Hora Inicio"]
COL_HORA_FINAL = columnas_detectadas["Hora Final"]
COL_INSTALACION = columnas_detectadas["ID Instalación"]


# ============================================================
# 3. PREPARAR BASE
# ============================================================

base = df.copy()

# Limpieza de identificadores
base["_doc_limpio"] = base[COL_DOC].apply(limpiar_codigo)
base["_doc_sin_ceros"] = base[COL_DOC].apply(quitar_ceros_izquierda)

base["_id_prof_limpio"] = base[COL_ID_PROF].apply(limpiar_codigo)
base["_id_prof_sin_ceros"] = base[COL_ID_PROF].apply(quitar_ceros_izquierda)

# Limpieza de ciclos
base["_ciclo_parseado"] = base[COL_CICLO].apply(parsear_periodo)
base["_ciclo_limpio"] = base["_ciclo_parseado"].apply(lambda x: x[0])
base["_ciclo_orden"] = base["_ciclo_parseado"].apply(lambda x: x[1])

base = base[base["_ciclo_orden"].notna()].copy()

if base.empty:
    st.error("No se detectaron ciclos lectivos válidos. Revisa la columna 'Ciclo Lectivo'.")
    st.stop()

periodos_disponibles = (
    base[["_ciclo_limpio", "_ciclo_orden"]]
    .drop_duplicates()
    .sort_values("_ciclo_orden")
)

lista_ciclos = periodos_disponibles["_ciclo_limpio"].tolist()

if len(lista_ciclos) == 0:
    st.error("No hay ciclos lectivos disponibles para consultar.")
    st.stop()


# ============================================================
# 4. CONSULTA DOCENTE
# ============================================================

st.divider()
st.subheader("2. Consulta Docente")

tipo_busqueda = st.selectbox(
    "Seleccione tipo de búsqueda",
    ["Número documento docente", "Id profesor"]
)

valor_busqueda = st.text_input(
    f"Ingrese {tipo_busqueda}",
    placeholder="Ejemplo: 80243251"
)

col_ini, col_fin = st.columns(2)

with col_ini:
    ciclo_inicial = st.selectbox(
        "Ciclo lectivo inicial",
        lista_ciclos,
        index=0
    )

with col_fin:
    ciclo_final = st.selectbox(
        "Ciclo lectivo final",
        lista_ciclos,
        index=len(lista_ciclos) - 1
    )

orden_inicial = periodos_disponibles.loc[
    periodos_disponibles["_ciclo_limpio"] == ciclo_inicial,
    "_ciclo_orden"
].iloc[0]

orden_final = periodos_disponibles.loc[
    periodos_disponibles["_ciclo_limpio"] == ciclo_final,
    "_ciclo_orden"
].iloc[0]

if orden_inicial > orden_final:
    st.error("El ciclo lectivo inicial no puede ser mayor que el ciclo lectivo final.")
    st.stop()

buscar = st.button("Buscar información docente", type="primary")


# ============================================================
# 5. PROCESAR BÚSQUEDA
# ============================================================

if buscar:

    valor_limpio = limpiar_codigo(valor_busqueda)
    valor_sin_ceros = quitar_ceros_izquierda(valor_busqueda)

    if valor_limpio == "":
        st.warning("Ingresa un valor para realizar la búsqueda.")
        st.stop()

    if tipo_busqueda == "Número documento docente":
        filtro_id = (
            (base["_doc_limpio"] == valor_limpio) |
            (base["_doc_sin_ceros"] == valor_sin_ceros)
        )
    else:
        filtro_id = (
            (base["_id_prof_limpio"] == valor_limpio) |
            (base["_id_prof_sin_ceros"] == valor_sin_ceros)
        )

    resultado = base[
        filtro_id &
        (base["_ciclo_orden"] >= orden_inicial) &
        (base["_ciclo_orden"] <= orden_final)
    ].copy()

    if resultado.empty:
        st.warning("No se encontraron registros para ese docente en el rango seleccionado.")
        st.stop()

    # ------------------------------------------------------------
    # Limpieza de columnas internas para cálculo
    # ------------------------------------------------------------

    resultado["_nombre_profesor"] = resultado[COL_NOMBRE_PROF].apply(formatear_valor)

    resultado["_curso"] = resultado[COL_CURSO].apply(formatear_valor)
    resultado["_curso_norm"] = resultado[COL_CURSO].apply(normalizar_texto)

    resultado["_componente"] = resultado[COL_COMPONENTE].apply(formatear_valor)
    resultado["_componente_norm"] = resultado[COL_COMPONENTE].apply(normalizar_texto)

    resultado["_descripcion"] = resultado[COL_DESCRIPCION].apply(formatear_valor)
    resultado["_descripcion_norm"] = resultado[COL_DESCRIPCION].apply(normalizar_texto)

    resultado["_num_clase"] = resultado[COL_NUM_CLASE].apply(limpiar_codigo)

    resultado["_id_seccion"] = resultado[COL_ID_SECCION].apply(limpiar_codigo)
    resultado["_tiene_id_seccion"] = resultado["_id_seccion"].apply(lambda x: x != "")

    resultado["_dia_norm"] = resultado[COL_DIA].apply(normalizar_texto)
    resultado["_hora_inicio_min"] = resultado[COL_HORA_INICIO].apply(hora_a_minutos)
    resultado["_hora_final_min"] = resultado[COL_HORA_FINAL].apply(hora_a_minutos)
    resultado["_instalacion_norm"] = resultado[COL_INSTALACION].apply(normalizar_texto)

    resultado["_fecha_inicial_parseada"] = resultado[COL_FECHA_INICIAL].apply(parsear_fecha)
    resultado["_fecha_final_parseada"] = resultado[COL_FECHA_FINAL].apply(parsear_fecha)

    # Se eliminan filas que no tienen datos suficientes para calcular horas
    resultado_horas = resultado[
        resultado["_hora_inicio_min"].notna() &
        resultado["_hora_final_min"].notna() &
        (resultado["_hora_final_min"] > resultado["_hora_inicio_min"]) &
        (resultado["_dia_norm"] != "") &
        (resultado["_curso_norm"] != "") &
        (resultado["_componente_norm"] != "")
    ].copy()

    if resultado_horas.empty:
        st.warning(
            "Se encontraron registros del docente, pero no hay filas con horarios válidos "
            "para calcular sesiones."
        )
        st.stop()

    # ------------------------------------------------------------
    # 5.1. Resolver clases espejo según ID Sección Combinada
    # ------------------------------------------------------------
    # Lógica corregida:
    # - El ID Sección Combinada indica posible espejo, pero no se usa solo.
    # - Un bloque espejo se identifica por:
    #   ID Sección Combinada + Día + Hora Inicio + Hora Final + ID Instalación.
    # - Si varias materias diferentes aparecen repetidas en distintos bloques espejo,
    #   no se acumulan todas en una sola materia.
    # - Se agrupa por el conjunto de materias espejo y se distribuyen los bloques
    #   reales entre esas materias.
    # - Para calcular bloques reales, primero se unen intervalos solapados o continuos.

    con_id_seccion = resultado_horas[resultado_horas["_tiene_id_seccion"]].copy()
    sin_id_seccion = resultado_horas[~resultado_horas["_tiene_id_seccion"]].copy()

    filas_espejo_resueltas = []

    if not con_id_seccion.empty:

        # --------------------------------------------------------
        # 1. Crear una firma del conjunto de materias por cada ID Sección.
        # --------------------------------------------------------
        # Ejemplo:
        # ID 1 tiene Clase A y Clase B
        # ID 2 tiene Clase A y Clase B
        # Entonces ambos quedan con la misma firma:
        # CLASE A || CLASE B
        #
        # Esto evita que la asignación se reinicie por cada ID.
        # --------------------------------------------------------

        firmas_por_id = {}

        for clave_id, grupo_id in con_id_seccion.groupby(
            ["_ciclo_limpio", "_id_seccion"],
            dropna=False
        ):
            materias_del_id = (
                grupo_id[
                    [
                        "_curso_norm",
                        "_componente_norm",
                        "_descripcion_norm",
                    ]
                ]
                .drop_duplicates()
                .astype(str)
            )

            materias_firma = []

            for _, fila_materia in materias_del_id.iterrows():
                materias_firma.append(
                    fila_materia["_curso_norm"]
                    + "||"
                    + fila_materia["_componente_norm"]
                    + "||"
                    + fila_materia["_descripcion_norm"]
                )

            firma_conjunto = " ## ".join(sorted(materias_firma))

            firmas_por_id[clave_id] = firma_conjunto

        con_id_seccion["_firma_conjunto_materias"] = con_id_seccion.apply(
            lambda fila: firmas_por_id.get(
                (fila["_ciclo_limpio"], fila["_id_seccion"]),
                ""
            ),
            axis=1
        )

        # --------------------------------------------------------
        # 2. Procesar por ciclo + conjunto de materias espejo.
        # --------------------------------------------------------
        # Aquí está la corrección importante:
        # Ya NO agrupamos solamente por ID Sección Combinada.
        # Agrupamos por el conjunto de materias.
        # Así ID 1 y ID 2 se procesan juntos si contienen las mismas materias.
        # --------------------------------------------------------

        for _, grupo_espejo in con_id_seccion.groupby(
            ["_ciclo_limpio", "_firma_conjunto_materias"],
            dropna=False
        ):

            grupo_espejo = grupo_espejo.copy()

            materias_distintas = (
                grupo_espejo[
                    [
                        "_curso_norm",
                        "_componente_norm",
                        "_descripcion_norm",
                        "_curso",
                        "_componente",
                        "_descripcion",
                        "_num_clase",
                    ]
                ]
                .drop_duplicates(
                    subset=[
                        "_curso_norm",
                        "_componente_norm",
                        "_descripcion_norm",
                    ]
                )
                .reset_index(drop=True)
            )

            # Caso simple:
            # Si solo hay una materia en el conjunto, solo quitamos duplicados espejo.
            if len(materias_distintas) <= 1:
                grupo_limpio = grupo_espejo.drop_duplicates(
                    subset=[
                        "_ciclo_limpio",
                        "_id_seccion",
                        "_dia_norm",
                        "_hora_inicio_min",
                        "_hora_final_min",
                        "_instalacion_norm",
                    ],
                    keep="first"
                )

                filas_espejo_resueltas.append(grupo_limpio)
                continue

            # --------------------------------------------------------
            # 3. Crear bloques horarios reales.
            # --------------------------------------------------------
            # Un bloque real se arma por:
            # ID Sección + Día + Instalación.
            #
            # Dentro de ese bloque unimos horarios:
            # 10-11 + 11-12 + 12-13 => 10-13
            # 10-12 + 11-13 => 10-13
            # --------------------------------------------------------

            bloques_reales = []

            for (id_seccion, dia, instalacion), grupo_bloque_base in grupo_espejo.groupby(
                ["_id_seccion", "_dia_norm", "_instalacion_norm"],
                dropna=False
            ):

                intervalos = list(
                    zip(
                        grupo_bloque_base["_hora_inicio_min"],
                        grupo_bloque_base["_hora_final_min"]
                    )
                )

                _, intervalos_unidos = unir_intervalos(intervalos)

                for inicio_bloque, fin_bloque in intervalos_unidos:
                    bloques_reales.append({
                        "_id_seccion": id_seccion,
                        "_dia_norm": dia,
                        "_instalacion_norm": instalacion,
                        "_inicio_bloque": inicio_bloque,
                        "_fin_bloque": fin_bloque,
                    })

            bloques_reales = pd.DataFrame(bloques_reales)

            if bloques_reales.empty:
                continue

            bloques_reales = bloques_reales.sort_values(
                [
                    "_dia_norm",
                    "_inicio_bloque",
                    "_fin_bloque",
                    "_instalacion_norm",
                    "_id_seccion",
                ]
            ).reset_index(drop=True)

            # --------------------------------------------------------
            # 4. Distribuir bloques entre materias distintas.
            # --------------------------------------------------------
            # Ejemplo:
            # Bloque lunes 10-13, ID 1 -> Clase A
            # Bloque miércoles 10-13, ID 2 -> Clase B
            #
            # Así no queda:
            # Clase A = 96
            #
            # Sino:
            # Clase A = 48
            # Clase B = 48
            # --------------------------------------------------------

            filas_asignadas = []

            for i, bloque in bloques_reales.iterrows():

                materia_asignada = materias_distintas.iloc[i % len(materias_distintas)]

                filtro_bloque = (
                    (grupo_espejo["_id_seccion"] == bloque["_id_seccion"]) &
                    (grupo_espejo["_dia_norm"] == bloque["_dia_norm"]) &
                    (grupo_espejo["_instalacion_norm"] == bloque["_instalacion_norm"]) &
                    (grupo_espejo["_hora_inicio_min"] < bloque["_fin_bloque"]) &
                    (grupo_espejo["_hora_final_min"] > bloque["_inicio_bloque"])
                )

                grupo_bloque = grupo_espejo[filtro_bloque].copy()

                if grupo_bloque.empty:
                    continue

                # Quitamos duplicados espejo exactos dentro del bloque.
                # Conserva los tramos necesarios para que después 5.2 una los intervalos.
                grupo_bloque_unico = grupo_bloque.drop_duplicates(
                    subset=[
                        "_id_seccion",
                        "_dia_norm",
                        "_hora_inicio_min",
                        "_hora_final_min",
                        "_instalacion_norm",
                    ],
                    keep="first"
                ).copy()

                # Asignamos TODO el bloque real a una sola materia representante.
                grupo_bloque_unico["_curso"] = materia_asignada["_curso"]
                grupo_bloque_unico["_curso_norm"] = materia_asignada["_curso_norm"]

                grupo_bloque_unico["_componente"] = materia_asignada["_componente"]
                grupo_bloque_unico["_componente_norm"] = materia_asignada["_componente_norm"]

                grupo_bloque_unico["_descripcion"] = materia_asignada["_descripcion"]
                grupo_bloque_unico["_descripcion_norm"] = materia_asignada["_descripcion_norm"]

                grupo_bloque_unico["_num_clase"] = materia_asignada["_num_clase"]

                filas_asignadas.append(grupo_bloque_unico)

            if filas_asignadas:
                filas_espejo_resueltas.append(
                    pd.concat(filas_asignadas, ignore_index=True)
                )

    if filas_espejo_resueltas:
        con_id_seccion_resuelto = pd.concat(
            filas_espejo_resueltas,
            ignore_index=True
        )
    else:
        con_id_seccion_resuelto = pd.DataFrame(columns=resultado_horas.columns)

    resultado_sin_espejos = pd.concat(
        [sin_id_seccion, con_id_seccion_resuelto],
        ignore_index=True
    )

    # ------------------------------------------------------------
    # 5.2. Calcular horas semanales por Número de Clase
    # ------------------------------------------------------------
    # Primero se consolida cada Número de Clase.
    # Dentro de cada clase, se unen rangos horarios por día para evitar:
    # - filas consecutivas repetidas
    # - solapamientos
    # - duplicados horarios

    grupos_clase = [
        "_ciclo_limpio",
        "_ciclo_orden",
        "_num_clase",
        "_curso_norm",
        "_componente_norm",
        "_descripcion_norm"
    ]

    clases_calculadas = []

    for clave, grupo_clase in resultado_sin_espejos.groupby(grupos_clase, dropna=False):
        ciclo_limpio = clave[0]
        ciclo_orden = clave[1]
        numero_clase = clave[2]
        curso_norm = clave[3]
        componente_norm = clave[4]
        descripcion_norm = clave[5]

        horas_semanales_clase = 0
        bloques_horarios = []

        # Unir intervalos por día.
        # No agrupamos por salón en la unión porque una misma clase no debería
        # contarse dos veces si aparece con el mismo horario en otra instalación.
        for dia, grupo_dia in grupo_clase.groupby("_dia_norm", dropna=False):
            intervalos = list(
                zip(
                    grupo_dia["_hora_inicio_min"],
                    grupo_dia["_hora_final_min"]
                )
            )

            horas_dia, intervalos_unidos = unir_intervalos(intervalos)
            horas_semanales_clase += horas_dia

            for inicio, fin in intervalos_unidos:
                bloques_horarios.append(
                    f"{dia.title()} {minutos_a_hora(inicio)}-{minutos_a_hora(fin)}"
                )

        clases_calculadas.append({
            "Ciclo Lectivo": ciclo_limpio,
            "_ciclo_orden": ciclo_orden,
            "_num_clase": numero_clase,
            "_curso_norm": curso_norm,
            "_componente_norm": componente_norm,
            "_descripcion_norm": descripcion_norm,
            "Nombre del curso": primero_no_vacio(grupo_clase["_curso"]),
            "Componente": primero_no_vacio(grupo_clase["_componente"]),
            "Descripción": primero_no_vacio(grupo_clase["_descripcion"]),
            "Horas semanales clase": horas_semanales_clase,
            "Fecha": combinar_fechas(grupo_clase, COL_FECHA_INICIAL, COL_FECHA_FINAL),
            "_nombre_profesor": primero_no_vacio(grupo_clase["_nombre_profesor"]),
            "_horario_debug": " | ".join(sorted(set(bloques_horarios))),
        })

    clases_df = pd.DataFrame(clases_calculadas)

    if clases_df.empty:
        st.warning("No fue posible consolidar clases para este docente.")
        st.stop()

    # ------------------------------------------------------------
    # 5.3. Agrupar por materia / componente / ciclo
    # ------------------------------------------------------------
    # La tabla final debe mostrar una sola fila por materia/componente/ciclo.
    # Si un profesor dicta varios grupos válidos de la misma materia,
    # se suman sus horas semanales y luego se multiplica por 16.

    grupos_finales = [
        "Ciclo Lectivo",
        "_ciclo_orden",
        "_curso_norm",
        "_componente_norm",
        "_descripcion_norm"
    ]

    tabla_final = (
        clases_df
        .groupby(grupos_finales, dropna=False)
        .agg(
            **{
                "Nombre del curso": ("Nombre del curso", "first"),
                "Componente": ("Componente", "first"),
                "Descripción": ("Descripción", "first"),
                "Horas semanales": ("Horas semanales clase", "sum"),
                "Fecha": ("Fecha", "first"),
                "_nombre_profesor": ("_nombre_profesor", "first"),
                "_clases_agrupadas": ("_num_clase", lambda x: ", ".join(sorted(set(x.astype(str))))),
                "_horarios": ("_horario_debug", lambda x: " | ".join(sorted(set(x.astype(str)))))
            }
        )
        .reset_index()
    )

    tabla_final["Sesiones"] = tabla_final["Horas semanales"] * SEMANAS_CICLO
    tabla_final["Sesiones"] = tabla_final["Sesiones"].apply(formatear_numero)

    tabla_final = tabla_final.sort_values(
        by=["_ciclo_orden", "Nombre del curso", "Componente"],
        ascending=[True, True, True]
    )

    nombre_profesor = primero_no_vacio(tabla_final["_nombre_profesor"])

    if nombre_profesor == "":
        nombre_profesor = primero_no_vacio(resultado[COL_NOMBRE_PROF])

    # ------------------------------------------------------------
    # 5.4. Mostrar resultados
    # ------------------------------------------------------------

    st.divider()

    st.markdown(f"## **{nombre_profesor}**")
    st.markdown(f"**{tipo_busqueda}:** {valor_busqueda}")
    st.markdown(f"**Rango de Ciclo Lectivo:** {ciclo_inicial} - {ciclo_final}")

    tabla_mostrar = tabla_final[
        [
            "Ciclo Lectivo",
            "Nombre del curso",
            "Componente",
            "Sesiones",
            "Descripción",
            "Fecha"
        ]
    ].copy()

    st.subheader("Tabla de resultados")

    st.dataframe(
        tabla_mostrar,
        use_container_width=True,
        hide_index=True
    )

    # Resumen útil para validar, no afecta la tabla final
    with st.expander("Resumen de procesamiento"):
        st.write("Registros encontrados antes de depurar:", len(resultado))
        st.write("Registros válidos para cálculo de horas:", len(resultado_horas))
        st.write("Registros después de eliminar posibles espejos:", len(resultado_sin_espejos))
        st.write("Números de clase consolidados:", clases_df["_num_clase"].nunique())
        st.write("Materias/componentes finales:", len(tabla_mostrar))

        st.dataframe(
            clases_df[
                [
                    "Ciclo Lectivo",
                    "_num_clase",
                    "Nombre del curso",
                    "Componente",
                    "Horas semanales clase",
                    "_horario_debug"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    excel_bytes = dataframe_a_excel_bytes(tabla_mostrar)

    st.download_button(
        label="Descargar resultado en Excel",
        data=excel_bytes,
        file_name=f"resultado_docente_{valor_limpio}_{ciclo_inicial}_a_{ciclo_final}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )