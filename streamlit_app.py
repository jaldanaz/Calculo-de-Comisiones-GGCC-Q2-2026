import streamlit as st
import pandas as pd

# =================================================================
# 1. DATA MODELS & CONSTANTS (Single Source of Truth)
# =================================================================
# Basado en tus liquidaciones: image_c85528.png e image_c8496b.png
FIXED_HABERES = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Bono Colación": 53372,
    "Bono Movilización": 63847,
    "Ajuste Sencillo": 104
}

# Oferta Táctica Enero 2026
TACTICAL_PRICING = {
    12990: {2: 9093, 3: 9093, 4: 7990},
    15990: {2: 7196, 3: 6396, 4: 5597},
    18990: {2: 7596, 3: 6077, 4: 5697},
    23990: {2: 9596, 3: 7677, 4: 7197}
}

# Anexo Comisional Grandes Cuentas
COMMISSION_MATRIX = {
    "BAM / Nueva / Porta Prepago": [2.0, 2.3, 2.7],
    "Portabilidad Postpago": [2.8, 3.1, 3.4],
    "Voz s/Porta + Equipo": [2.9, 3.2, 3.5],
    "Porta + Equipo": [3.1, 3.4, 3.7]
}

# =================================================================
# 2. LOGIC ENGINES (Cálculos de Ingeniería)
# =================================================================
class CommissionEngine:
    @staticmethod
    def get_arpu(base_plan, lines):
        if lines < 2: return base_plan
        return TACTICAL_PRICING.get(base_plan, {}).get(min(lines, 4), base_plan)

    @staticmethod
    def get_commission(tipo, lines, arpu):
        if lines < 30: return 0 # Mínimo comisional
        idx = 2 if lines >= 226 else (1 if lines >= 111 else 0)
        multiplier = COMMISSION_MATRIX[tipo][idx]
        raw_comm = (arpu * multiplier) * lines
        return min(raw_comm, 3500000) # Tope comisional

class TaxEngine:
    @staticmethod
    def calculate_net(gross_taxable, non_taxable):
        """Calcula el sueldo líquido aplicando descuentos legales chilenos."""
        # Estimaciones estándar 2026
        afp = gross_taxable * 0.115 # AFP promedio + SIS
        salud = gross_taxable * 0.07 # Fonasa/Isapre base
        cesantia = gross_taxable * 0.006 # Seguro cesantía (contrato indefinido)
        
        # Impuesto Único (Cálculo simplificado para tramo intermedio)
        base_tax = gross_taxable - (afp + salud + cesantia)
        impuesto = 0
        if base_tax > 850000: # Tramo exento aproximado
            impuesto = (base_tax * 0.04) - 35000 # Factor y rebaja referencial
            
        return (gross_taxable - (afp + salud + cesantia + max(0, impuesto))) + non_taxable

# =================================================================
# 3. UI PRESENTATION LAYER (Streamlit)
# =================================================================
def main():
    st.set_page_config(page_title="WOM Commission Pro - Jorge Aldana", layout="wide")
    
    # Custom CSS para imitar el look & feel corporativo
    st.markdown("""<style> .main { background-color: #f5f5f5; } .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); } </style>""", unsafe_allow_html=True)

    st.title("💰 Calculadora de Renta Final")
    st.caption("Grandes Cuentas | PoC Certificada 2026")

    col_config, col_results = st.columns([1, 1.2], gap="large")

    with col_config:
        st.subheader("⚙️ Configuración del Mes")
        with st.expander("Haberes Fijos (Cuadro Morado)", expanded=False):
            for k, v in FIXED_HABERES.items():
                st.text(f"{k}: ${v:,}")
        
        tipo_venta = st.selectbox("Categoría de Venta", list(COMMISSION_MATRIX.keys()))
        plan_base = st.selectbox("Plan Comercial", [12990, 15990, 18990, 23990], format_func=lambda x: f"${x:,}")
        lineas = st.number_input("Total Líneas en Portabilidad", min_value=0, value=30, step=1)
        
        st.divider()
        st.subheader("📅 Parámetros Legales")
        d_habiles = st.number_input("Días Hábiles Mes", value=21, min_value=1)
        d_festivos = st.number_input("Domingos/Festivos", value=5, min_value=1)

    with col_results:
        # Lógica de negocio vinculada
        arpu_calc = CommissionEngine.get_arpu(plan_base, lineas)
        comision_final = CommissionEngine.get_commission(tipo_venta, lineas, arpu_calc)
        
        # Semana Corrida (Art. 45 Código del Trabajo)
        semana_corrida = (comision_final / d_habiles) * d_festivos if comision_final > 0 else 0
        
        total_imponible = FIXED_HABERES["Sueldo Base"] + FIXED_HABERES["Gratificación Legal"] + comision_final + semana_corrida
        total_no_imponible = FIXED_HABERES["Bono Colación"] + FIXED_HABERES["Bono Movilización"] + FIXED_HABERES["Ajuste Sencillo"]
        
        renta_liquida = TaxEngine.calculate_net(total_imponible, total_no_imponible)

        # Visualización de KPIs
        st.subheader("📊 Resultados de Proyección")
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("Comisión Neta", f"${int(comision_final):,}", delta="Tope: $3.5MM")
        kpi2.metric("Semana Corrida", f"${int(semana_corrida):,}")
        
        st.divider()
        st.success(f"## 💵 Renta Líquida Estimada: ${int(renta_liquida):,}")
        
        # Detalle de Validación para el Usuario
        with st.expander("Ver desglose para revisión (Auditoría)"):
            df_detalle = pd.DataFrame({
                "Concepto": ["Imponible Fijo", "Comisión Variable", "Semana Corrida", "No Imponible Total", "Deducciones Legales (AFP/Salud/Imp)"],
                "Monto": [
                    FIXED_HABERES["Sueldo Base"] + FIXED_HABERES["Gratificación Legal"],
                    int(comision_final),
                    int(semana_corrida),
                    int(total_no_imponible),
                    -int(total_imponible + total_no_imponible - renta_liquida)
                ]
            })
            st.table(df_detalle)

if __name__ == "__main__":
    main()
