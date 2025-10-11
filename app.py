import os
import re
import tempfile
import time
import streamlit as st
import google.generativeai as genai

# ------------------------------------------------------
# --- Configuração da Página ---------------------------
# ------------------------------------------------------

st.set_page_config(
    page_title="🤖 Agente I2A2 - Leitor de Nota Fiscal",
    page_icon="🧾",
    layout="centered"
)

# ------------------------------------------------------
# --- Estilos customizados -----------------------------
# ------------------------------------------------------

st.markdown("""
    <style>
        /* Centraliza o conteúdo */
        .block-container {
            max-width: 900px;
            margin: auto;
            padding-top: 2rem;
        }
        /* Estilo dos títulos */
        h1, h2, h3 {
            text-align: center;
            color: #2B4162;
        }
        /* Caixa de upload personalizada */
        .stFileUploader {
            border: 2px dashed #6C63FF;
            border-radius: 12px;
            padding: 1rem;
        }
        /* Spinner */
        div[data-testid="stSpinner"] p {
            font-size: 1.1rem;
            font-weight: 500;
        }
        /* Caixa de código */
        pre code {
            white-space: pre-wrap !important;
            word-wrap: break-word !important;
        }
    </style>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# --- Funções auxiliares -------------------------------
# ------------------------------------------------------

def extrair_texto_via_gemini(model, file_bytes: bytes, file_name: str, mime_type: str) -> str:
    """Envia o arquivo diretamente ao modelo Gemini para extrair o texto."""
    try:
        response = model.generate_content(
            [
                {"mime_type": mime_type, "data": file_bytes},
                "\nExtraia **todo o texto legível** deste arquivo e devolva apenas o texto puro, sem explicações."
            ]
        )
        return response.text.strip()
    except Exception as e:
        raise ValueError(f"Erro ao processar arquivo com Gemini: {e}")

def gerar_prompt_nota_fiscal(texto_extraido: str) -> str:
    """Gera o prompt de análise da nota fiscal."""
    return f"""
    Leia o texto de uma nota fiscal brasileira e extraia os dados nos campos especificados.

    Texto para análise:
    {texto_extraido[:8000]}

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
          "valor_unitario_item": ""
          "valor_total_item": ""
        }}
      ],
      "data_hora_emissao": "",
      "valor_total_nota": "",
      "icms": "",
      "ipi": "",
      "pis": "",
      "cofins": "",
      "cfop": "",
      "cst": "",
      "outros_codigos_fiscais": {{}}
    }}


    ⚠️ Instruções adicionais:
    - Inclua **somente códigos fiscais** no campo "outros_codigos_fiscais".
    - **NÃO** inclua números de série, IE, IM, COO, CCF, MD5, versões de software, ou identificadores técnicos de impressora fiscal.
    - Se o campo não estiver presente, deixe o campo como string vazia ("").
    - Use o formato JSON válido, sem explicações adicionais.

    """.strip()

# ------------------------------------------------------
# --- Interface principal ------------------------------
# ------------------------------------------------------

st.title("🤖 Agente I2A2 - Leitor de Nota Fiscal")
st.caption("💡 Faça upload de um PDF, XML ou imagem (JPG/PNG) contendo uma nota fiscal para análise automática.")

# Entrada da API Key
api_key = st.text_input("🔑 Insira sua Google API Key:", type="password", help="Necessária para usar o modelo Gemini.")

if not api_key:
    st.info("🔐 Insira sua API Key para começar.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key
genai.configure(api_key=api_key)

model = genai.GenerativeModel("models/gemini-2.5-flash")

# Upload de arquivo
uploaded_file = st.file_uploader(
    "📂 Faça upload do arquivo da nota fiscal",
    type=["pdf", "xml", "jpg", "jpeg", "png"]
)

if uploaded_file:
    start_time = time.time()

    file_ext = uploaded_file.name.split(".")[-1].lower()
    mime_map = {
        "pdf": "application/pdf",
        "xml": "application/xml",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }
    mime_type = mime_map.get(file_ext, "application/octet-stream")

    st.success(f"✅ Arquivo **{uploaded_file.name}** detectado! Tipo: **.{file_ext}**")

    with st.spinner("📖 Extraindo texto com Gemini..."):
        try:
            texto_extraido = extrair_texto_via_gemini(model, uploaded_file.getvalue(), uploaded_file.name, mime_type)
        except Exception as e:
            st.error(f"❌ Erro ao processar o arquivo: {e}")
            st.stop()

    if not texto_extraido.strip():
        st.error("⚠️ O Gemini não conseguiu extrair texto do arquivo.")
        st.stop()

    with st.spinner("🤖 Gerando JSON estruturado..."):
        try:
            prompt = gerar_prompt_nota_fiscal(texto_extraido)
            response = model.generate_content(prompt)
        except Exception as e:
            st.error(f"❌ Erro durante a análise: {e}")
            st.stop()

    total_time = time.time() - start_time

    st.success(f"🎉 Análise concluída em **{total_time:.2f} segundos**!")
    st.subheader("📊 Resultado (JSON extraído):")

    # Mostra o JSON formatado
    json_result = response.text.strip()
    st.code(json_result, language="json")

    json_resulto_download = re.sub(r"^```(?:json)?|```$", "", json_result, flags=re.MULTILINE).strip()

    # Botão para download
    st.download_button(
        label="💾 Baixar JSON",
        data=json_resulto_download.encode("utf-8"),
        file_name="relatorio.json",
        mime="application/json",
        help="Clique para baixar o resultado em formato JSON"
    )


else:
    st.info("⬆️ Faça upload de um arquivo para iniciar a análise.")

