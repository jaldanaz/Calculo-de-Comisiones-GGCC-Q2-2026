import streamlit as st
import pandas as pd

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

# Tipos de venta alineados al Anexo Comisional
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
    def get_arpu_details(tipo, plan, cant, is_manual=False, manual_arpu=0):
        """Calcula el ARPU determinando si es automático o una excepción manual."""
        if is_manual:
            ahorro = 1 - (manual_arpu / plan) if plan > 0 else 0
            return manual_arpu, f"{int(ahorro*100)}% (Manual/Exc.)"
            
        # Lógica Automática (Oferta Táctica 2026)
        if "Porta" in tipo and "Prepago" not in tipo and cant >= 2:
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
    st.set_page_config(page_title="WOM Financial Audit Pro", layout="wide")
    
    if 'mix_ventas' not in st.session_state:
        st.session_state.mix_ventas = []

    st.title("📈 Control de Ingresos y Mix de Ventas")
    st.info("Soporta Carga Táctica Automatizada y Excepciones Comerciales Manuales.")

    tab_carga, tab_auditoria = st.tabs(["📥 Cargar Ventas", "🔍 Desglose de Ingresos"])

    with tab_carga:
        col_f, col_v = st.columns([1, 2.2])
        with col_f:
            with st.form("nueva_venta", clear_on_submit=True):
                st.subheader("Configuración de Venta")
                cliente = st.text_input("Cliente / Proyecto")
                tipo = st.selectbox("Tipo de Línea", list(MULTIPLICADORES.keys()))
                plan = st.selectbox("Plan Comercial", [12990, 15990, 18990, 23990])
                cant = st.number_input("Cantidad de Líneas", min_value=1, step=1)
                
                st.divider()
                st.markdown("#### ⚙️ Excepciones y Equipos")
                
                # Checkbox para activar sobreescritura manual
                is_manual = st.checkbox("Aplicar Descuento Especial (Sobreescribir Matriz)")
                manual_arpu = 0
                if is_manual:
                    manual_arpu = st.number_input(
                        "Ingresar ARPU Neto Final ($)", 
                        min_value=0, 
                        value=plan,
                        help="Ingresa el valor exacto del plan tras aplicar el descuento especial autorizado."
                    )
                
                # Dinámico: Solo mostrar si el tipo incluye "Equipo"
                cuota_equipo = 0
                if "Equipo" in tipo:
                    cuota_equipo = st.number_input(
                        "Cuota Mensual de Arriendo Equipo ($)", 
                        min_value=0, 
                        value=0,
                        help="Ingresa el valor de la cuota. Útil para modelos de nueva inclusión sin tabla."
                    )
                
                if st.form_submit_button("Confirmar y Sumar al Mix"):
                    # Procesar ARPU (Automático vs Manual)
                    arpu, desc_label = FinancialEngine.get_arpu_details(tipo, plan, cant, is_manual, manual_arpu)
                    
                    st.session_state.mix_ventas.append({
                        "Cliente": cliente if cliente else "N/A",
                        "Tipo": tipo,
                        "Plan Base": plan,
                        "Cant": cant,
                        "ARPU Neto": arpu,
                        "Desc. Aplicado": desc_label,
                        "Cuota Equipo": cuota_equipo
                    })
                    st.success("Venta procesada y agregada con éxito.")

        with col_v:
            st.subheader("Estado Actual del Mes")
            if st.session_state.mix_ventas:
                df = pd.DataFrame(st.session_state.mix_ventas)
                # Formateo visual rápido para la tabla
                df_visual = df.copy()
                df_visual["Plan Base"] = df_visual["Plan Base"].apply(lambda x: f"${x:,}")
                df_visual["ARPU Neto"] = df_visual["ARPU Neto"].apply(lambda x: f"${int(x):,}")
                df_visual["Cuota Equipo"] = df_visual["Cuota Equipo"].apply(lambda x: f"${int(x):,}")
                
                st.dataframe(df_visual, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Descargar Reporte (CSV)", data=csv, file_name="mix_ventas_wom.csv", mime="text/csv")
                
                if st.button("🗑️ Limpiar Mes Completo"):
                    st.session_state.mix_ventas = []
                    st.rerun()
            else:
                st.write("El embudo está vacío. Comienza a cargar ventas a la izquierda.")

    with tab_auditoria:
        if not st.session_state.mix_ventas:
            st.warning("Carga al menos una venta para calcular el desglose.")
        else:
            total_lines = sum(v['Cant'] for v in st.session_state.mix_ventas)
            tier_idx, tier_label = FinancialEngine.get_tier_info(total_lines)
            
            st.subheader(f"Auditoría de Desempeño: {tier_label}")
            
            audit_data = []
            comision_total = 0
            
            for v in st.session_state.mix_ventas:
                mult = MULTIPLICADORES[v["Tipo"]][tier_idx] if tier_idx is not None else 0
                # La comisión se calcula sobre el ARPU Neto (el plan con el descuento aplicado)
                subtotal = v["ARPU Neto"] * mult * v["Cant"]
                comision_total += subtotal
                
                audit_data.append({
                    "Producto": v["Tipo"],
                    "Líneas": v["Cant"],
                    "ARPU (Comisionable)": f"${int(v['ARPU Neto']):,}",
                    "Cuota Equipo": f"${int(v['Cuota Equipo']):,}",
                    "Tasa / Mult": f"x{mult}",
                    "Comisión Generada": f"${int(subtotal):,}"
                })
            
            st.table(pd.DataFrame(audit_data))
            
            if comision_total > 3500000:
                comision_total = 3500000
                st.warning("Tope Comisional Aplicado: $3.500.000")

            st.divider()
            c1, c2, c3 = st.columns(3)
            habiles = c1.number_input("Días Hábiles", value=21)
            festivos = c2.number_input("Festivos", value=5)
            
            sc = (comision_total / habiles) * festivos if habiles > 0 else 0
            
            imponible = HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"] + comision_total + sc
            no_imponible = HABERES_FIJOS["Movilización"] + HABERES_FIJOS["Colación"] + HABERES_FIJOS["Ajuste Sencillo"]
            liquido = (imponible * 0.81) + no_imponible

            st.metric("Total Líneas Escrutadas", total_lines)
            st.metric("Comisión Proyectada", f"${int(comision_total):,}")
            st.metric("Semana Corrida", f"${int(sc):,}")
            
            st.success(f"### 💵 Renta Líquida Estimada: **${int(liquido):,}**")

if __name__ == "__main__":
    main()
