import os
import fitz  # PyMuPDF
import tempfile
import streamlit as st
import google.generativeai as genai
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

# ------------------------------------------------------
# --- Funções auxiliares -------------------------------
# ------------------------------------------------------

def log_message(text: str):
    """Exibe mensagens de log na interface Streamlit."""
    st.write(text)


def extract_text_with_ocr(pdf_path: str) -> str:
    """Extrai texto de PDFs escaneados usando OCR (Tesseract)."""
    text = ""
    try:
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img, lang="por")
    except Exception as e:
        raise ValueError(f"Erro ao processar OCR: {e}")
    return text.strip()


def pdf_to_text(pdf_path: str) -> str:
    """
    Extrai texto de um PDF.
    - Primeiro tenta extração direta (PyMuPDF).
    - Se falhar ou não houver texto, usa OCR como fallback.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    text = ""
    try:
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text("text")
    except Exception:
        text = ""

    if not text.strip():
        st.info("📷 PDF parece ser escaneado — usando OCR para extrair o texto...")
        text = extract_text_with_ocr(pdf_path)

    return text.strip()


def gerar_prompt_pdf(pdf_text: str) -> str:
    """Monta o prompt de extração estruturada no formato JSON."""
    return f"""
Leia o texto de uma nota fiscal brasileira e extraia os dados nos campos especificados.

Texto para análise:
{pdf_text[:8000]}  # truncado para evitar limite de tokens

Responda **apenas** com o JSON preenchido, seguindo o formato abaixo:

{{
  "emitente_info": {{
    "nome": "",
    "cnpj": "",
    "endereco": "",
    "telefone": ""
  }},
  "destinatario_info": {{
    "nome": "",
    "cpf_cnpj": "",
    "endereco": "",
    "telefone": ""
  }},
  "info_nota": [
    {{
      "descricao": "",
      "quantidade": "",
      "valor_total_item": ""
    }}
  ],
  "valor_total_nota": "",
  "icms": "",
  "ipi": "",
  "pis": "",
  "cofins": "",
  "cfop": "",
  "cst": "",
  "outros_codigos_fiscais": ""
}}

Se algum campo não existir, deixe-o como string vazia ("").
    """.strip()

# ------------------------------------------------------
# --- Interface Streamlit ------------------------------
# ------------------------------------------------------

st.set_page_config(page_title="Agente I2A2 - Leitor de Nota Fiscal", page_icon="🤖")
st.title("🤖 Agente I2A2 - Leitor de Nota Fiscal (PDF)")

# Campo para API Key
api_key = st.text_input("🔑 Insira sua Google API Key:", type="password")

if not api_key:
    st.warning("⚠️ Insira sua API Key para continuar.")
    st.stop()

# Configuração da API
os.environ["GOOGLE_API_KEY"] = api_key
genai.configure(api_key=api_key)
model = genai.GenerativeModel("models/gemini-2.5-flash")

# Upload de PDF
uploaded_file = st.file_uploader("📂 Faça upload do arquivo PDF da nota fiscal", type=["pdf"])

if uploaded_file:
    with st.spinner("📂 Lendo e processando o PDF..."):
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp_file.write(uploaded_file.getbuffer())
        tmp_file.close()

        pdf_path = tmp_file.name
        pdf_text = pdf_to_text(pdf_path)

    if not pdf_text.strip():
        st.error("❌ Não foi possível extrair texto do PDF. Verifique se o arquivo está legível.")
        st.stop()

    st.success(f"✅ Arquivo '{uploaded_file.name}' processado com sucesso!")

    with st.spinner("🤖 Extraindo dados estruturados..."):
        prompt = gerar_prompt_pdf(pdf_text)
        try:
            response = model.generate_content(prompt)
            st.subheader("📊 Resultado (JSON):")
            st.code(response.text.strip(), language="json")
        except Exception as e:
            st.error(f"Erro durante a análise: {e}")

else:
    st.info("⬆️ Faça upload de um arquivo PDF para começar.")
