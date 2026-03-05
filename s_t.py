import os
import streamlit as st
from bokeh.models import CustomJS, Button
from bokeh.layouts import row
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
from gtts import gTTS
from googletrans import Translator

# Configuración de página minimalista
st.set_page_config(page_title="Traductor Shiny", page_icon="🌐", layout="centered")

# --- Estilos minimalistas (CSS inyectado para mejorar el look) ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    div.stButton > button { border-radius: 8px; border: 1px solid #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# Encabezado estilo Notion
st.title("🌐 Traductor Shiny")
st.markdown("Tu herramienta de voz a texto y traducción inteligente.")
st.divider()

# Instrucciones en un Expander (limpio y compacto)
with st.expander("ℹ️ ¿Cómo usar este traductor?"):
    st.write("1. Presiona **Escuchar** para empezar a dictar.")
    st.write("2. Habla claro. El sistema detectará tu voz.")
    st.write("3. Presiona **Detener** cuando hayas terminado.")
    st.write("4. Configura tus idiomas y presiona 'Convertir'.")

# --- CONTENEDOR DE VOZ ---
with st.container(border=True):
    st.subheader("🎙️ Entrada de Voz")
    
    # Botones Bokeh
    stt_button = Button(label="Escuchar 🎤", width=150, height=50, button_type="success")
    stt_button.js_on_event("button_click", CustomJS(code="""
        window._rec = new webkitSpeechRecognition();
        window._rec.continuous = false;
        window._rec.interimResults = true;
        window._rec.lang = 'es-ES';
        window._rec.onresult = function (e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) { value += e.results[i][0].transcript; }
            }
            if (value != "") { document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value})); }
        }
        window._rec.start();
    """))

    stop_btn = Button(label="⏹️ Detener", width=150, height=50) 
    stop_btn.js_on_event("button_click", CustomJS(code="""
        try { if (window._rec) { window._rec.stop(); }
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: ""})); } 
        catch (err) { console.log(err); }
    """))

    layout = row(stt_button, stop_btn)
    result = streamlit_bokeh_events(layout, events="GET_TEXT", key="listen", refresh_on_update=False, override_height=70, debounce_time=0)

# --- LÓGICA DE TRADUCCIÓN ---
if result and "GET_TEXT" in result and result.get("GET_TEXT"):
    text = result.get("GET_TEXT")
    
    # Tarjeta de resultado de voz
    st.info(f"**Escuchado:** {text}")
    
    if not os.path.exists("temp"): os.mkdir("temp")
    
    st.subheader("⚙️ Configuración")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        langs = {"Inglés": "en", "Español": "es", "Bengali": "bn", "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja"}
        
        with col1:
            in_lang_name = st.selectbox("Idioma Entrada", list(langs.keys()), index=1)
            input_language = langs[in_lang_name]

        with col2:
            out_lang_name = st.selectbox("Idioma Salida", list(langs.keys()), index=0)
            output_language = langs[out_lang_name]

        accents = {"Defecto": "com", "Español": "com.mx", "Reino Unido": "co.uk", "EE.UU": "com", "Canadá": "ca", "Australia": "com.au"}
        english_accent = st.selectbox("Acento de voz", list(accents.keys()))
        tld = accents[english_accent]
        display_output_text = st.checkbox("Mostrar texto traducido", value=True)

    if st.button("🚀 Convertir y Traducir", type="primary"):
        with st.spinner("Traduciendo y generando audio..."):
            translator = Translator()
            translation = translator.translate(text, src=input_language, dest=output_language)
            trans_text = translation.text
            
            tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
            my_file_name = "audio_result"
            tts.save(f"temp/{my_file_name}.mp3")
            
            st.markdown("### ✨ Resultado")
            with open(f"temp/{my_file_name}.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3")
            
            if display_output_text:
                st.success(f"**Traducción:** {trans_text}")

# Limpieza
def remove_files(n):
    for f in glob.glob("temp/*mp3"):
        if os.stat(f).st_mtime < time.time() - (n * 86400): os.remove(f)

remove_files(7)
