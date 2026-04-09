import streamlit as st
from streamlit_mic_recorder import mic_recorder
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
import os

# Configuración de la página
st.set_page_config(page_title="Technical Assessment AI", layout="centered")

# --- ESTILOS Y DATOS ---
INDICADORES = [
    "Nutrición en general", "Conocimiento de productos", "Nutrición aplicada", 
    "Sistemas de alimentación", "Manejo del agua", "Patología general", 
    "Patología metabólica", "Patología infecciosa y parasitaria", 
    "Anatomía patológica", "Técnicas diagnósticas", "Antibioterapia", 
    "Aditivos alternativos", "Bioseguridad", "Instalaciones", 
    "Manejo útiles diagnóstico", "Arranques", "Animales en producción", 
    "Reposición", "Sostenibilidad", "Recogida de datos", 
    "Tratamiento de datos", "Tratamiento de textos", "Informes", 
    "Inglés", "Manejo herramientas/programas"
]

CRITERIOS_TEXTO = """
0: Básico - Conocimiento limitado, sin capacidad de asesorar.
1: Controla - Capacidad de asesoramiento en granja.
2: Supera - Capacidad notable de asesoramiento de calidad.
3: Certificado - Obtiene certificación/acreditación específica.
4: Excelente - Asesoramiento sobresaliente. Referente en la materia.
5: Master - Capacidad de docencia en la materia (Universitario/Máster).
6: Máximo - Capacidad docente máxima y mejora continua (Referente total).
"""

# --- LÓGICA DE IA ---
def pensar_puntuacion(indicador, descripcion):
    if not descripcion:
        return None
    
    llm = ChatOpenAI(model="gpt-4o", temperature=0) # Requiere OPENAI_API_KEY en variables de entorno
    
    prompt_sistema = f"""
    Eres un experto en evaluación técnica. Tu objetivo es asignar una puntuación del 0 al 6 
    basándote en los siguientes criterios:
    {CRITERIOS_TEXTO}
    
    Analiza la descripción del usuario para el indicador '{indicador}' y devuelve:
    1. Puntuación (0-6).
    2. Breve razonamiento de por qué esa nota.
    """
    
    mensajes = [
        SystemMessage(content=prompt_sistema),
        HumanMessage(content=f"Descripción del evaluado: {descripcion}")
    ]
    
    respuesta = llm.invoke(mensajes)
    return respuesta.content

# --- INTERFAZ DE USUARIO ---
st.title("🚀 Asistente de Assessment Técnico")
st.markdown("Selecciona un indicador y describe tu experiencia (escribe o usa el micrófono).")

# Desplegable de Indicadores
indicador_sel = st.selectbox("Selecciona el indicador a evaluar:", INDICADORES)

st.divider()

# Sección de Entrada (Texto o Voz)
st.subheader("Descripción de capacidades")
col1, col2 = st.columns([3, 1])

with col2:
    st.write("¿Prefieres hablar?")
    audio = mic_recorder(start_prompt="🎤 Grabar voz", stop_prompt="🛑 Detener", key='recorder')

# Lógica para procesar el texto o la transcripción
# Nota: Para una app real de voz, necesitarías conectar el audio a Whisper de OpenAI
texto_usuario = st.text_area("Escribe aquí tus méritos o comentarios para este indicador:", 
                             height=150, 
                             placeholder="Ej: He liderado proyectos de bioseguridad y soy ponente en congresos...")

if audio:
    st.info("Audio capturado. (En producción, aquí conectaríamos con Whisper API para transcribir el audio a texto automáticamente).")

# Botón de Acción
if st.button("Calcular Puntuación Sugerida"):
    if texto_usuario:
        with st.spinner("La IA está analizando tus criterios..."):
            resultado = pensar_puntuacion(indicador_sel, texto_usuario)
            st.success("### Resultado del Análisis")
            st.write(resultado)
    else:
        st.warning("Por favor, introduce una descripción para poder evaluar.")

# Pie de página
st.sidebar.info("App configurada con los 25 indicadores del Technical Plan Career.")