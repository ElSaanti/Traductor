import os
import streamlit as st
from bokeh.models import CustomJS, Button
from bokeh.layouts import column  # Importante para mostrar ambos botones
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
from gtts import gTTS
from googletrans import Translator

# Configuración de la página
st.set_page_config(page_title="TRADUCTOR Shiny", layout="centered")

st.title("TRADUCTOR Shiny.")
st.subheader("Escucho lo que quieres traducir.")

# Imagen (Asegúrate de tener el archivo o comenta esta línea)
try:
    image = Image.open('traductor.jpg')
    st.image(image, width=300)
except:
    st.info("💡 Coloca una imagen llamada 'traductor.jpg' en la carpeta para verla aquí.")

with st.sidebar:
    st.subheader("Traductor.")
    st.write("Presiona el botón, cuando escuches la señal habla lo que quieres traducir.")

st.write("Toca el botón y habla lo que te gustaría traducir (excepto si tienes iPhone 🫠)")

# --- CONFIGURACIÓN DE BOTONES BOKEH ---

# Botón Iniciar
stt_button = Button(label="Escuchar 🎤", width=300, height=50, button_type="success")
stt_button.js_on_event("button_click", CustomJS(code="""
    window._rec = new webkitSpeechRecognition();
    window._rec.continuous = false;
    window._rec.interimResults = true;
    window._rec.lang = 'es-ES';

    window._rec.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    window._rec.start();
"""))

# Botón Detener
stop_btn = Button(label="⏹️ Detener", width=300, height=50, button_type="danger")
stop_btn.js_on_event("button_click", CustomJS(code="""
    try {
        if (window._rec) { 
            window._rec.stop(); 
        }
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: ""}));
    } catch (err) {
        console.log(err);
    }
"""))

# Agrupamos los botones en un diseño de columna
layout = column(stt_button, stop_btn)

# Renderizamos los eventos de Bokeh
result = streamlit_bokeh_events(
    layout,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=150, # Altura ajustada para dos botones
    debounce_time=0
)

# --- LÓGICA DE TRADUCCIÓN ---

if result and "GET_TEXT" in result:
    text = result.get("GET_TEXT")
    
    if text:
        st.info(f"Escuchado: {text}")
        
        if not os.path.exists("temp"):
            os.mkdir("temp")
            
        st.divider()
        st.subheader("Configuración de Traducción")
        
        col1, col2 = st.columns(2)
        
        with col1:
            langs = {"Inglés": "en", "Español": "es", "Bengali": "bn", "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja"}
            in_lang_name = st.selectbox("Idioma Entrada", list(langs.keys()), index=1)
            input_language = langs[in_lang_name]

        with col2:
            out_lang_name = st.selectbox("Idioma Salida", list(langs.keys()), index=0)
            output_language = langs[out_lang_name]

        accents = {
            "Defecto": "com", "Español": "com.mx", "Reino Unido": "co.uk", 
            "EE.UU": "com", "Canadá": "ca", "Australia": "com.au"
        }
        english_accent = st.selectbox("Selecciona el acento de voz", list(accents.keys()))
        tld = accents[english_accent]

        display_output_text = st.checkbox("Mostrar el texto traducido", value=True)

        if st.button("Convertir y Traducir"):
            translator = Translator()
            translation = translator.translate(text, src=input_language, dest=output_language)
            trans_text = translation.text
            
            # Generar Audio
            tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
            my_file_name = "audio_result"
            tts.save(f"temp/{my_file_name}.mp3")
            
            st.markdown("### Resultado:")
            with open(f"temp/{my_file_name}.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3")
            
            if display_output_text:
                st.success(f"Traducción: {trans_text}")

# Limpieza de archivos viejos
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    now = time.time()
    for f in mp3_files:
        if os.stat(f).st_mtime < now - (n * 86400):
            os.remove(f)

remove_files(7)
