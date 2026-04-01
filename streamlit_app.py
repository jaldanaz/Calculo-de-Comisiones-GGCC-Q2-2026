import streamlit as st
import pandas as pd
from io import StringIO

# ==========================================
# 1. CONSTANTES (Extraídas de tus Documentos)
# ==========================================
HABERES_FIJOS = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Movilización": 63847,
    "Colación": 53372,
    "Ajuste Sencillo": 104
}

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
# 2. MOTOR DE CÁLCULO AVANZADO
# ==========================================
class FinancialEngine:
    @staticmethod
    def get_arpu_details(tipo, plan, cant):
        if "Porta" in tipo and cant >= 2:
            arpu = TACTICAL_MATRIX.get(plan, {}).get(min(cant, 4), plan)
            ahorro = 1 - (arpu / plan)
            return arpu, f"{int(ahorro*100)}% (Táctico)"
        return plan, "0% (Base)"

    @staticmethod
    def get_tier_info(total_lines):
        if total_lines < 30: return None, "No alcanza mínimo (30)"
        if total_lines <= 110: return 0, "Intervalo 1 (30-110)"
        if total_lines <= 225: return 1, "Intervalo 2 (111-225)"
        return 2, "Intervalo 3 (226+)"

# ==========================================
# 3. INTERFAZ PROFESIONAL
# ==========================================
def main():
    st.set_page_config(page_title="WOM Financial Audit - Jorge Aldana", layout="wide")
    
    if 'mix_ventas' not in st.session_state:
        st.session_state.mix_ventas = []

    st.title("📈 Control de Ingresos y Mix de Ventas")
    st.info("Configuración basada en Anexo Comisional y Oferta Táctica Enero 2026.")

    tab_carga, tab_auditoria = st.tabs(["📥 Cargar Ventas", "🔍 Desglose de Ingresos"])

    with tab_carga:
        col_f, col_v = st.columns([1, 2])
        with col_f:
            with st.form("nueva_venta", clear_on_submit=True):
                st.subheader("Nueva Operación")
                cliente = st.text_input("Nombre del Cliente")
                tipo = st.selectbox("Tipo de Producto", list(MULTIPLICADORES.keys()))
                plan = st.selectbox("Plan", [12990, 15990, 18990, 23990])
                cant = st.number_input("Cantidad de Líneas", min_value=1, step=1)
                
                if st.form_submit_button("Confirmar y Sumar"):
                    arpu, desc_label = FinancialEngine.get_arpu_details(tipo, plan, cant)
                    st.session_state.mix_ventas.append({
                        "Cliente": cliente,
                        "Tipo": tipo,
                        "Plan Base": plan,
                        "Cant": cant,
                        "ARPU Neto": arpu,
                        "Desc.": desc_label
                    })
                    st.success("Venta agregada.")

        with col_v:
            st.subheader("Estado Actual del Mes")
            if st.session_state.mix_ventas:
                df = pd.DataFrame(st.session_state.mix_ventas)
                st.dataframe(df, use_container_width=True)
                
                # Exportación
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte Mensual (CSV)", data=csv, file_name="mix_ventas_wom.csv", mime="text/csv")
                
                if st.button("🗑️ Reiniciar Mes"):
                    st.session_state.mix_ventas = []
                    st.rerun()
            else:
                st.write("No hay datos cargados.")

    with tab_auditoria:
        if not st.session_state.mix_ventas:
            st.warning("Carga al menos una venta para ver el desglose.")
        else:
            total_lines = sum(v['Cant'] for v in st.session_state.mix_ventas)
            tier_idx, tier_label = FinancialEngine.get_tier_info(total_lines)
            
            st.subheader(f"Resumen de Desempeño: {tier_label}")
            
            # Detalle Técnico de Comisiones
            audit_data = []
            comision_total = 0
            for v in st.session_state.mix_ventas:
                mult = MULTIPLICADORES[v["Tipo"]][tier_idx] if tier_idx is not None else 0
                subtotal = v["ARPU Neto"] * mult * v["Cant"]
                comision_total += subtotal
                audit_data.append({
                    "Producto": v["Tipo"],
                    "Líneas": v["Cant"],
                    "ARPU Neto": f"${v['ARPU Neto']:,}",
                    "Mult.": f"x{mult}",
                    "Subtotal": f"${int(subtotal):,}"
                })
            
            st.table(pd.DataFrame(audit_data))
            
            # Tope Comisional
            if comision_total > 3500000:
                comision_total = 3500000
                st.warning("Se ha aplicado el Tope Comisional de $3.500.000 s/Anexo.")

            # Parámetros Legales
            st.divider()
            c1, c2, c3 = st.columns(3)
            habiles = c1.number_input("Días Hábiles Trabajados", value=21)
            festivos = c2.number_input("Domingos/Festivos", value=5)
            
            sc = (comision_total / habiles) * festivos if habiles > 0 else 0
            
            # Cálculo Final
            imponible = HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"] + comision_total + sc
            no_imponible = HABERES_FIJOS["Movilización"] + HABERES_FIJOS["Colación"] + HABERES_FIJOS["Ajuste Sencillo"]
            
            # Neto estimado (Factor 0.81 para AFP/Salud/Impuesto)
            liquido = (imponible * 0.81) + no_imponible

            st.metric("Total Líneas Mes", total_lines)
            st.metric("Comisión Proyectada", f"${int(comision_total):,}")
            st.metric("Semana Corrida", f"${int(sc):,}")
            
            st.markdown(f"""
            ### 💵 Renta Líquida Final Estimada: **${int(liquido):,}**
            ---
            **Explicación para Liquidación:**
            1. **Sueldo Base + Gratificación:** ${HABERES_FIJOS['Sueldo Base'] + HABERES_FIJOS['Gratificación Legal']:,} (Fijo)
            2. **Comisiones:** Acumulado de {total_lines} líneas en tramo {tier_label}.
            3. **Semana Corrida:** Proporcional a ${int(comision_total):,} de variable sobre {habiles} días.
            4. **Descuentos Legales:** Estimación de previsión e impuestos sobre imponible de ${int(imponible):,}.
            """)

if __name__ == "__main__":
    main()
