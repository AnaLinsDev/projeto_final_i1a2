import json
import os
import time

import google.generativeai as genai
import streamlit as st

from services.gemini_extractor import (build_nfe_prompt,
                                       extract_text_with_gemini)
from services.xml_nfe_parser import parse_nfe_xml_to_model
from utils.json_tools import ensure_pretty_json

st.set_page_config(
    page_title="🤖 Agente I2A2 - Leitor de Nota Fiscal",
    page_icon="🧾",
    layout="centered"
)


st.markdown("""
<style>
.block-container { max-width: 900px; margin: auto; padding-top: 2rem; }
h1, h2, h3 { text-align: center; color: #2B4162; }
.stFileUploader { border: 2px dashed #6C63FF; border-radius: 12px; padding: 1rem; }
div[data-testid="stSpinner"] p { font-size: 1.1rem; font-weight: 500; }
pre code { white-space: pre-wrap !important; word-wrap: break-word !important; }
</style>
""", unsafe_allow_html=True)


st.title("🤖 Agente I2A2 - Leitor de Nota Fiscal")
st.caption("💡 Envie um PDF, XML ou imagem (JPG/PNG) "
           "com uma Nota Fiscal para análise automática.")


api_key = st.text_input(
    "🔑 Insira sua Google API Key "
    "(obrigatória para PDF/Imagem; opcional para XML):",
    type="password",
    help="Para XML, o app parseia localmente sem IA. Para PDF/Imagem, usa Gemini."
)

if api_key:
    os.environ["GOOGLE_API_KEY"] = api_key
    genai.configure(api_key=api_key)


def get_gemini_model():
    if not api_key:
        st.error("Para PDF/Imagem você precisa informar a Google API Key.")
        st.stop()
    try:
        return genai.GenerativeModel("models/gemini-2.5-flash")
    except AttributeError:
        st.error(
            "A classe GenerativeModel não está disponível."
            "Atualize o pacote google-generativeai."
        )
        st.stop()



uploaded_files = st.file_uploader(
    "📂 Faça upload dos arquivos das Notas Fiscais",
    type=["pdf", "xml", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if not uploaded_files:
    st.info("⬆️ Faça upload de um ou mais arquivos para iniciar a análise.")
    st.stop()

start_time = time.time()
json_results = []
errors = []

for uploaded_file in uploaded_files:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    st.success(
        f"✅ Arquivo **{uploaded_file.name}** detectado! Tipo: **.{file_ext}**"
    )

    if file_ext == "xml":
        with st.spinner(
            f"📖 Lendo NF-e (XML) localmente: {uploaded_file.name}..."
        ):
            try:
                nfe = parse_nfe_xml_to_model(uploaded_file.getvalue())
                data = nfe.to_dict()
                json_results.append(data)
            except Exception as e:
                errors.append(f"{uploaded_file.name}: {e}")
        continue

    mime_map = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }
    mime_type = mime_map.get(file_ext)
    if not mime_type:
        errors.append(
            f"{uploaded_file.name}: Tipo de arquivo não suportado para análise com IA."
        )
        continue

    model = get_gemini_model()

    with st.spinner(f"📖 Extraindo texto com Gemini: {uploaded_file.name}..."):
        try:
            texto_extraido = extract_text_with_gemini(
                model,
                uploaded_file.getvalue(),
                mime_type
            )
        except Exception as e:
            errors.append(
                f"{uploaded_file.name}: Erro ao extrair texto com Gemini: {e}"
            )
            continue

    if not texto_extraido.strip():
        errors.append(
            f"{uploaded_file.name}: O Gemini não conseguiu extrair texto do arquivo."
        )
        continue

    with st.spinner(
        f"🤖 Estruturando JSON com Gemini: {uploaded_file.name}..."
    ):
        try:
            prompt = build_nfe_prompt(texto_extraido)
            response = model.generate_content(prompt)
            raw = (response.text or "").strip()
            pretty = ensure_pretty_json(raw)
            # Tenta converter para dict para garantir que é JSON válido
            try:
                data = json.loads(pretty)
            except Exception:
                data = pretty
            json_results.append(data)
        except Exception as e:
            errors.append(f"{uploaded_file.name}: Erro durante a análise: {e}")
            continue

total_time = time.time() - start_time

if json_results:
    st.success(f"🎉 Análise concluída em **{total_time:.2f} segundos**!")
    st.subheader(f"📊 Resultado ({len(json_results)} JSON extraídos):")
    pretty_json = json.dumps(json_results, ensure_ascii=False, indent=2)
    st.code(pretty_json, language="json")
    st.download_button(
        "💾 Baixar JSONs",
        data=pretty_json.encode("utf-8"),
        file_name="relatorios.json",
        mime="application/json"
    )
else:
    st.error("❌ Nenhum JSON foi extraído dos arquivos enviados.")

if errors:
    st.warning("\n".join(errors))
