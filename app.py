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
            "A classe GenerativeModel não está disponível. "
            "Atualize o pacote google-generativeai."
        )
        st.stop()


# === Configurações da página ===
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

# === Interface principal ===
st.title("🤖 Agente I2A2 - Leitor de Nota Fiscal (Multi-arquivos)")
st.caption("💡 Envie **um ou mais PDFs, XMLs ou imagens (JPG/PNG)** de Notas Fiscais para análise automática.")

# === Input da API Key ===
api_key = st.text_input(
    "🔑 Insira sua Google API Key",
    type="password",
    help="Obrigatória para todos os tipos de arquivo (PDF, XML, imagem)."
)

if not api_key:
    st.warning("⚠️ Insira sua Google API Key para liberar o upload dos arquivos.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key
genai.configure(api_key=api_key)

# === Upload de múltiplos arquivos ===
uploaded_files = st.file_uploader(
    "📂 Faça upload dos arquivos das Notas Fiscais",
    type=["pdf", "xml", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if "results" not in st.session_state:
    st.session_state["results"] = None

# === Botão de processamento ===
if uploaded_files and st.button("🚀 Processar arquivos"):
    all_results = []
    model = get_gemini_model()

    for uploaded_file in uploaded_files:
        st.divider()
        st.subheader(f"📄 Processando: {uploaded_file.name}")

        start_time = time.time()
        file_ext = uploaded_file.name.split(".")[-1].lower()
        st.success(f"✅ Arquivo **{uploaded_file.name}** detectado! Tipo: **.{file_ext}**")

        result_json = None

        # === Tratamento XML direto ===
        if file_ext == "xml":
            with st.spinner("📖 Enviando XML para o Gemini..."):
                try:
                    xml_content = uploaded_file.getvalue().decode("utf-8", errors="ignore")
                    prompt = build_nfe_prompt(xml_content)
                    response = model.generate_content(prompt)
                    raw = (response.text or "").strip()
                    result_json = json.loads(ensure_pretty_json(raw))
                except Exception as e:
                    st.error(f"❌ Erro ao processar XML com Gemini: {e}")
                    continue

        # === Tratamento para PDF/Imagem ===
        else:
            mime_map = {
                "pdf": "application/pdf",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
            }
            mime_type = mime_map.get(file_ext)

            if not mime_type:
                st.error(f"❌ Tipo de arquivo não suportado: {file_ext}")
                continue

            with st.spinner("📖 Extraindo texto com Gemini..."):
                try:
                    texto_extraido = extract_text_with_gemini(
                        model,
                        uploaded_file.getvalue(),
                        mime_type
                    )
                except Exception as e:
                    st.error(f"❌ Erro ao extrair texto com Gemini: {e}")
                    continue

            if not texto_extraido.strip():
                st.error("⚠️ O Gemini não conseguiu extrair texto do arquivo.")
                continue

            with st.spinner("🤖 Estruturando JSON com Gemini..."):
                try:
                    prompt = build_nfe_prompt(texto_extraido)
                    response = model.generate_content(prompt)
                    raw = (response.text or "").strip()
                    result_json = json.loads(ensure_pretty_json(raw))
                except Exception as e:
                    st.error(f"❌ Erro durante a análise: {e}")
                    continue

        if result_json:
            all_results.append({
                "file_name": uploaded_file.name,
                "data": result_json
            })

        total_time = time.time() - start_time
        st.info(f"🕒 {uploaded_file.name} processado em {total_time:.2f} segundos.")

    if all_results:
        st.session_state["results"] = all_results
        st.success("✅ Todos os arquivos foram processados com sucesso!")

# === Exibição final (usando session_state) ===
if st.session_state["results"]:
    combined_json = json.dumps(st.session_state["results"], indent=2, ensure_ascii=False)
    st.divider()
    st.subheader("📊 Resultado Final (array de JSONs):")
    st.code(combined_json, language="json")

    st.download_button(
        "💾 Baixar resultado combinado",
        data=combined_json.encode("utf-8"),
        file_name="resultado_combinado.json",
        mime="application/json"
    )
