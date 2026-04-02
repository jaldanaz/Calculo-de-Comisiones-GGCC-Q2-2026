import streamlit as st
import pandas as pd

# ==========================================
# 1. CONSTANTES (Sueldo y Multiplicadores)
# ==========================================
HABERES_FIJOS = {
    "Sueldo Base": 633513,
    "Gratificación Legal": 178694,
    "Movilización": 63847,
    "Colación": 53372,
    "Ajuste Sencillo": 104
}

PLANES_OFICIALES = [12990, 15990, 18990, 23990]

# Multiplicadores según Anexo
MULTIPLICADORES = {
    "BAM / Nueva / Porta Prepago": [2.0, 2.3, 2.7],
    "Portabilidad Postpago": [2.8, 3.1, 3.4],
    "Voz s/Porta + Equipo": [2.9, 3.2, 3.5],
    "Porta + Equipo": [3.1, 3.4, 3.7]
}

# ==========================================
# 2. MOTOR DE CÁLCULO (Lógica de Negocio)
# ==========================================
class SalesEngine:
    @staticmethod
    def calculate_arpu(plan_base, dcto_porcentaje):
        """Calcula el valor comisionable final basado en el % de descuento."""
        return plan_base * (1 - (dcto_porcentaje / 100))

    @staticmethod
    def get_tier_index(total_lines):
        """Determina el tramo de comisión."""
        if total_lines < 30: return None
        if total_lines <= 110: return 0
        if total_lines <= 225: return 1
        return 2

# ==========================================
# 3. INTERFAZ DE USUARIO (UX)
# ==========================================
def main():
    st.set_page_config(page_title="WOM Sales Tracker - Jorge Aldana", layout="wide")
    
    if 'ventas_mes' not in st.session_state:
        st.session_state.ventas_mes = []

    st.title("💼 Calculadora de Comisiones de Venta")
    st.caption("Enfoque: Descuentos Comerciales y Cuotas de Arriendo Manuales")

    tab_input, tab_resumen = st.tabs(["➕ Registrar Venta", "📊 Resumen Mensual"])

    with tab_input:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            with st.form("form_registro", clear_on_submit=True):
                st.subheader("Datos del Negocio")
                cliente = st.text_input("Nombre Cliente / ID Negocio")
                tipo = st.selectbox("Tipo de Venta", list(MULTIPLICADORES.keys()))
                plan = st.selectbox("Plan Comercial Base", PLANES_OFICIALES, format_func=lambda x: f"${x:,}")
                cant = st.number_input("Cantidad de Líneas", min_value=1, step=1)
                
                st.divider()
                st.subheader("Condiciones de Cierre")
                
                # Entrada por % de descuento (lo que el vendedor recuerda)
                dcto = st.slider("% Descuento aplicado al Plan", 0, 100, 0, step=5)
                
                # Cuota de equipo manual (para modelos nuevos/especiales)
                cuota_equipo = 0
                if "Equipo" in tipo:
                    cuota_equipo = st.number_input("Cuota Arriendo Equipo Mensual ($)", min_value=0, value=0)

                if st.form_submit_button("Cargar al Mix Mensual"):
                    arpu_final = SalesEngine.calculate_arpu(plan, dcto)
                    st.session_state.ventas_mes.append({
                        "Cliente": cliente if cliente else "Sin Nombre",
                        "Tipo": tipo,
                        "Plan": plan,
                        "Dcto %": f"{dcto}%",
                        "ARPU Neto": arpu_final,
                        "Cant": cant,
                        "Cuota Equipo": cuota_equipo
                    })
                    st.toast(f"Venta de {cant} líneas cargada exitosamente")

    with tab_resumen:
        if not st.session_state.ventas_mes:
            st.warning("No hay ventas registradas este mes.")
        else:
            df = pd.DataFrame(st.session_state.ventas_mes)
            total_lineas = df["Cant"].sum()
            idx = SalesEngine.get_tier_index(total_lineas)
            
            # Mostrar Tabla de Control
            st.subheader("Detalle del Mix de Ventas")
            st.table(df[["Cliente", "Tipo", "Cant", "Plan", "Dcto %", "ARPU Neto", "Cuota Equipo"]])

            # Cálculos de Comisiones
            comision_total = 0
            if idx is not None:
                for v in st.session_state.ventas_mes:
                    m = MULTIPLICADORES[v["Tipo"]][idx]
                    comision_total += (v["ARPU Neto"] * m * v["Cant"])
                
                comision_total = min(comision_total, 3500000) # Tope legal
            
            # --- SECCIÓN DE LIQUIDACIÓN ---
            st.divider()
            c_calc1, c_calc2 = st.columns(2)
            
            with c_calc1:
                st.subheader("Haberes del Mes")
                d_h = st.number_input("Días Hábiles", value=21)
                d_f = st.number_input("Dom/Festivos", value=5)
                sc = (comision_total / d_h) * d_f if d_h > 0 else 0
                
                st.metric("Comisión de Ventas", f"${int(comision_total):,}")
                st.metric("Semana Corrida", f"${int(sc):,}")

            with c_calc2:
                st.subheader("Proyección Sueldo Líquido")
                imponible = HABERES_FIJOS["Sueldo Base"] + HABERES_FIJOS["Gratificación Legal"] + comision_total + sc
                no_imponible = sum([HABERES_FIJOS["Movilización"], HABERES_FIJOS["Colación"], HABERES_FIJOS["Ajuste Sencillo"]])
                
                # Cálculo neto simplificado (descuentos legales aprox 19%)
                liquido = (imponible * 0.81) + no_imponible
                
                st.success(f"## ESTIMADO LÍQUIDO: ${int(liquido):,}")
                st.caption(f"Basado en un total de {total_lineas} líneas (Tramo {idx+1 if idx is not None else 'N/A'})")

            # Botón de descarga
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📩 Exportar Reporte para Jefatura", data=csv, file_name="mix_ventas.csv")
            
            if st.button("🗑️ Borrar Datos del Mes"):
                st.session_state.ventas_mes = []
                st.rerun()

if __name__ == "__main__":
    main()
