import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="WOM Comisiones - Jorge Aldana", layout="wide")

# --- LÓGICA DE NEGOCIO (ANEXO + OFERTA ENERO 2026) ---
def calcular_arpu_tactico(plan_base, num_lineas):
    """Aplica la tabla de descuentos de la Nueva Oferta Táctica 2026"""
    #
    tarifas = {
        12990: {2: 9093, 3: 9093, 4: 7990}, # 200GB
        15990: {2: 7196, 3: 6396, 4: 5597}, # 400GB
        18990: {2: 7596, 3: 6077, 4: 5697}, # Libre
        23990: {2: 9596, 3: 7677, 4: 7197}  # Libre+
    }
    if plan_base not in tarifas: return plan_base
    if num_lineas >= 4: return tarifas[plan_base][4]
    return tarifas[plan_base].get(num_lineas, plan_base)

def obtener_multiplicador(tipo, total_lineas):
    """Matriz comisional según Anexo"""
    intervalo = 0
    if total_lineas >= 226: intervalo = 2
    elif total_lineas >= 111: intervalo = 1
    elif total_lineas >= 30: intervalo = 0
    else: return 0 # No comisiona menos de 30 líneas

    matriz = {
        "BAM / Nueva / Prepago": [2.0, 2.3, 2.7],
        "Porta Postpago": [2.8, 3.1, 3.4],
        "Voz + Equipo": [2.9, 3.2, 3.5],
        "Porta + Equipo": [3.1, 3.4, 3.7]
    }
    return matriz[tipo][intervalo]

# --- INTERFAZ ---
st.title("🚀 Calculadora de Renta Final - Grandes Cuentas")

with st.sidebar:
    st.header("📋 Haberes Fijos (Cuadro Morado)")
    # Datos extraídos de
    base = st.number_input("Sueldo Base", value=633513) 
    grat = st.number_input("Gratificación Legal", value=178694)
    movil = st.number_input("Movilización", value=63847)
    colac = st.number_input("Colación", value=53372)
    # incluye estos montos específicos.

tab1, tab2 = st.tabs(["💰 Simulador de Ventas", "📊 Liquidación Proyectada"])

with tab1:
    st.subheader("Simulador de Oferta Táctica")
    col1, col2, col3 = st.columns(3)
    
    plan_sel = col1.selectbox("Plan Comercial", [12990, 15990, 18990, 23990], format_func=lambda x: f"${x:,}")
    n_lineas = col2.number_input("Cantidad de Líneas", min_value=1, value=30)
    tipo_v = col3.selectbox("Tipo de Venta", ["BAM / Nueva / Prepago", "Porta Postpago", "Voz + Equipo", "Porta + Equipo"])
    
    arpu_final = calcular_arpu_tactico(plan_sel, n_lineas)
    mult = obtener_multiplicador(tipo_v, n_lineas)
    
    comision_total = (arpu_final * mult) * n_lineas
    
    st.metric("ARPU con Descuento Táctico", f"${int(arpu_final):,}", help="Aplicando matriz de portabilidad 2+ líneas")
    st.metric("Comisión Proyectada", f"${int(comision_total):,}")

with tab2:
    st.subheader("Cálculo de Renta Líquida")
    
    # Semana Corrida: (Comisiones / Días Hábiles) * Domingos
    d_habiles = st.slider("Días Hábiles trabajados", 1, 26, 20)
    festivos = st.slider("Domingos y Festivos", 1, 10, 5)
    semana_corrida = (comision_total / d_habiles) * festivos if d_habiles > 0 else 0
    
    total_imponible = base + grat + comision_total + semana_corrida
    total_no_imponible = movil + colac
    
    # Descuentos legales estimados (Chile)
    afp_salud = total_imponible * 0.18 # Estimación promedio AFP + Fonasa/Isapre
    
    liquido = (total_imponible - afp_salud) + total_no_imponible
    
    c1, c2 = st.columns(2)
    c1.write("**Detalle de Haberes:**")
    c1.write(f"- Sueldo Base: ${base:,}")
    c1.write(f"- Gratificación: ${grat:,}")
    c1.write(f"- Comisión Venta: ${int(comision_total):,}")
    c1.write(f"- Semana Corrida: ${int(semana_corrida):,}")
    
    st.divider()
    st.header(f"Total Líquido: ${int(liquido):,}")
    st.info("Nota: Este cálculo usa el tope comisional de $3.500.000 definido en tu anexo.")
