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


st.write("# 🎙️ Traductor Shiny")

# --- SECCIÓN: CÓMO USAR (CON IMAGEN INTERNA) ---
with st.expander("📖 Guía de uso rápido", expanded=True):
    col_text, col_img = st.columns([2, 1])
    with col_text:
        st.markdown("""
        **Pasos para traducir:**
        1. Haz clic en **Escuchar**.
        2. Di tu frase claramente.
        3. El sistema detectará el texto automáticamente.
        4. Configura los idiomas y dale a **Generar**.
        """)
    with col_img:
        try:
            image = Image.open('traductor.jpg')
            st.image(image, use_container_width=True)
        except:
            st.warning("Imagen no encontrada")

st.write("---")

# --- ÁREA DE CAPTURA DE VOZ ---
st.markdown("### Presiona el boton y habla")


# Botones Bokeh
stt_button = Button(label="Escuchar 🎤", width=150, height=45, button_type="primary")
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
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    window._rec.start();
"""))

stop_btn = Button(label="Detener ⏹️", width=150, height=45) 
stop_btn.js_on_event("button_click", CustomJS(code="""
    try {
        if (window._rec) { window._rec.stop(); }
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: ""}));
    } catch (err) { console.log(err); }
"""))

layout = row(stt_button, stop_btn)

result = streamlit_bokeh_events(
    layout,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# --- PROCESAMIENTO ---
if result and "GET_TEXT" in result:
    text = result.get("GET_TEXT")
    if text:
        st.info(f"**Escuchado:** {text}")
        
        if not os.path.exists("temp"):
            os.mkdir("temp")
            
        st.markdown("### ✨ Configuración")
        
        with st.container():
            c1, c2 = st.columns(2)
            langs = {"Inglés": "en", "Español": "es", "Bengali": "bn", "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja"}
            
            with c1:
                in_lang = st.selectbox("Desde", list(langs.keys()), index=1)
            with c2:
                out_lang = st.selectbox("Hacia", list(langs.keys()), index=0)

            accents = {"Defecto": "com", "Español": "com.mx", "Reino Unido": "co.uk", "EE.UU": "com"}
            english_accent = st.selectbox("Acento de voz", list(accents.keys()))

        if st.button("Traducir y Generar Audio"):
            with st.spinner("Procesando..."):
                translator = Translator()
                translation = translator.translate(text, src=langs[in_lang], dest=langs[out_lang])
                
                tts = gTTS(translation.text, lang=langs[out_lang], tld=accents[english_accent], slow=False)
                fname = f"temp/audio_{int(time.time())}.mp3"
                tts.save(fname)
                
                st.success(f"**Traducción:** {translation.text}")
                with open(fname, "rb") as f:
                    st.audio(f.read(), format="audio/mp3")

# Limpieza
def remove_files(n):
    mp3_files = glob.glob("temp/*mp3")
    now = time.time()
    for f in mp3_files:
        if os.stat(f).st_mtime < now - (n * 86400):
            try: os.remove(f)
            except: pass

remove_files(7)
