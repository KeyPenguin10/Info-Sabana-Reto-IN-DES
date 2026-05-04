import io
import re
import json
import html
import base64
import unicodedata
from pathlib import Path
from datetime import datetime, time
from uuid import uuid4

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

RUTA_BASE = Path(__file__).resolve().parent
RUTA_LOGO_SABANA = RUTA_BASE / "assets" / "logo_sabana.png"

st.set_page_config(
    page_title="InfoSabana - Información Docente",
    page_icon=str(RUTA_LOGO_SABANA),
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        :root {
            --azul-sabana: #002B7A;
            --azul-sabana-hover: #001C64;
            --azul-claro: #EAF1FF;
            --azul-borde: #D8E5FF;
            --fondo-app: #F8FAFC;
            --texto-principal: #1F2937;
            --texto-secundario: #64748B;
            --borde-suave: #E5E7EB;
            --exito: #10B981;
            --sombra-suave: 0 10px 28px rgba(15, 23, 42, 0.08);
            --radio-card: 18px;
            --ancho-app: 1100px;
        }

        /* ============================================================
           ESTABILIDAD GENERAL
           Mantiene la página siempre con el mismo ancho visual.
           ============================================================ */

        html {
            overflow-y: scroll !important;
            overflow-x: hidden !important;
            scrollbar-gutter: stable both-edges !important;
            width: 100% !important;
        }

        body {
            overflow-x: hidden !important;
            width: 100% !important;
            margin: 0 !important;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', 'Source Sans Pro', Arial, sans-serif !important;
        }

        .stApp {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
            background: radial-gradient(circle at top left, #EEF4FF 0, #F8FAFC 340px, #F8FAFC 100%) !important;
            color: var(--texto-principal) !important;
        }

        [data-testid="stAppViewContainer"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
        }

        [data-testid="stMain"] {
            width: 100% !important;
            max-width: 100% !important;
            overflow-x: hidden !important;
        }

        /* Contenedor principal: queda siempre en el ancho amplio */
        .block-container,
        [data-testid="stMainBlockContainer"] {
            width: var(--ancho-app) !important;
            max-width: var(--ancho-app) !important;
            min-width: var(--ancho-app) !important;
            margin-left: auto !important;
            margin-right: auto !important;
            padding-top: 1.2rem !important;
            padding-bottom: 3rem !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            box-sizing: border-box !important;
        }

        /* En pantallas menores, mantiene margen fijo sin deformarse */
        @media (max-width: 1240px) {
            .block-container,
            [data-testid="stMainBlockContainer"] {
                width: calc(100vw - 48px) !important;
                max-width: calc(100vw - 48px) !important;
                min-width: calc(100vw - 48px) !important;
                margin-left: 24px !important;
                margin-right: 24px !important;
                padding-left: 0 !important;
                padding-right: 0 !important;
                box-sizing: border-box !important;
            }
        }

        /* Evita microcambios de ancho en formularios, inputs y columnas */
        div[data-testid="stForm"],
        div[data-testid="stForm"] > div,
        div[data-testid="stVerticalBlock"],
        div[data-testid="stHorizontalBlock"],
        div[data-testid="column"],
        div[data-baseweb="select"],
        div[data-baseweb="input"],
        div[data-baseweb="textarea"],
        div[data-testid="stSelectbox"],
        div[data-testid="stTextInput"],
        div[data-testid="stNumberInput"] {
            max-width: 100% !important;
            box-sizing: border-box !important;
        }

        /* Quita animaciones que hacen parecer que la página se estira */
        * {
            transition-property: color, background-color, border-color, box-shadow !important;
        }

        /* ============================================================
           TÍTULOS Y HEADER
           ============================================================ */

        .infosabana-title {
            color: var(--azul-sabana) !important;
            -webkit-text-fill-color: var(--azul-sabana) !important;
            font-family: 'Inter', Arial, sans-serif !important;
            font-style: normal !important;
            font-weight: 800 !important;
            font-size: clamp(34px, 4vw, 50px) !important;
            line-height: 1.08 !important;
            letter-spacing: -0.04em !important;
            margin: 0 !important;
        }

        .infosabana-subtitle {
            color: var(--azul-sabana) !important;
            -webkit-text-fill-color: var(--azul-sabana) !important;
            font-family: 'Inter', Arial, sans-serif !important;
            font-style: normal !important;
            font-weight: 750 !important;
            letter-spacing: -0.02em !important;
        }

        .infosabana-hero {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 24px;
            margin: 14px auto 28px auto;
            padding: 26px 28px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid var(--azul-borde);
            border-radius: 24px;
            box-shadow: var(--sombra-suave);
            box-sizing: border-box;
            width: 100%;
        }

        .infosabana-logo {
            width: 82px;
            height: auto;
            object-fit: contain;
            flex-shrink: 0;
            filter: drop-shadow(0 6px 12px rgba(0, 43, 122, 0.12));
        }

        .infosabana-hero-text {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .infosabana-tagline {
            margin: 0;
            color: var(--texto-secundario);
            font-size: 15px;
            font-weight: 500;
            max-width: 620px;
        }

        /* ============================================================
           CARDS Y SECCIONES
           ============================================================ */

        .info-card {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid var(--borde-suave);
            border-radius: var(--radio-card);
            box-shadow: var(--sombra-suave);
            padding: 22px 24px;
            margin: 18px 0;
            box-sizing: border-box;
            width: 100%;
        }

        .info-card-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 0 8px 0;
            color: var(--azul-sabana);
            font-size: 22px;
            font-weight: 800;
            letter-spacing: -0.03em;
        }

        .info-card-text {
            margin: 0;
            color: var(--texto-secundario);
            font-size: 15px;
            line-height: 1.55;
        }

        .section-label {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 7px 12px;
            border-radius: 999px;
            background: var(--azul-claro);
            color: var(--azul-sabana);
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 10px;
        }

        /* ============================================================
           UPLOADER
           ============================================================ */

        div[data-testid="stFileUploader"] {
            background: #FFFFFF;
            border: 1.5px dashed #B7C7E8;
            border-radius: 16px;
            padding: 12px 14px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.04);
            box-sizing: border-box;
            width: 100%;
        }

        div[data-testid="stFileUploader"] label {
            color: var(--azul-sabana) !important;
            font-weight: 750 !important;
        }

        div[data-testid="stFileUploader"] section {
            border-radius: 14px !important;
        }

        div[data-testid="stFileUploader"] button {
            background-color: var(--azul-sabana) !important;
            color: white !important;
            border-radius: 10px !important;
            border: 1px solid var(--azul-sabana) !important;
            font-weight: 700 !important;
        }

        /* ============================================================
           BOTONES
           ============================================================ */

        div.stButton > button[kind="primary"] {
            background-color: var(--azul-sabana) !important;
            border-color: var(--azul-sabana) !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 0.65rem !important;
            min-height: 48px !important;
        }

        div.stButton > button[kind="primary"]:hover {
            background-color: var(--azul-sabana-hover) !important;
            border-color: var(--azul-sabana-hover) !important;
            color: white !important;
        }

        div.stDownloadButton {
            margin: 0 !important;
            padding: 0 !important;
        }

        div.stDownloadButton > button {
            background-color: var(--azul-sabana) !important;
            border-color: var(--azul-sabana) !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 0.65rem !important;
            height: 48px !important;
            min-height: 48px !important;
            padding: 0 18px !important;
            line-height: 1 !important;
            box-shadow: none !important;
            width: 100% !important;
        }

        div.stDownloadButton > button:hover {
            background-color: var(--azul-sabana-hover) !important;
            border-color: var(--azul-sabana-hover) !important;
            color: white !important;
        }

        div.stDownloadButton > button p {
            color: white !important;
            font-weight: 600 !important;
            font-size: 15px !important;
            line-height: 1.1 !important;
        }

        /* ============================================================
           MÉTRICAS, TABLAS Y ALERTAS
           ============================================================ */

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid var(--borde-suave);
            border-radius: 14px;
            padding: 14px 16px;
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--borde-suave);
            border-radius: 14px;
            overflow: visible !important;
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
        }

        .stAlert {
            border-radius: 14px !important;
        }

        hr {
            margin: 1.6rem 0 !important;
        }

        /* ============================================================
           RESPONSIVE
           ============================================================ */

        @media (max-width: 720px) {
            .infosabana-hero {
                flex-direction: column;
                text-align: center;
                padding: 22px 18px;
            }

            .infosabana-logo {
                width: 70px;
            }
        }
    </style>
    """,
    unsafe_allow_html=True
)


SEMANAS_CICLO = 16

COLUMNAS_RESULTADO_DISPONIBLES = [
    "Ciclo Lectivo",
    "Nombre del curso",
    "Componente",
    "Sesiones",
    "Descripción",
    "Fecha"
]

# Llaves nuevas para que Streamlit no reutilice estados viejos.
COLUMNAS_CHECK_PREFIX = "check_columnas_resultado_visual_v5_"
COLUMNAS_CONFIRMADAS_KEY = "columnas_resultado_confirmadas_visual_v5"

# Si el usuario nunca toca Configurar columnas, se muestran todas.
if COLUMNAS_CONFIRMADAS_KEY not in st.session_state:
    st.session_state[COLUMNAS_CONFIRMADAS_KEY] = COLUMNAS_RESULTADO_DISPONIBLES.copy()

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
        "Total Inscritos": [
            "Total Inscritos",
            "Total inscritos",
            "TOTAL INSCRITOS",
            "Total de Inscritos",
            "Total estudiantes inscritos"
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
    
def formatear_ciclo_para_correo(valor):
    texto = str(valor).strip()

    if texto.upper().startswith("PERIODO"):
        return texto.upper()

    return f"PERIODO {texto}".upper()

# ============================================================
# FUNCIONES PARA BÚSQUEDA POR NOMBRE DE PROFESOR
# ============================================================

def valor_es_solo_numeros(valor):
    """
    Valida que un documento o ID docente tenga únicamente números.
    Permite ceros a la izquierda.
    """
    texto = limpiar_codigo(valor)
    return bool(re.fullmatch(r"\d+", texto))


def validar_nombre_profesor_busqueda(valor):
    """
    Valida que la búsqueda por nombre tenga solo letras y espacios.
    También exige mínimo dos palabras para evitar búsquedas demasiado amplias.
    """
    texto_original = str(valor).strip()

    if texto_original == "":
        return {
            "ok": False,
            "mensaje": (
                "Ingresa el nombre del profesor para realizar la búsqueda. "
                "Escribe nombres y apellidos para evitar coincidencias ambiguas."
            ),
            "tokens": [],
            "nombre_norm": ""
        }

    if not re.fullmatch(r"[A-Za-zÁÉÍÓÚÜáéíóúüÑñ ]+", texto_original):
        return {
            "ok": False,
            "mensaje": (
                "Para buscar por nombre, usa únicamente letras y espacios. "
                "No incluyas números, códigos, puntos, comas ni caracteres especiales."
            ),
            "tokens": [],
            "nombre_norm": ""
        }

    nombre_norm = normalizar_texto(texto_original)
    tokens = nombre_norm.split()

    if len(tokens) < 2:
        return {
            "ok": False,
            "mensaje": (
                "La búsqueda por nombre es demasiado amplia. "
                "Escribe al menos un nombre y un apellido del profesor. "
                "Ejemplo: PEREZ ADRIAN o PEREZ HERNANDEZ ADRIAN FELIPE."
            ),
            "tokens": tokens,
            "nombre_norm": nombre_norm
        }

    return {
        "ok": True,
        "mensaje": "",
        "tokens": tokens,
        "nombre_norm": nombre_norm
    }


def preparar_docentes_unicos_para_nombre(base, col_nombre_prof, col_doc, col_id_prof):
    """
    Crea una base única de docentes para búsqueda por nombre.
    Separa nombres, documentos e ID profesor sin duplicar por cada clase.
    """
    docentes = base[
        [col_nombre_prof, col_doc, col_id_prof]
    ].copy()

    docentes["_nombre_mostrar"] = docentes[col_nombre_prof].apply(formatear_valor)
    docentes["_nombre_norm"] = docentes[col_nombre_prof].apply(normalizar_texto)

    docentes["_doc_limpio_tmp"] = docentes[col_doc].apply(limpiar_codigo)
    docentes["_id_prof_limpio_tmp"] = docentes[col_id_prof].apply(limpiar_codigo)

    docentes = docentes[
        docentes["_nombre_norm"] != ""
    ].copy()

    docentes = docentes.drop_duplicates(
        subset=[
            "_nombre_norm",
            "_doc_limpio_tmp",
            "_id_prof_limpio_tmp"
        ]
    )

    return docentes


def reducir_candidatos_por_identidad(candidatos):
    """
    Evita contar varias veces al mismo docente si aparece repetido por clases.
    Prioriza documento; si no existe documento, usa ID profesor.
    """
    if candidatos.empty:
        return candidatos

    candidatos = candidatos.copy()

    candidatos_con_doc = candidatos[
        candidatos["_doc_limpio_tmp"] != ""
    ].copy()

    if not candidatos_con_doc.empty:
        return candidatos_con_doc.drop_duplicates(
            subset=["_doc_limpio_tmp"]
        )

    candidatos_con_id = candidatos[
        candidatos["_id_prof_limpio_tmp"] != ""
    ].copy()

    if not candidatos_con_id.empty:
        return candidatos_con_id.drop_duplicates(
            subset=["_id_prof_limpio_tmp"]
        )

    return candidatos.drop_duplicates(
        subset=["_nombre_norm"]
    )


def mostrar_candidatos_nombre_profesor(candidatos):
    """
    Muestra coincidencias de docentes cuando la búsqueda por nombre es ambigua.
    """
    if candidatos is None or candidatos.empty:
        return

    tabla_candidatos = candidatos[
        [
            "_nombre_mostrar",
            "_doc_limpio_tmp",
            "_id_prof_limpio_tmp"
        ]
    ].copy()

    tabla_candidatos = tabla_candidatos.rename(
        columns={
            "_nombre_mostrar": "Nombre profesor",
            "_doc_limpio_tmp": "Documento docente",
            "_id_prof_limpio_tmp": "ID docente"
        }
    )

    st.dataframe(
        tabla_candidatos,
        use_container_width=True,
        hide_index=True
    )


def resolver_busqueda_por_nombre_profesor(
    base,
    nombre_ingresado,
    col_nombre_prof,
    col_doc,
    col_id_prof,
    max_candidatos=8
):
    """
    Resuelve una búsqueda por nombre de profesor de forma controlada.

    Reglas:
    - Solo letras y espacios.
    - Mínimo dos palabras.
    - Ignora tildes, mayúsculas y espacios extra.
    - El orden no importa.
    - Si hay una única coincidencia, devuelve documento o ID para buscar.
    - Si hay varias coincidencias, pide más datos.
    """
    validacion = validar_nombre_profesor_busqueda(nombre_ingresado)

    if not validacion["ok"]:
        return {
            "ok": False,
            "estado": "entrada_invalida",
            "mensaje": validacion["mensaje"],
            "candidatos": pd.DataFrame()
        }

    tokens = validacion["tokens"]
    nombre_norm = validacion["nombre_norm"]

    docentes = preparar_docentes_unicos_para_nombre(
        base=base,
        col_nombre_prof=col_nombre_prof,
        col_doc=col_doc,
        col_id_prof=col_id_prof
    )

    if docentes.empty:
        return {
            "ok": False,
            "estado": "sin_docentes",
            "mensaje": (
                "No fue posible consultar por nombre porque no se encontraron "
                "nombres de profesores válidos en la base cargada."
            ),
            "candidatos": pd.DataFrame()
        }

    # 1. Primero: coincidencia exacta del nombre completo normalizado.
    exactos = docentes[
        docentes["_nombre_norm"] == nombre_norm
    ].copy()

    exactos = reducir_candidatos_por_identidad(exactos)

    if len(exactos) == 1:
        candidato = exactos.iloc[0]

        documento = candidato["_doc_limpio_tmp"]
        id_profesor = candidato["_id_prof_limpio_tmp"]

        if documento != "":
            return {
                "ok": True,
                "estado": "unico",
                "tipo_identificador": "documento",
                "valor_identificador": documento,
                "nombre_mostrar": candidato["_nombre_mostrar"],
                "mensaje": ""
            }

        if id_profesor != "":
            return {
                "ok": True,
                "estado": "unico",
                "tipo_identificador": "id",
                "valor_identificador": id_profesor,
                "nombre_mostrar": candidato["_nombre_mostrar"],
                "mensaje": ""
            }

        return {
            "ok": False,
            "estado": "sin_identificador",
            "mensaje": (
                "Se encontró el docente, pero no tiene documento ni ID docente válido "
                "para realizar la consulta."
            ),
            "candidatos": exactos
        }

    if len(exactos) > 1:
        return {
            "ok": False,
            "estado": "duplicado_exacto",
            "mensaje": (
                "Se encontraron varios docentes con exactamente el mismo nombre. "
                "Para evitar certificar a la persona equivocada, realiza la búsqueda "
                "por documento docente o ID docente."
            ),
            "candidatos": exactos.head(max_candidatos)
        }

    # 2. Segunda opción: coincidencia por palabras completas, sin importar el orden.
    def coincide_por_palabras(nombre_norm_docente):
        palabras_docente = set(nombre_norm_docente.split())
        return all(token in palabras_docente for token in tokens)

    candidatos = docentes[
        docentes["_nombre_norm"].apply(coincide_por_palabras)
    ].copy()

    candidatos = reducir_candidatos_por_identidad(candidatos)

    # 3. Si no hubo coincidencia por palabra exacta, probamos coincidencia parcial controlada.
    # Esto ayuda si escriben una palabra incompleta, pero solo se usa como fallback.
    if candidatos.empty:
        def coincide_parcial(nombre_norm_docente):
            palabras_docente = nombre_norm_docente.split()

            for token in tokens:
                encontrado = any(
                    palabra.startswith(token) or token.startswith(palabra)
                    for palabra in palabras_docente
                    if len(token) >= 3 and len(palabra) >= 3
                )

                if not encontrado:
                    return False

            return True

        candidatos = docentes[
            docentes["_nombre_norm"].apply(coincide_parcial)
        ].copy()

        candidatos = reducir_candidatos_por_identidad(candidatos)

    if candidatos.empty:
        return {
            "ok": False,
            "estado": "no_encontrado",
            "mensaje": (
                "No se encontró ningún docente con el nombre ingresado. "
                "Verifica la escritura o intenta buscar por documento docente o ID docente."
            ),
            "candidatos": pd.DataFrame()
        }

    if len(candidatos) > max_candidatos:
        return {
            "ok": False,
            "estado": "demasiados",
            "mensaje": (
                "La búsqueda por nombre es demasiado amplia y genera muchas coincidencias. "
                "Escribe el nombre completo con nombres y apellidos, o realiza la búsqueda "
                "por documento docente o ID docente."
            ),
            "candidatos": candidatos.head(max_candidatos)
        }

    if len(candidatos) > 1:
        return {
            "ok": False,
            "estado": "ambiguo",
            "mensaje": (
                "Se encontraron varios docentes que coinciden con el nombre ingresado. "
                "Escribe el nombre completo con nombres y apellidos, o realiza la búsqueda "
                "por documento docente o ID docente para evitar errores."
            ),
            "candidatos": candidatos.head(max_candidatos)
        }

    candidato = candidatos.iloc[0]

    documento = candidato["_doc_limpio_tmp"]
    id_profesor = candidato["_id_prof_limpio_tmp"]

    if documento != "":
        return {
            "ok": True,
            "estado": "unico",
            "tipo_identificador": "documento",
            "valor_identificador": documento,
            "nombre_mostrar": candidato["_nombre_mostrar"],
            "mensaje": ""
        }

    if id_profesor != "":
        return {
            "ok": True,
            "estado": "unico",
            "tipo_identificador": "id",
            "valor_identificador": id_profesor,
            "nombre_mostrar": candidato["_nombre_mostrar"],
            "mensaje": ""
        }

    return {
        "ok": False,
        "estado": "sin_identificador",
        "mensaje": (
            "Se encontró el docente, pero no tiene documento ni ID docente válido "
            "para realizar la consulta."
        ),
        "candidatos": candidatos
    }


def dataframe_a_tabla_html_correo(df):
    """
    Convierte la tabla seleccionada en una tabla HTML editable al pegar en Outlook.
    Respeta las columnas que el usuario haya seleccionado.
    """
    columnas = list(df.columns)

    estilo_tabla = (
        "border-collapse:collapse;"
        "font-family:Calibri, Arial, sans-serif;"
        "font-size:14px;"
        "color:#1f1f1f;"
    )

    estilo_th = (
        "border:2px solid #2f6b3f;"
        "background-color:#d9d2c9;"
        "padding:6px 10px;"
        "text-align:center;"
        "font-weight:bold;"
        "vertical-align:middle;"
        "white-space:nowrap;"
    )

    estilo_td = (
        "border:2px solid #2f6b3f;"
        "padding:6px 10px;"
        "text-align:center;"
        "vertical-align:middle;"
    )

    html_tabla = f'<table style="{estilo_tabla}">'

    # Encabezados
    html_tabla += "<thead><tr>"
    for col in columnas:
        html_tabla += f'<th style="{estilo_th}">{html.escape(str(col).upper())}</th>'
    html_tabla += "</tr></thead>"

    html_tabla += "<tbody>"

    # Si la tabla tiene Ciclo Lectivo, hacemos un efecto similar a la imagen:
    # el periodo aparece agrupado con rowspan.
    if "Ciclo Lectivo" in columnas:
        otras_columnas = [c for c in columnas if c != "Ciclo Lectivo"]

        for ciclo, grupo in df.groupby("Ciclo Lectivo", sort=False):
            grupo = grupo.reset_index(drop=True)
            rowspan = len(grupo)

            for i, fila in grupo.iterrows():
                html_tabla += "<tr>"

                if i == 0:
                    ciclo_texto = formatear_ciclo_para_correo(ciclo)
                    html_tabla += (
                        f'<td rowspan="{rowspan}" style="{estilo_td} font-weight:bold;">'
                        f'{html.escape(ciclo_texto)}'
                        f"</td>"
                    )

                for col in otras_columnas:
                    valor = "" if pd.isna(fila[col]) else str(fila[col])
                    html_tabla += f'<td style="{estilo_td}">{html.escape(valor)}</td>'

                html_tabla += "</tr>"

    else:
        for _, fila in df.iterrows():
            html_tabla += "<tr>"

            for col in columnas:
                valor = "" if pd.isna(fila[col]) else str(fila[col])
                html_tabla += f'<td style="{estilo_td}">{html.escape(valor)}</td>'

            html_tabla += "</tr>"

    html_tabla += "</tbody></table>"

    return html_tabla


def generar_correo_html(nombre_profesor, tabla_mostrar):
    """
    Genera el cuerpo del correo en HTML para pegarlo en Outlook.
    """
    nombre_profesor_limpio = html.escape(str(nombre_profesor).strip().upper())

    tabla_html = dataframe_a_tabla_html_correo(tabla_mostrar)

    correo_html = f"""
    <div style="font-family:Calibri, Arial, sans-serif; font-size:14px; color:#1f1f1f;">
        <p><em>Buen Día</em></p>

        <p><em>Cordial Saludo</em></p>

        <p>
            <em>
                Apreciad@s, envío la información encontrada del profesor
                <strong>{nombre_profesor_limpio}</strong>.
            </em>
        </p>

        {tabla_html}

        <p><em>Gracias por su amable atención.</em></p>
    </div>
    """

    return correo_html


def boton_copiar_correo(correo_html):
    """
    Botón HTML/JS que copia el correo como contenido enriquecido.
    Al pegar en Outlook, debe conservar texto + tabla editable.
    """
    correo_json = json.dumps(correo_html)

    componente = f"""
    <html>
        <head>
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    background: transparent !important;
                    overflow: hidden;
                    font-family: Inter, 'Source Sans Pro', Calibri, Arial, sans-serif;
                }}

                .copy-wrapper {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    background: transparent !important;
                }}

                #btnCopiarCorreo {{
                    background-color: #002B7A;
                    color: white;
                    border: 1px solid #002B7A;
                    border-radius: 0.65rem;
                    padding: 0 18px;
                    font-family: Inter, 'Source Sans Pro', Calibri, Arial, sans-serif;
                    font-size: 15px;
                    font-weight: 600;
                    line-height: 1;
                    cursor: pointer;
                    width: 100%;
                    height: 48px;
                    min-height: 48px;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0;
                    box-shadow: none;
                }}

                #btnCopiarCorreo:hover {{
                    background-color: #001C64;
                    border-color: #001C64;
                }}

                #mensajeCopiado {{
                    margin-top: 5px;
                    font-size: 12px;
                    color: #16a34a;
                    font-weight: 600;
                    line-height: 1.2;
                    background: transparent !important;
                }}
            </style>
        </head>

        <body>
            <div class="copy-wrapper">
                <button id="btnCopiarCorreo">
                    Copiar correo
                </button>

                <div id="mensajeCopiado"></div>
            </div>

            <script>
                const correoHTML = {correo_json};

                function htmlATextoPlano(html) {{
                    const temp = document.createElement("div");
                    temp.innerHTML = html;
                    return temp.innerText;
                }}

                function copiarFallback() {{
                    const contenedor = document.createElement("div");
                    contenedor.innerHTML = correoHTML;
                    contenedor.style.position = "fixed";
                    contenedor.style.left = "-9999px";
                    contenedor.style.top = "0";
                    document.body.appendChild(contenedor);

                    const rango = document.createRange();
                    rango.selectNodeContents(contenedor);

                    const seleccion = window.getSelection();
                    seleccion.removeAllRanges();
                    seleccion.addRange(rango);

                    document.execCommand("copy");

                    seleccion.removeAllRanges();
                    document.body.removeChild(contenedor);
                }}

                async function copiarCorreo() {{
                    const mensaje = document.getElementById("mensajeCopiado");

                    try {{
                        if (navigator.clipboard && window.ClipboardItem) {{
                            const blobHTML = new Blob([correoHTML], {{ type: "text/html" }});
                            const blobTexto = new Blob([htmlATextoPlano(correoHTML)], {{ type: "text/plain" }});

                            await navigator.clipboard.write([
                                new ClipboardItem({{
                                    "text/html": blobHTML,
                                    "text/plain": blobTexto
                                }})
                            ]);
                        }} else {{
                            copiarFallback();
                        }}

                        mensaje.innerText = "Correo copiado. Ahora pégalo en Outlook con Ctrl + V.";
                    }} catch (error) {{
                        try {{
                            copiarFallback();
                            mensaje.innerText = "Correo copiado. Ahora pégalo en Outlook con Ctrl + V.";
                        }} catch (fallbackError) {{
                            mensaje.style.color = "#dc2626";
                            mensaje.innerText = "No se pudo copiar automáticamente. Intenta de nuevo.";
                        }}
                    }}
                }}

                document.getElementById("btnCopiarCorreo").addEventListener("click", copiarCorreo);
            </script>
        </body>
    </html>
    """

    components.html(componente, height=105, scrolling=False)

# ============================================================
# FUNCIONES CACHEADAS PARA MEJORAR RENDIMIENTO
# ============================================================

@st.cache_data(show_spinner="Leyendo archivo Excel...")
def obtener_hojas_excel_cache(archivo_bytes):
    archivo_en_memoria = io.BytesIO(archivo_bytes)
    excel = pd.ExcelFile(archivo_en_memoria)
    return excel.sheet_names


@st.cache_data(show_spinner="Cargando hoja del Excel...")
def cargar_hoja_excel_cache(archivo_bytes, hoja_seleccionada, fila_encabezado):
    archivo_en_memoria = io.BytesIO(archivo_bytes)

    df = pd.read_excel(
        archivo_en_memoria,
        sheet_name=hoja_seleccionada,
        header=fila_encabezado - 1
    )

    df = df.dropna(axis=1, how="all")

    return df


@st.cache_data(show_spinner="Preparando base de datos...")
def preparar_base_cache(df):
    columnas_detectadas, columnas_faltantes = validar_columnas_requeridas(df)

    if columnas_faltantes:
        return columnas_detectadas, columnas_faltantes, None, None, None

    col_ciclo = columnas_detectadas["Ciclo Lectivo"]
    col_doc = columnas_detectadas["Número documento docente"]
    col_id_prof = columnas_detectadas["Id profesor"]
    col_nombre_prof = columnas_detectadas["Nombre profesor"]
    col_total_inscritos = columnas_detectadas["Total Inscritos"]

    base_cache = df.copy()

    # Filtrar registros con estudiantes inscritos.
    # Solo se cuentan clases con Total Inscritos >= 1.
    base_cache["_total_inscritos_num"] = pd.to_numeric(
        base_cache[col_total_inscritos],
        errors="coerce"
    ).fillna(0)

    base_cache = base_cache[
        base_cache["_total_inscritos_num"] >= 1
    ].copy()


    base_cache["_doc_limpio"] = base_cache[col_doc].apply(limpiar_codigo)
    base_cache["_doc_sin_ceros"] = base_cache[col_doc].apply(quitar_ceros_izquierda)

    base_cache["_id_prof_limpio"] = base_cache[col_id_prof].apply(limpiar_codigo)
    base_cache["_id_prof_sin_ceros"] = base_cache[col_id_prof].apply(quitar_ceros_izquierda)

    base_cache["_nombre_prof_norm"] = base_cache[col_nombre_prof].apply(normalizar_texto)

    base_cache["_ciclo_parseado"] = base_cache[col_ciclo].apply(parsear_periodo)
    base_cache["_ciclo_limpio"] = base_cache["_ciclo_parseado"].apply(lambda x: x[0])
    base_cache["_ciclo_orden"] = base_cache["_ciclo_parseado"].apply(lambda x: x[1])

    base_cache = base_cache[base_cache["_ciclo_orden"].notna()].copy()

    if base_cache.empty:
        return columnas_detectadas, columnas_faltantes, base_cache, None, []

    periodos_disponibles_cache = (
        base_cache[["_ciclo_limpio", "_ciclo_orden"]]
        .drop_duplicates()
        .sort_values("_ciclo_orden")
    )

    lista_ciclos_cache = periodos_disponibles_cache["_ciclo_limpio"].tolist()

    return (
        columnas_detectadas,
        columnas_faltantes,
        base_cache,
        periodos_disponibles_cache,
        lista_ciclos_cache
    )



def imagen_a_base64(ruta_imagen):
    with open(ruta_imagen, "rb") as archivo_imagen:
        return base64.b64encode(archivo_imagen.read()).decode()


logo_base64 = imagen_a_base64(RUTA_BASE / "assets" / "logo_sabana.png")

st.markdown(
    f"""
    <div class="infosabana-hero">
        <img class="infosabana-logo" src="data:image/png;base64,{logo_base64}">
        <div class="infosabana-hero-text">
            <div class="infosabana-title">
                InfoSabana - Consultor de<br>
                Información Docente
            </div>
            <p class="infosabana-tagline">
                Sistema de consulta y consolidación de programación académica para certificados docentes.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ============================================================
# 1. CARGAR EXCEL
# ============================================================

st.markdown(
    """
    <div class="info-card">
        <div class="section-label">1.</div>
        <h2 class="info-card-title">Carga tu archivo de programación académica</h2>
        <p class="info-card-text">
            Arrastra o selecciona tu archivo Excel (.xlsx o .xls). Procesaremos el archivo automáticamente y
            guardaremos esta carga para este usuario usando la URL actual.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

CARPETA_ARCHIVOS_USUARIOS = RUTA_BASE / "archivos_usuarios"
CARPETA_ARCHIVOS_USUARIOS.mkdir(exist_ok=True)

PARAM_USUARIO = "usuario"

# ------------------------------------------------------------
# Crear o recuperar un ID único para este usuario/navegador.
# Este ID queda en la URL como ?usuario=...
# Así, si la persona refresca la página, se conserva el archivo.
# ------------------------------------------------------------

id_usuario = st.query_params.get(PARAM_USUARIO, "")

if isinstance(id_usuario, list):
    id_usuario = id_usuario[0]

if not re.fullmatch(r"[a-f0-9]{32}", str(id_usuario)):
    id_usuario = uuid4().hex
    st.query_params[PARAM_USUARIO] = id_usuario

CARPETA_USUARIO = CARPETA_ARCHIVOS_USUARIOS / id_usuario
CARPETA_USUARIO.mkdir(exist_ok=True)

RUTA_EXCEL_USUARIO = CARPETA_USUARIO / "archivo_excel.bin"
RUTA_METADATA_USUARIO = CARPETA_USUARIO / "metadata.json"

archivo_subido = st.file_uploader(
    "Arrastra o selecciona tu archivo Excel (.xlsx o .xls)",
    type=["xlsx", "xls"],
    key="archivo_excel_usuario"
)

# ------------------------------------------------------------
# Si el usuario sube un archivo nuevo, se guarda físicamente.
# Si ya había uno guardado para ese usuario, se reemplaza.
# ------------------------------------------------------------

if archivo_subido is not None:
    nombre_archivo_subido = archivo_subido.name

    if not nombre_archivo_subido.lower().endswith((".xlsx", ".xls")):
        st.error("El archivo cargado no es válido. Por favor, sube un archivo de Excel en formato .xlsx o .xls.")
        st.stop()

    RUTA_EXCEL_USUARIO.write_bytes(archivo_subido.getvalue())

    metadata = {
        "nombre_archivo": nombre_archivo_subido,
        "fecha_carga": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    RUTA_METADATA_USUARIO.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )

# ------------------------------------------------------------
# Si no hay archivo subido en este momento, intentamos cargar
# el archivo que ya estaba guardado para este usuario.
# ------------------------------------------------------------

if not RUTA_EXCEL_USUARIO.exists():
    st.info("Carga tu archivo Excel para comenzar.")
    st.stop()

try:
    metadata = json.loads(
        RUTA_METADATA_USUARIO.read_text(encoding="utf-8")
    )
    nombre_archivo = metadata.get("nombre_archivo", "archivo cargado")

except Exception:
    nombre_archivo = "archivo cargado"

st.success(f"Archivo activo: {nombre_archivo}")

st.info(
    "🔒 El archivo quedó guardado para este usuario. "
    "Si cierras la página y quieres recuperarlo después, vuelve a entrar usando esta misma URL del navegador."
)

try:
    archivo_bytes_actual = RUTA_EXCEL_USUARIO.read_bytes()
    hojas = obtener_hojas_excel_cache(archivo_bytes_actual)

except Exception:
    st.error("No fue posible leer el archivo. Verifica que sea un archivo de Excel válido y que no esté dañado.")
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
    df = cargar_hoja_excel_cache(
        archivo_bytes_actual,
        hoja_seleccionada,
        fila_encabezado
    )

except Exception as e:
    st.error(f"No se pudo cargar la hoja seleccionada. Error: {e}")
    st.stop()

st.success("Archivo procesado correctamente.")

st.markdown(
    '<h3 class="infosabana-subtitle">Vista previa del archivo</h3>',
    unsafe_allow_html=True
)

m1, m2 = st.columns(2)
m1.metric("Filas detectadas", f"{len(df):,}")
m2.metric("Columnas detectadas", f"{len(df.columns):,}")

st.dataframe(
    df.head(20),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 2. DETECTAR COLUMNAS Y PREPARAR BASE
# ============================================================

columnas_detectadas, columnas_faltantes, base, periodos_disponibles, lista_ciclos = preparar_base_cache(df)

if columnas_faltantes:
    st.error(
        "No se encontraron algunas columnas requeridas en el Excel. "
        "Revisa que los encabezados estén en la fila correcta."
    )

    st.write("Columnas faltantes:")
    st.write(columnas_faltantes)

    st.stop()

if base is None or base.empty:
    st.error("No se detectaron ciclos lectivos válidos. Revisa la columna 'Ciclo Lectivo'.")
    st.stop()

if len(lista_ciclos) == 0:
    st.error("No hay ciclos lectivos disponibles para consultar.")
    st.stop()


# Variables de columnas reales del Excel
COL_CICLO = columnas_detectadas["Ciclo Lectivo"]
COL_CURSO = columnas_detectadas["Nombre del curso"]
COL_COMPONENTE = columnas_detectadas["Componente"]
COL_TOTAL_INSCRITOS = columnas_detectadas["Total Inscritos"]
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
# 4. CONSULTA DOCENTE
# ============================================================

st.divider()
st.markdown(
    '<h3 class="infosabana-subtitle">Consulta Docente</h3>',
    unsafe_allow_html=True
)

TIPO_BUSQUEDA_KEY = "tipo_busqueda_docente_actual"
VALOR_DOCUMENTO_KEY = "valor_busqueda_documento_docente_actual"
VALOR_ID_KEY = "valor_busqueda_id_docente_actual"
VALOR_NOMBRE_KEY = "valor_busqueda_nombre_profesor_actual"
CICLO_INICIAL_KEY = "ciclo_inicial_docente_actual"
CICLO_FINAL_KEY = "ciclo_final_docente_actual"

TIPOS_BUSQUEDA_DOCENTE = [
    "Número documento docente",
    "Nombre profesor",
    "Id profesor"
]

if st.session_state.get(TIPO_BUSQUEDA_KEY) not in TIPOS_BUSQUEDA_DOCENTE:
    st.session_state[TIPO_BUSQUEDA_KEY] = "Número documento docente"

# Este selector va fuera del form para que el label cambie inmediatamente.
tipo_busqueda_visual = st.selectbox(
    "Seleccione tipo de búsqueda",
    TIPOS_BUSQUEDA_DOCENTE,
    key=TIPO_BUSQUEDA_KEY
)

if tipo_busqueda_visual == "Id profesor":
    label_input = "Ingrese ID docente"
    placeholder_input = "Ejemplo: 000012345"
    valor_key_actual = VALOR_ID_KEY

elif tipo_busqueda_visual == "Nombre profesor":
    label_input = "Ingrese nombre del profesor"
    placeholder_input = "Ejemplo: PEREZ HERNANDEZ ADRIAN FELIPE"
    valor_key_actual = VALOR_NOMBRE_KEY

else:
    label_input = "Ingrese número de documento"
    placeholder_input = "Ejemplo: 21435432"
    valor_key_actual = VALOR_DOCUMENTO_KEY

with st.form("form_consulta_docente", clear_on_submit=False):

    st.text_input(
        label_input,
        placeholder=placeholder_input,
        key=valor_key_actual
    )

    col_ini, col_fin = st.columns(2)

    with col_ini:
        ciclo_inicial = st.selectbox(
            "Ciclo lectivo inicial",
            lista_ciclos,
            index=0,
            key=CICLO_INICIAL_KEY
        )

    with col_fin:
        ciclo_final = st.selectbox(
            "Ciclo lectivo final",
            lista_ciclos,
            index=len(lista_ciclos) - 1,
            key=CICLO_FINAL_KEY
        )

    col_buscar, col_config = st.columns([1, 1])

    with col_buscar:
        buscar = st.form_submit_button(
            "Buscar información docente",
            type="primary"
        )

    with col_config:
        with st.popover("Configurar columnas"):
            st.markdown("#### Columnas de la tabla")
            st.caption(
                "Selecciona mínimo 2 columnas. "
                "La selección se aplicará cuando oprimas 'Buscar información docente'."
            )

            st.divider()

            for columna in COLUMNAS_RESULTADO_DISPONIBLES:
                key_checkbox = COLUMNAS_CHECK_PREFIX + columna

                if key_checkbox not in st.session_state:
                    st.session_state[key_checkbox] = True

                st.checkbox(
                    columna,
                    key=key_checkbox
                )
# ============================================================
# 5. PROCESAR BÚSQUEDA
# ============================================================

if buscar:

    tipo_busqueda = st.session_state[TIPO_BUSQUEDA_KEY]

    if tipo_busqueda == "Id profesor":
        valor_busqueda = st.session_state.get(VALOR_ID_KEY, "")
    elif tipo_busqueda == "Nombre profesor":
        valor_busqueda = st.session_state.get(VALOR_NOMBRE_KEY, "")
    else:
        valor_busqueda = st.session_state.get(VALOR_DOCUMENTO_KEY, "")

    ciclo_inicial = st.session_state[CICLO_INICIAL_KEY]
    ciclo_final = st.session_state[CICLO_FINAL_KEY]

    st.session_state[COLUMNAS_CONFIRMADAS_KEY] = [
        columna
        for columna in COLUMNAS_RESULTADO_DISPONIBLES
        if st.session_state.get(COLUMNAS_CHECK_PREFIX + columna, True)
    ]

    valor_texto = str(valor_busqueda).strip()

    if valor_texto == "":
        if tipo_busqueda == "Nombre profesor":
            st.error(
                "Ingresa el nombre del profesor para realizar la búsqueda. "
                "Escribe nombres y apellidos para evitar coincidencias ambiguas."
            )
        elif tipo_busqueda == "Id profesor":
            st.error(
                "Ingresa el ID docente para realizar la búsqueda. "
                "Este campo debe contener únicamente números."
            )
        else:
            st.error(
                "Ingresa el número de documento del docente para realizar la búsqueda. "
                "Este campo debe contener únicamente números."
            )

        st.stop()

    columnas_seleccionadas = st.session_state.get(
        COLUMNAS_CONFIRMADAS_KEY,
        COLUMNAS_RESULTADO_DISPONIBLES.copy()
    )

    if len(columnas_seleccionadas) == 0:
        st.error(
            "No tienes ninguna columna seleccionada. "
            "Selecciona mínimo 2 columnas para mostrar la tabla."
        )
        st.stop()

    if len(columnas_seleccionadas) == 1:
        st.error(
            "Solo tienes una columna seleccionada. "
            "Debes seleccionar mínimo 2 columnas para mostrar la tabla."
        )
        st.stop()

    orden_inicial = periodos_disponibles.loc[
        periodos_disponibles["_ciclo_limpio"] == ciclo_inicial,
        "_ciclo_orden"
    ].iloc[0]

    orden_final = periodos_disponibles.loc[
        periodos_disponibles["_ciclo_limpio"] == ciclo_final,
        "_ciclo_orden"
    ].iloc[0]

    if orden_inicial > orden_final:
        st.error(
            "El ciclo lectivo inicial no puede ser mayor que el ciclo lectivo final. "
            "Ajusta el rango e intenta nuevamente."
        )
        st.stop()

    tipo_busqueda_norm = normalizar_texto(tipo_busqueda)

    # ------------------------------------------------------------
    # Resolver búsqueda por documento, ID o nombre
    # ------------------------------------------------------------

    if tipo_busqueda_norm in [
        "NUMERO DOCUMENTO DOCENTE",
        "NUMERO DE DOCUMENTO",
        "DOCUMENTO DE IDENTIDAD",
        "DOCUMENTO"
    ]:
        if not valor_es_solo_numeros(valor_busqueda):
            st.error(
                "El número de documento debe contener únicamente números. "
                "No incluyas letras, puntos, comas, espacios ni caracteres especiales."
            )
            st.stop()

        valor_limpio = limpiar_codigo(valor_busqueda)
        valor_sin_ceros = quitar_ceros_izquierda(valor_busqueda)

        filtro_id = (
            (base["_doc_limpio"] == valor_limpio) |
            (base["_doc_sin_ceros"] == valor_sin_ceros)
        )

        registros_docente = base[filtro_id].copy()

        if registros_docente.empty:
            st.error(
                "No se encontró ningún docente registrado con el número de documento ingresado. "
                "Verifica el dato e intenta nuevamente."
            )
            st.stop()

    elif tipo_busqueda_norm in [
        "ID PROFESOR",
        "ID DOCENTE"
    ]:
        if not valor_es_solo_numeros(valor_busqueda):
            st.error(
                "El ID docente debe contener únicamente números. "
                "No incluyas letras, puntos, comas, espacios ni caracteres especiales."
            )
            st.stop()

        valor_limpio = limpiar_codigo(valor_busqueda)
        valor_sin_ceros = quitar_ceros_izquierda(valor_busqueda)

        filtro_id = (
            (base["_id_prof_limpio"] == valor_limpio) |
            (base["_id_prof_sin_ceros"] == valor_sin_ceros)
        )

        registros_docente = base[filtro_id].copy()

        if registros_docente.empty:
            st.error(
                "No se encontró ningún docente registrado con el ID docente ingresado. "
                "Verifica el dato e intenta nuevamente."
            )
            st.stop()

    elif tipo_busqueda_norm in [
        "NOMBRE PROFESOR",
        "NOMBRE DOCENTE",
        "PROFESOR",
        "DOCENTE"
    ]:
        resultado_nombre = resolver_busqueda_por_nombre_profesor(
            base=base,
            nombre_ingresado=valor_busqueda,
            col_nombre_prof=COL_NOMBRE_PROF,
            col_doc=COL_DOC,
            col_id_prof=COL_ID_PROF,
            max_candidatos=8
        )

        if not resultado_nombre["ok"]:
            st.error(resultado_nombre["mensaje"])

            candidatos = resultado_nombre.get("candidatos", pd.DataFrame())

            if candidatos is not None and not candidatos.empty:
                st.caption(
                    "Coincidencias encontradas. Para evitar errores, usa el documento docente "
                    "o el ID docente del profesor correcto."
                )
                mostrar_candidatos_nombre_profesor(candidatos)

            st.stop()

        tipo_identificador = resultado_nombre["tipo_identificador"]
        valor_identificador = resultado_nombre["valor_identificador"]

        valor_limpio = limpiar_codigo(valor_identificador)
        valor_sin_ceros = quitar_ceros_izquierda(valor_identificador)

        # Para mostrar en pantalla el nombre limpio encontrado.
        valor_busqueda = resultado_nombre["nombre_mostrar"]

        if tipo_identificador == "documento":
            filtro_id = (
                (base["_doc_limpio"] == valor_limpio) |
                (base["_doc_sin_ceros"] == valor_sin_ceros)
            )
        else:
            filtro_id = (
                (base["_id_prof_limpio"] == valor_limpio) |
                (base["_id_prof_sin_ceros"] == valor_sin_ceros)
            )

        registros_docente = base[filtro_id].copy()

        if registros_docente.empty:
            st.error(
                "Se identificó un docente por nombre, pero no fue posible recuperar "
                "sus registros académicos. Intenta realizar la búsqueda por documento "
                "docente o ID docente."
            )
            st.stop()

    else:
        st.error(
            "Tipo de búsqueda no reconocido. Selecciona documento docente, ID docente "
            "o nombre profesor."
        )
        st.stop()

    # ------------------------------------------------------------
    # Aplicar rango de ciclo lectivo seleccionado
    # ------------------------------------------------------------

    resultado = registros_docente[
        (registros_docente["_ciclo_orden"] >= orden_inicial) &
        (registros_docente["_ciclo_orden"] <= orden_final)
    ].copy()

    if resultado.empty:
        st.warning(
            "El docente existe en la base de datos, pero no tiene registros académicos "
            "en el rango de ciclo lectivo seleccionado."
        )
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

    columnas_seleccionadas = st.session_state.get(
        COLUMNAS_CONFIRMADAS_KEY,
        COLUMNAS_RESULTADO_DISPONIBLES.copy()
    )

    if len(columnas_seleccionadas) < 2:
        st.error(
            "La tabla no puede mostrarse con menos de 2 columnas. "
            "Abre 'Configurar columnas' y selecciona mínimo 2 columnas."
        )
        st.stop()

    tabla_mostrar = tabla_final[columnas_seleccionadas].copy()

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

    excel_bytes = dataframe_a_excel_bytes(tabla_mostrar)
    correo_html = generar_correo_html(nombre_profesor, tabla_mostrar)

    col_descargar, col_copiar, col_vacio = st.columns([1.2, 1.2, 3])

    with col_descargar:
        st.download_button(
            label="Descargar resultado en Excel",
            data=excel_bytes,
            file_name=f"resultado_docente_{valor_limpio}_{ciclo_inicial}_a_{ciclo_final}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            on_click="ignore"
        )

    with col_copiar:
        boton_copiar_correo(correo_html)