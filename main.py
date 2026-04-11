import json
import re
from datetime import datetime

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Technical Assessment Assistant",
    page_icon="🧭",
    layout="wide",
)

# =========================================================
# CONFIGURACIÓN
# =========================================================

INDICATORS = {
    "ALIMENTACION": [
        "Nutrición en general",
        "Conocimiento de productos",
        "Nutrición aplicada",
        "Sistemas de alimentación",
        "Manejo del agua",
    ],
    "SANIDAD": [
        "Patología general",
        "Patología metabólica",
        "Patología infecciosa y parasitaria",
        "Anatomía patológica",
        "Técnicas diagnosticas",
        "Antibioterapia",
        "Aditivos alternativos",
    ],
    "MANEJO": [
        "Bioseguridad",
        "Instalaciones",
        "Manejo utiles diagnostico instalaciones",
        "Arranques",
        "Animales en producción",
        "Reposición",
        "Sostenibilidad",
    ],
    "HERRAMIENTAS": [
        "Recogida de datos",
        "Tratamiento de datos",
        "Tratamiento de textos",
        "Informes",
        "Ingles",
        "Manejo herramientas/programas",
    ],
}

INDICATOR_LIST = [
    f"{area} · {item}"
    for area, items in INDICATORS.items()
    for item in items
]

# Escala del anexo:
# 0 Básico | 1 Controla | 2 Supera | 3 Certificado | 4 Excelente | 5 Master | 6 Máximo
LEVELS = {
    0: {
        "name": "BÁSICO",
        "short": "Entrada en la compañía. Minuto cero.",
        "signals": [
            "inicio", "recién incorporado", "sin experiencia", "aprendiendo", "base",
            "junior", "acompañado", "primeras visitas", "nivel inicial", "minuto cero"
        ],
    },
    1: {
        "name": "CONTROLA",
        "short": "Asesoramiento con garantías. Conoce productos, manejo, nutrición y sanidad. Genera confianza.",
        "signals": [
            "realiza visitas por su cuenta", "autonomía", "autonomia", "diagnostica",
            "interpreta datos", "aconseja", "manejo", "sanidad", "explica productos",
            "argumenta productos", "gana confianza", "forma al personal",
            "asesoramiento con garantías", "asesoramiento con garantias"
        ],
    },
    2: {
        "name": "SUPERA",
        "short": "Asesoramiento de alta calidad. Aporta consejos valiosos, planes de mejora y reconocimiento.",
        "signals": [
            "plan de mejora", "mejora continua", "asesoramiento de calidad", "reconocimiento",
            "desarrollo de explotación", "desarrollo de explotacion",
            "formación especializada", "formacion especializada",
            "consejos valiosos", "asesoramiento de alta calidad"
        ],
    },
    3: {
        "name": "CERTIFICADO",
        "short": "Como el nivel anterior, con acreditación o certificación obtenida.",
        "signals": [
            "certificación", "certificacion", "certificado", "acreditación",
            "acreditacion", "acreditado", "titulado", "curso certificado",
            "nivel acreditado"
        ],
    },
    4: {
        "name": "EXCELENTE",
        "short": "Asesoramiento reconocido de alto valor. Especialización, proyectos, publicaciones y liderazgo.",
        "signals": [
            "alto valor", "referente", "reconocido en el sector",
            "proyecto de investigación", "proyecto de investigacion",
            "publicaciones", "liderazgo", "alta especialización",
            "alta especializacion", "ponente", "proyecto de calado"
        ],
    },
    5: {
        "name": "MASTER",
        "short": "Sobresaliente. Docencia universitaria o posgrado, publicaciones científicas y reconocimiento acreditado.",
        "signals": [
            "docencia universitaria", "máster", "master", "posgrado",
            "publicaciones científicas", "publicaciones cientificas",
            "comité científico", "comite cientifico", "docente", "universitario"
        ],
    },
    6: {
        "name": "MÁXIMO",
        "short": "Reconocimiento y capacidad docente de máxima referencia. Nivel abierto y excepcional.",
        "signals": [
            "máximo", "maximo", "referencia absoluta", "trayectoria excepcional",
            "muy alto reconocimiento", "referente nacional",
            "referente internacional", "excelencia sostenida"
        ],
    },
}

LEVEL_HINTS = {
    0: ["entrada", "cero", "inicial", "base", "aprende"],
    1: ["autonomia", "visitas", "diagnostica", "interpreta", "explica productos", "confianza"],
    2: ["planes de mejora", "alta calidad", "reconocimiento", "especializada"],
    3: ["certificacion", "acreditacion"],
    4: ["publicaciones", "investigacion", "liderazgo", "alto valor", "sector"],
    5: ["universidad", "posgrado", "comite cientifico", "cientificas"],
    6: ["maximo", "excepcional", "referencia absoluta"],
}

INDICATOR_KEYWORDS = {
    "Nutrición en general": ["ración", "nutrición", "nutricion", "balance", "necesidades", "formulación", "formulacion"],
    "Conocimiento de productos": ["producto", "portfolio", "aditivo", "argumenta", "recomienda"],
    "Nutrición aplicada": ["aplicación", "aplicacion", "ajusta", "caso práctico", "caso practico", "objetivo productivo"],
    "Sistemas de alimentación": ["sistema de alimentación", "sistema de alimentacion", "comedero", "mezcla", "distribución", "distribucion"],
    "Manejo del agua": ["agua", "caudal", "calidad del agua", "consumo de agua"],
    "Patología general": ["patología", "patologia", "diagnóstico diferencial", "diagnostico diferencial", "signos clínicos", "signos clinicos"],
    "Patología metabólica": ["metabólica", "metabolica", "cetosis", "acidosis", "hipocalcemia"],
    "Patología infecciosa y parasitaria": ["infecciosa", "parasitaria", "agente", "parásito", "parasito", "infección", "infeccion"],
    "Anatomía patológica": ["lesión", "lesion", "necropsia", "hallazgo", "anatomía patológica", "anatomia patologica"],
    "Técnicas diagnosticas": ["muestra", "laboratorio", "pcr", "serología", "serologia", "diagnóstico", "diagnostico"],
    "Antibioterapia": ["antibiótico", "antibiotico", "antibioterapia", "antibiograma", "tratamiento"],
    "Aditivos alternativos": ["aditivo alternativo", "probiótico", "probiotico", "prebiótico", "prebiotico", "fitogénico", "fitogenico"],
    "Bioseguridad": ["bioseguridad", "protocolo", "riesgo", "entrada", "limpieza"],
    "Instalaciones": ["instalación", "instalacion", "ventilación", "ventilacion", "diseño", "diseno", "densidad", "equipamiento"],
    "Manejo utiles diagnostico instalaciones": ["checklist", "auditoría", "auditoria", "medición", "medicion", "instrumento"],
    "Arranques": ["arranque", "inicio", "transición", "transicion", "primeros días", "primeros dias"],
    "Animales en producción": ["producción", "produccion", "rendimiento", "lote", "fase productiva"],
    "Reposición": ["reposición", "reposicion", "recría", "recria", "futuras reproductoras", "desarrollo"],
    "Sostenibilidad": ["sostenibilidad", "huella", "eficiencia", "impacto ambiental"],
    "Recogida de datos": ["datos", "toma de datos", "recogida", "registro"],
    "Tratamiento de datos": ["análisis", "analisis", "tabla", "power bi", "estadística", "estadistica", "indicador"],
    "Tratamiento de textos": ["texto", "redacción", "redaccion", "síntesis", "sintesis", "documentación", "documentacion"],
    "Informes": ["informe", "conclusión", "conclusion", "recomendación", "recomendacion", "presentación", "presentacion"],
    "Ingles": ["english", "inglés", "ingles", "meeting", "paper", "presentation"],
    "Manejo herramientas/programas": ["excel", "power bi", "software", "programa", "herramienta"],
}

QUESTION_GUIDE = [
    {
        "Pregunta": "¿Qué haces tú solo en este tema, sin ayuda?",
        "Objetivo": "Medir autonomía real y nivel operativo.",
    },
    {
        "Pregunta": "Cuéntame un caso reciente y concreto en el que lo hayas aplicado.",
        "Objetivo": "Confirmar aplicación práctica, no solo conocimiento teórico.",
    },
    {
        "Pregunta": "¿Qué decisión o recomendación diste tú en ese caso?",
        "Objetivo": "Valorar capacidad de análisis y criterio técnico.",
    },
    {
        "Pregunta": "¿Qué resultado, mejora o impacto tuvo tu intervención?",
        "Objetivo": "Detectar si aporta valor real y mejora observable.",
    },
    {
        "Pregunta": "¿Tienes formación específica, certificación o reconocimiento en este ámbito?",
        "Objetivo": "Diferenciar niveles altos y evidencias formales.",
    },
]

# =========================================================
# UTILIDADES
# =========================================================

def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    replacements = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ü": "u", "ñ": "n",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = re.sub(r"\s+", " ", text)
    return text


def score_level(description: str, indicator: str) -> dict:
    text = normalize_text(description)
    indicator_name = indicator.split(" · ", 1)[1] if " · " in indicator else indicator

    if not text:
        return {
            "score": 0,
            "name": LEVELS[0]["name"],
            "reason": "Sin descripción suficiente. Se propone el nivel más conservador.",
            "matched": [],
        }

    raw_scores = {level: 0 for level in LEVELS}
    matched = {level: [] for level in LEVELS}

    # 1) Señales explícitas del nivel
    for level, meta in LEVELS.items():
        for signal in meta["signals"]:
            sig_n = normalize_text(signal)
            if sig_n in text:
                raw_scores[level] += 3
                matched[level].append(signal)

    # 2) Pistas generales
    for level, hints in LEVEL_HINTS.items():
        for hint in hints:
            hint_n = normalize_text(hint)
            if hint_n in text:
                raw_scores[level] += 2
                matched[level].append(hint)

    # 3) Alineación con el indicador concreto
    keywords = INDICATOR_KEYWORDS.get(indicator_name, [])
    keyword_hits = [kw for kw in keywords if normalize_text(kw) in text]
    if keyword_hits:
        raw_scores[1] += 1
        raw_scores[2] += 1

    # 4) Reglas de refuerzo
    if any(x in text for x in ["certificacion", "certificado", "acreditacion", "acreditado"]):
        raw_scores[3] += 4

    if any(x in text for x in ["publicacion", "publicaciones", "investigacion", "liderazgo", "referente"]):
        raw_scores[4] += 4

    if any(x in text for x in ["universidad", "universitario", "posgrado", "master", "comite cientifico", "docencia"]):
        raw_scores[5] += 5

    if any(x in text for x in ["maximo", "referente nacional", "referente internacional", "trayectoria excepcional"]):
        raw_scores[6] += 5

    practical_count = sum(
        1 for x in [
            "autonomia", "visitas", "diagnostica", "interpreta", "aconseja",
            "manejo", "sanidad", "productos", "datos", "informes",
            "ingles", "programas"
        ] if x in text
    )
    if practical_count >= 2:
        raw_scores[1] += 2
    if practical_count >= 4:
        raw_scores[2] += 2

    # 5) Selección inicial
    best_level = max(raw_scores, key=lambda x: raw_scores[x])

    # 6) Fallback conservador
    if raw_scores[best_level] == 0:
        word_count = len(text.split())
        if word_count < 12:
            best_level = 0
        elif word_count < 25:
            best_level = 1
        else:
            best_level = 2

    # 7) Barreras lógicas
    if best_level >= 4 and raw_scores[4] == 0 and raw_scores[5] == 0 and raw_scores[6] == 0:
        best_level = 3 if raw_scores[3] > 0 else 2
    if best_level == 3 and raw_scores[3] == 0:
        best_level = 2
    if best_level == 5 and raw_scores[5] == 0:
        best_level = 4
    if best_level == 6 and raw_scores[6] == 0:
        best_level = 5

    matches = sorted(set(matched[best_level]))
    fragments = []

    if matches:
        fragments.append(f"evidencias de nivel: {', '.join(matches[:6])}")
    if keyword_hits:
        fragments.append(f"alineación con el indicador: {', '.join(keyword_hits[:5])}")

    if fragments:
        reason = (
            f"Se propone {best_level} · {LEVELS[best_level]['name']} porque el texto aporta "
            + " | ".join(fragments)
            + "."
        )
    else:
        reason = f"Se propone {best_level} · {LEVELS[best_level]['name']} por ajuste global del contenido a los criterios de la escala."

    return {
        "score": best_level,
        "name": LEVELS[best_level]["name"],
        "reason": reason,
        "matched": matches,
    }


def initialize_state() -> None:
    if "results" not in st.session_state:
        st.session_state.results = {
            indicator: {
                "area": indicator.split(" · ")[0],
                "indicator": indicator.split(" · ")[1],
                "description": "",
                "score": None,
                "name": "",
                "reason": "",
                "updated_at": "",
            }
            for indicator in INDICATOR_LIST
        }


def build_export_block() -> str:
    ordered_scores = []
    for indicator in INDICATOR_LIST:
        value = st.session_state.results[indicator]["score"]
        ordered_scores.append("" if value is None else str(value))
    return "\t".join(ordered_scores)


def results_dataframe() -> pd.DataFrame:
    rows = []
    for indicator in INDICATOR_LIST:
        item = st.session_state.results[indicator]
        rows.append(
            {
                "Área": item["area"],
                "Indicador": item["indicator"],
                "Puntuación": item["score"],
                "Nivel": item["name"],
                "Última actualización": item["updated_at"],
            }
        )
    return pd.DataFrame(rows)


# =========================================================
# APP
# =========================================================

initialize_state()

st.title("Technical Assessment Assistant")
st.caption(
    "Evaluación rápida de 25 indicadores con propuesta automática de nivel 0–6 y bloque final listo para copiar/pegar."
)

with st.expander("Ver escala de puntuación", expanded=False):
    for level, meta in LEVELS.items():
        st.markdown(f"**{level} · {meta['name']}** — {meta['short']}")

left, right = st.columns([1.15, 1])

with left:
    st.subheader("1) Evaluar un indicador")

    selected_indicator = st.selectbox(
        "Indicador",
        INDICATOR_LIST,
        index=0,
        help="Selecciona uno de los 25 indicadores.",
    )

    current_data = st.session_state.results[selected_indicator]

    with st.expander("Guía rápida para entrevistar al técnico", expanded=False):
        st.table(pd.DataFrame(QUESTION_GUIDE))
        st.caption(
            "Resume la evidencia en este orden: autonomía + caso real + decisión + resultado + acreditación/reconocimiento."
        )

    st.info(
        "Consejo: en Windows, coloca el cursor dentro del cuadro de texto y pulsa Windows + H para dictar por voz."
    )

    st.markdown("**Descripción de evidencia**")
    description = st.text_area(
        "Describe lo observado",
        value=current_data["description"],
        height=240,
        placeholder=(
            "Ejemplo:\n"
            "- Qué hace solo y con qué autonomía\n"
            "- Caso reciente y concreto\n"
            "- Decisión o recomendación que dio\n"
            "- Resultado o impacto\n"
            "- Formación, certificación o reconocimiento"
        ),
        label_visibility="collapsed",
    )

    c1, c2, c3 = st.columns([1, 1, 1.2])
    with c1:
        evaluate = st.button("Proponer puntuación", use_container_width=True)
    with c2:
        clear_current = st.button("Limpiar indicador", use_container_width=True)
    with c3:
        save_manual = st.button("Guardar sin evaluar", use_container_width=True)

    if clear_current:
        st.session_state.results[selected_indicator].update(
            {
                "description": "",
                "score": None,
                "name": "",
                "reason": "",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        st.rerun()

    if save_manual:
        st.session_state.results[selected_indicator]["description"] = description
        st.session_state.results[selected_indicator]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        st.success("Descripción guardada.")

    if evaluate:
        proposal = score_level(description, selected_indicator)
        st.session_state.results[selected_indicator].update(
            {
                "description": description,
                "score": proposal["score"],
                "name": proposal["name"],
                "reason": proposal["reason"],
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        st.rerun()

with right:
    st.subheader("2) Resultado propuesto")
    current_data = st.session_state.results[selected_indicator]

    if current_data["score"] is not None:
        st.metric(
            label="Calificación",
            value=f"{current_data['score']} · {current_data['name']}",
        )
        st.info(current_data["reason"])
    else:
        st.warning("Todavía no hay puntuación propuesta para este indicador.")

    st.subheader("3) Ajuste manual rápido")
    manual_score = st.select_slider(
        "Corrige si lo necesitas",
        options=list(LEVELS.keys()),
        value=current_data["score"] if current_data["score"] is not None else 0,
        format_func=lambda x: f"{x} · {LEVELS[x]['name']}",
    )

    if st.button("Aplicar ajuste manual", use_container_width=True):
        st.session_state.results[selected_indicator].update(
            {
                "description": description,
                "score": manual_score,
                "name": LEVELS[manual_score]["name"],
                "reason": f"Ajuste manual aplicado por el evaluador. Nivel final: {manual_score} · {LEVELS[manual_score]['name']}.",
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        st.success("Ajuste manual guardado.")

st.divider()

st.subheader("4) Resumen de los 25 indicadores")
df = results_dataframe()
st.dataframe(df, use_container_width=True, hide_index=True)

completed = int(df["Puntuación"].notna().sum())
st.progress(completed / len(INDICATOR_LIST), text=f"Indicadores evaluados: {completed}/{len(INDICATOR_LIST)}")

st.subheader("5) Bloque final para copiar y pegar")
export_block = build_export_block()
st.text_area(
    "Valores en el orden exacto de los 25 indicadores",
    value=export_block,
    height=100,
    help="Se exporta en una sola línea, separado por tabuladores, para facilitar el pegado en la herramienta Technical Plan Career.",
)

col_a, col_b, col_c = st.columns([1, 1, 1.2])

with col_a:
    st.download_button(
        "Descargar CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="technical_assessment_results.csv",
        mime="text/csv",
        use_container_width=True,
    )

with col_b:
    json_data = json.dumps(st.session_state.results, ensure_ascii=False, indent=2)
    st.download_button(
        "Descargar JSON",
        data=json_data.encode("utf-8"),
        file_name="technical_assessment_results.json",
        mime="application/json",
        use_container_width=True,
    )

with col_c:
    if st.button("Reiniciar toda la evaluación", use_container_width=True):
        del st.session_state["results"]
        initialize_state()
        st.rerun()

with st.expander("Orden de exportación de los 25 indicadores", expanded=False):
    for idx, indicator in enumerate(INDICATOR_LIST, start=1):
        st.write(f"{idx:02d}. {indicator}")
