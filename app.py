import json
import os
import time
import google.generativeai as genai
import streamlit as st

from services.gemini_extractor import build_nfe_prompt, extract_text_with_gemini
from utils.json_tools import ensure_pretty_json


# === Função para inicializar o modelo ===
def get_gemini_model():
    if not api_key:
        st.error("Para PDF/Imagem/XML você precisa informar a Google API Key.")
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

    with st.spinner("🤖 Estruturando JSON com Gemini..."):
        try:
            prompt = build_nfe_prompt(texto_extraido)
            response = model.generate_content(prompt)
            raw = (response.text or "").strip()
            pretty_json = ensure_pretty_json(raw)
        except Exception as e:
            st.error(f"❌ Erro durante a análise: {e}")
            st.stop()

# === Resultado ===
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
