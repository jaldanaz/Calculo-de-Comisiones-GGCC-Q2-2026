import streamlit as st
import pandas as pd

# ==========================================
# 1. CONSTANTES (SSoT)
# ==========================================
HABERES_FIJOS = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Movilización": 63847,
    "Colación": 53372,
    "Ajuste Sencillo": 104
}

# Solo aplica a Portabilidad
TACTICAL_MATRIX = {
    12990: {2: 9093, 3: 9093, 4: 7990},
    15990: {2: 7196, 3: 6396, 4: 5597},
    18990: {2: 7596, 3: 6077, 4: 5697},
    23990: {2: 9596, 3: 7677, 4: 7197}
}

MULTIPLICADORES = {
    "BAM / Nueva / Porta Prepago": [2.0, 2.3, 2.7],
    "Portabilidad Postpago": [2.8, 3.1, 3.4],
    "Voz s/Porta + Equipo": [2.9, 3.2, 3.5],
    "Porta + Equipo": [3.1, 3.4, 3.7]
}

# ==========================================
# 2. LOGIC ENGINE
# ==========================================
class SalesManager:
    @staticmethod
    def get_arpu(tipo, plan_base, cant):
        # El descuento táctico es EXCLUSIVO para portabilidades de 2+ líneas
        if "Porta" in tipo and cant >= 2:
            return TACTICAL_MATRIX.get(plan_base, {}).get(min(cant, 4), plan_base)
        return plan_base

    @staticmethod
    def get_interval_index(total_lines):
        if total_lines < 30: return None
        if total_lines <= 110: return 0
        if total_lines <= 225: return 1
        return 2

# ==========================================
# 3. INTERFAZ (MIX DE VENTAS)
# ==========================================
def main():
    st.set_page_config(page_title="WOM Sales Mix Pro", layout="wide")
    
    # Inicializar el "carritos de ventas" si no existe
    if 'mix_ventas' not in st.session_state:
        st.session_state.mix_ventas = []

    st.title("🚀 Mix de Ventas y Renta Final")
    
    col_input, col_summary = st.columns([1, 1.2])

    with col_input:
        st.subheader("📥 Cargar Nueva Venta")
        with st.form("form_venta", clear_on_submit=True):
            cliente = st.text_input("Nombre Cliente / ID Proyecto", placeholder="Ej: Minera ABC")
            tipo = st.selectbox("Tipo de Producto", list(MULTIPLICADORES.keys()))
            plan = st.selectbox("Plan Base", [12990, 15990, 18990, 23990], format_func=lambda x: f"${x:,}")
            cant = st.number_input("Cantidad de Líneas", min_value=1, step=1)
            
            submit = st.form_submit_button("Agregar al Mix Mensual")
            if submit:
                arpu_final = SalesManager.get_arpu(tipo, plan, cant)
                st.session_state.mix_ventas.append({
                    "Cliente": cliente,
                    "Tipo": tipo,
                    "Plan": plan,
                    "Líneas": cant,
                    "ARPU Calc": arpu_final
                })

        if st.button("Limpiar Mes (Borrar todo)"):
            st.session_state.mix_ventas = []
            st.rerun()

    with col_summary:
        st.subheader("📋 Resumen del Mix")
        if not st.session_state.mix_ventas:
            st.info("No has cargado ventas aún. Usa el formulario de la izquierda.")
            total_lines = 0
        else:
            df = pd.DataFrame(st.session_state.mix_ventas)
            st.table(df)
            total_lines = df["Líneas"].sum()
            
            # --- CÁLCULOS FINALES ---
            idx = SalesManager.get_interval_index(total_lines)
            
            comision_total = 0
            if idx is not None:
                for v in st.session_state.mix_ventas:
                    mult = MULTIPLICADORES[v["Tipo"]][idx]
                    comision_total += (v["ARPU Calc"] * mult * v["Líneas"])
                
                comision_total = min(comision_total, 3500000) # Tope legal
            
            # --- RENTA FINAL ---
            st.divider()
            h_habiles = st.slider("Días Hábiles Trabajados", 1, 26, 21)
            h_festivos = st.slider("Domingos/Festivos", 1, 10, 5)
            
            semana_corrida = (comision_total / h_habiles) * h_festivos if h_habiles > 0 else 0
            
            # Imponible total = Fijos + Comisión + SC
            total_imp = HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"] + comision_total + semana_corrida
            
            # Cálculo Neto (Descuentos legales aprox 19% + Impuesto Único)
            # Para PoC usamos un factor neto de 0.81 (19% desc)
            neto_estimado = (total_imp * 0.81) + HABERES_FIJOS["Movilización"] + HABERES_FIJOS["Colación"] + HABERES_FIJOS["Ajuste Sencillo"]

            # KPIs
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Líneas", f"{total_lines}", delta=f"{30-total_lines if total_lines < 30 else 'Meta OK'}")
            m2.metric("Comisión Acum.", f"${int(comision_total):,}")
            m3.metric("Semana Corrida", f"${int(semana_corrida):,}")

            st.success(f"### 💰 Sueldo Líquido Proyectado: ${int(neto_estimado):,}")

if __name__ == "__main__":
    main()
