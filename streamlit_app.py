import streamlit as st
import pandas as pd

# =================================================================
# 1. DATA MODELS (Valores exactos de tus liquidaciones)
# =================================================================
# Basado en image_c85ce6.png e image_c85528.png
HABERES_FIJOS = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Bono Colación": 53372,
    "Bono Movilización": 63847,
    "Ajuste Sencillo": 104
}

# Matriz Táctica Enero 2026
TACTICAL_PRICING = {
    12990: {2: 9093, 3: 9093, 4: 7990},
    15990: {2: 7196, 3: 6396, 4: 5597},
    18990: {2: 7596, 3: 6077, 4: 5697},
    23990: {2: 9596, 3: 7677, 4: 7197}
}

# Anexo Comisional
COMMISSION_MATRIX = {
    "BAM / Nueva / Porta Prepago": [2.0, 2.3, 2.7],
    "Portabilidad Postpago": [2.8, 3.1, 3.4],
    "Voz s/Porta + Equipo": [2.9, 3.2, 3.5],
    "Porta + Equipo": [3.1, 3.4, 3.7]
}

# =================================================================
# 2. LOGIC ENGINES (Cálculos robustos)
# =================================================================
class CommissionEngine:
    @staticmethod
    def get_arpu_final(base_plan, lines):
        """Calcula ARPU asegurando que nunca retorne None."""
        if lines < 2: 
            return base_plan
        
        # Obtenemos los descuentos para el plan. Si no hay, devolvemos el base.
        plan_discounts = TACTICAL_PRICING.get(base_plan, {})
        
        # Buscamos el descuento por cantidad de líneas (máximo 4+)
        lookup_lines = min(lines, 4)
        arpu_con_descuento = plan_discounts.get(lookup_lines)
        
        # Si no hay descuento específico para ese número, devolvemos el base
        return arpu_con_descuento if arpu_con_descuento is not None else base_plan

    @staticmethod
    def get_commission_total(tipo, lines, arpu):
        """Aplica multiplicadores y tope de $3.5MM."""
        if lines < 30: 
            return 0
        
        # Determinar intervalo (0: 30-110, 1: 111-225, 2: 226+)
        if lines >= 226: idx = 2
        elif lines >= 111: idx = 1
        else: idx = 0
            
        multiplier = COMMISSION_MATRIX.get(tipo, [0, 0, 0])[idx]
        total = (arpu * multiplier) * lines
        
        # Aplicar tope comisional
        return min(total, 3500000)

class TaxEngine:
    @staticmethod
    def calculate_net(taxable, non_taxable):
        """Descuentos legales Chile 2026 (Estimado AFP 11.5%, Salud 7%, Cesantía 0.6%)"""
        if taxable <= 0: return non_taxable
        
        legal_deductions = taxable * (0.115 + 0.07 + 0.006)
        
        # Impuesto Único simplificado (sobrepasando los ~$850.000 de base tributable)
        tributable = taxable - legal_deductions
        impuesto = 0
        if tributable > 850000:
            impuesto = (tributable * 0.04) - 35000 # Rebaja referencial tramo 2
            
        return (taxable - legal_deductions - max(0, impuesto)) + non_taxable

# =================================================================
# 3. INTERFAZ (UI)
# =================================================================
def main():
    st.set_page_config(page_title="WOM Renta Pro", layout="wide")
    st.title("💰 Calculadora de Comisiones y Renta Final")
    st.markdown("---")

    c1, c2 = st.columns([1, 1.2], gap="large")

    with c1:
        st.subheader("📊 Simulación de Venta")
        tipo = st.selectbox("Categoría de Venta", list(COMMISSION_MATRIX.keys()))
        plan = st.selectbox("Plan Comercial", [12990, 15990, 18990, 23990], format_func=lambda x: f"${x:,}")
        cantidad = st.number_input("Total Líneas", min_value=0, value=30)
        
        st.divider()
        st.subheader("📅 Parámetros Mes")
        hábiles = st.slider("Días Hábiles", 1, 26, 21)
        festivos = st.slider("Domingos/Festivos", 1, 10, 5)

    with c2:
        # Cálculos vinculados
        arpu_final = CommissionEngine.get_arpu_final(plan, cantidad)
        comision = CommissionEngine.get_commission_total(tipo, cantidad, arpu_final)
        
        # Semana Corrida
        sc = (comision / hábiles) * festivos if hábiles > 0 else 0
        
        total_imp = HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"] + comision + sc
        total_no_imp = sum([HABERES_FIJOS["Bono Colación"], HABERES_FIJOS["Bono Movilización"], HABERES_FIJOS["Ajuste Sencillo"]])
        
        renta_liq = TaxEngine.calculate_net(total_imp, total_no_imp)

        # Resultados Visuales
        st.subheader("🧾 Resultados Proyectados")
        k1, k2 = st.columns(2)
        k1.metric("Comisión Neta", f"${int(comision):,}")
        k2.metric("Semana Corrida", f"${int(sc):,}")
        
        st.divider()
        st.success(f"## Sueldo Líquido: ${int(renta_liq):,}")
        
        with st.expander("Detalle de Haberes Fijos"):
            st.json(HABERES_FIJOS)

if __name__ == "__main__":
    main()
