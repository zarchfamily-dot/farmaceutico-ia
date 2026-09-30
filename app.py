import os
from PIL import Image
import google.generativeai as genai
import requests
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Agente IA Vademécum con API Oficial", page_icon="💊", layout="centered"
)

st.title("💊 Asistente Inteligente de Medicamentos (ADALID ZARATE CHOQUEHUANCA)")
st.write(
    "Sube una foto de un medicamento o escribe su nombre. El agente consultará"
    " la API oficial pública para extraer datos precisos."
)

# Configura tu Google AI Studio API Key
api_key = st.text_input("Ingresa tu Google AI Studio API Key:", type="password")


def buscar_medicamento_cima(nombre_o_principio):
  """Consulta la API pública de CIMA (AEMPS) para obtener datos reales del medicamento."""
  url = f"https://cima.aemps.es/cima/rest/medicamentos?nombre={nombre_o_principio}"
  try:
    response = requests.get(url, timeout=10)
    if response.status_code == 200:
      data = response.json()
      resultados = data.get("resultados", [])
      if resultados:
        info_resumen = []
        for med in resultados[:2]:
          nombre = med.get("nombre", "Desconocido")
          lab = med.get("labtitular", "Desconocido")
          nregistro = med.get("nregistro", "")
          p_activos = ", ".join(
              [p.get("nombre", "") for p in med.get("pactivos", [])]
          )
          info_resumen.append(
              f"- Nombre: {nombre} | Principio Activo: {p_activos} | Laboratorio:"
              f" {lab} | N° Registro: {nregistro}"
          )
        return "\n".join(info_resumen)
  except Exception as e:
    return f"No se pudo conectar a la API externa: {e}"
  return "No se encontraron registros oficiales exactos en la base de datos pública."


if api_key:
  genai.configure(api_key=api_key)

  # 👉 MODELO ACTUALIZADO AQUÍ PARA EVITAR EL ERROR 404
  model = genai.GenerativeModel("gemini-3-flash")

  input_type = st.radio(
      "¿Cómo deseas ingresar el medicamento?", ("Escribir nombre", "Subir imagen")
  )

  medicamento_input = None
  imagen_cargada = None

  if input_type == "Escribir nombre":
    medicamento_input = st.text_input(
        "Nombre del medicamento (ej. Ibuprofeno, Paracetamol):"
    )
  else:
    imagen_archivo = st.file_uploader(
        "Sube la foto de la caja o etiqueta", type=["jpg", "jpeg", "png"]
    )
    if imagen_archivo:
      imagen_cargada = Image.open(imagen_archivo)
      st.image(
          imagen_cargada,
          caption="Imagen del medicamento",
          use_container_width=True,
      )

  if st.button("Consultar y Analizar"):
    if not medicamento_input and not imagen_cargada:
      st.warning(
          "Por favor, escribe el nombre o sube una imagen del medicamento."
      )
    else:
      with st.spinner(
          "Extrayendo información y consultando API oficial de Vademécum..."
      ):

        nombre_extraido = medicamento_input
        if imagen_cargada:
          prompt_extraccion = (
              "Analiza esta imagen y extrae únicamente el nombre comercial o"
              " principio activo principal del medicamento que aparece escrito"
              " en la caja o envase. Responde solo con el nombre."
          )
          res_vision = model.generate_content([prompt_extraccion, imagen_cargada])
          nombre_extraido = res_vision.text.strip()
          st.info(
              f"🔍 Texto/Medicamento detectado por visión artificial:"
              f" *{nombre_extraido}*"
          )

        datos_oficiales = "No se consultó API externa."
        if nombre_extraido:
          datos_oficiales = buscar_medicamento_cima(nombre_extraido)

        prompt_final = f"""
                Eres un asistente farmacéutico virtual experto y riguroso.
                
                Datos oficiales obtenidos del Vademécum Público (CIMA AEMPS):
                {datos_oficiales}
                
                Con base en estos datos oficiales y en tu conocimiento médico general, elabora un informe estructurado estrictamente con los siguientes apartados para el usuario:
                1. **Principio Activo y Nombre Comercial:**
                2. **Indicaciones Principales:**
                3. **Dosis Habitual Orientativa:** (Aclara que depende de la prescripción médica).
                4. **Contraindicaciones y Advertencias:**
                5. **⚠️ Aviso Médico de Seguridad:** "Esta información es meramente orientativa obtenida de registros públicos. No sustituye la consulta con un médico o farmacéutico."
                """

        try:
          if imagen_cargada:
            response = model.generate_content([prompt_final, imagen_cargada])
          else:
            response = model.generate_content(
                [prompt_final, f"Consulta sobre: {medicamento_input}"]
            )

          st.markdown("### 📋 Resultados del Agente Inteligente:")
          st.markdown(response.text)

          with st.expander("Ver datos brutos de la API Pública consultada"):
            st.text(datos_oficiales)

        except Exception as e:
          st.error(f"Ocurrió un error al procesar el agente: {e}")
else:
  st.info(
      "Por favor ingresa tu API Key de Google AI Studio para activar el agente."
  )
