import streamlit as st
import pandas as pd

# ==========================================
# 1. CONFIGURACIÓN Y CONSTANTES (SSoT)
# ==========================================
# Datos extraídos de image_c8496b.png y image_c7ce40.png
HABERES_FIJOS = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Movilización": 63847,
    "Colación": 53372,
    "Ajuste Sencillo": 104
}

# Matriz de Oferta Táctica Enero 2026
MATRIZ_TACTICA = {
    12990: {2: 9093, 3: 9093, 4: 7990}, # 200GB
    15990: {2: 7196, 3: 6396, 4: 5597}, # 400GB
    18990: {2: 7596, 3: 6077, 4: 5697}, # Libre
    23990: {2: 9596, 3: 7677, 4: 7197}  # Libre+
}

# Multiplicadores Anexo Grandes Cuentas
MULTIPLICADORES = {
    "BAM / Nueva / Porta Prepago": [2.0, 2.3, 2.7],
    "Portabilidad Postpago": [2.8, 3.1, 3.4],
    "Voz s/Porta + Equipo": [2.9, 3.2, 3.5],
    "Porta + Equipo": [3.1, 3.4, 3.7]
}

# ==========================================
# 2. MOTOR DE CÁLCULO (BUSINESS LOGIC)
# ==========================================
class CommissionEngine:
    @staticmethod
    def get_tactical_arpu(plan_base, num_lineas):
        """Calcula el ARPU neto tras descuentos por volumen (2026)."""
        if num_lineas < 2: return plan_base
        descuentos = MATRIZ_TACTICA.get(plan_base, {})
        # Si son 4 o más, aplica el máximo descuento
        return descuentos.get(min(num_lineas, 4), plan_base)

    @staticmethod
    def get_interval(total_lineas):
        """Determina el tramo comisional. Mínimo 30 para pago."""
        if total_lineas < 30: return None
        if total_lineas <= 110: return 0 # Intervalo 1
        if total_lineas <= 225: return 1 # Intervalo 2
        return 2 # Intervalo 3

    @staticmethod
    def calculate_semana_corrida(comision_variable, dias_habiles, dom_fest):
        """Fórmula legal: (Comisión / Días Trabajados) * Días Descanso."""
        if dias_habiles <= 0: return 0
        return (comision_variable / dias_habiles) * dom_fest

# ==========================================
# 3. INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
def main():
    st.set_page_config(page_title="Calculadora de Comisiones WOM", layout="wide")
    
    st.title("💰 Calculadora de Renta Final - Grandes Cuentas")
    st.markdown("---")

    # SIDEBAR: Haberes Fijos
    with st.sidebar:
        st.header("📋 Haberes Fijos (Contrato)")
        st.info("Valores detectados en tu última liquidación.")
        for concepto, valor in HABERES_FIJOS.items():
            st.write(f"**{concepto}:** ${valor:,}")
        
        st.divider()
        st.header("📅 Parámetros del Mes")
        dias_h = st.number_input("Días Hábiles (L-V/S)", value=21, min_value=1)
        feriados = st.number_input("Domingos y Festivos", value=5, min_value=0)

    # CUERPO PRINCIPAL
    col_in, col_out = st.columns([1, 1.2])

    with col_in:
        st.subheader("🛒 Simulación de Ventas")
        tipo_v = st.selectbox("Tipo de Producto", list(MULTIPLICADORES.keys()))
        plan_v = st.selectbox("Plan Comercial", [12990, 15990, 18990, 23990], format_func=lambda x: f"${x:,}")
        cantidad = st.number_input("Cantidad de Líneas", min_value=0, value=30, step=1)
        
        arpu_calc = CommissionEngine.get_tactical_arpu(plan_v, cantidad)
        intervalo = CommissionEngine.get_interval(cantidad)
        
        st.write("---")
        if intervalo is None:
            st.error("⚠️ No se alcanza el mínimo de 30 líneas para comisionar.")
            comision_neta = 0
        else:
            factor = MULTIPLICADORES[tipo_v][intervalo]
            comision_neta = (arpu_calc * factor) * cantidad
            st.success(f"Multiplicador aplicado: **x{factor}**")

    with col_out:
        st.subheader("🧾 Proyección de Liquidación")
        
        # Cálculo de Semana Corrida
        sc = CommissionEngine.calculate_semana_corrida(comision_neta, dias_h, feriados)
        
        # Tope de comisión
        if comision_neta > 3500000:
            comision_neta = 3500000
            st.warning("Tope máximo de comisión ($3.5MM) alcanzado.")

        total_imponible = (HABERES_FIJOS["Sueldo Base"] + 
                           HABERES_FIJOS["Gratificación Legal"] + 
                           comision_neta + sc)
        
        total_no_imponible = HABERES_FIJOS["Movilización"] + HABERES_FIJOS["Colación"]
        
        # Descuentos legales estimados (Chile ~20%)
        descuentos_est = total_imponible * 0.19
        renta_liquida = (total_imponible - descuentos_est) + total_no_imponible

        # Visualización de Resultados
        st.metric("Comisión de Ventas", f"${int(comision_neta):,}")
        st.metric("Semana Corrida", f"${int(sc):,}")
        
        st.divider()
        st.header(f"Renta Líquida Estimada: ${int(renta_liquida):,}")
        
        with st.expander("Ver desglose técnico"):
            detalle = {
                "Concepto": ["Imponible Fijo", "Comisión Variable", "Semana Corrida", "No Imponibles", "Descuentos (AFP/Salud)"],
                "Monto": [
                    HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"],
                    int(comision_neta),
                    int(sc),
                    total_no_imponible,
                    -int(descuentos_est)
                ]
            }
            st.table(pd.DataFrame(detalle))

if __name__ == "__main__":
    main()
