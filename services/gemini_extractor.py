from typing import Optional

import google.generativeai as genai

SYSTEM_PROMPT = """
Extraia TODO o texto legível do arquivo enviado e devolva apenas o texto puro,
sem explicações.
"""


def extract_text_with_gemini(model, file_bytes: bytes, mime_type: str) -> str:
    """
    Extrai texto de PDF/Imagem usando Gemini Multimodal.
    """
    resp = model.generate_content(
        [
            {"mime_type": mime_type, "data": file_bytes},
            SYSTEM_PROMPT
        ]
    )
    return (resp.text or "").strip()


def build_nfe_prompt(texto: str) -> str:
    return f"""
Leia o texto de uma nota fiscal brasileira e extraia
os dados nos campos especificados.

Texto para análise (parcial, até 8000 chars):
{texto[:8000]}

Responda APENAS com o JSON válido, no exato formato:

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
      "valor_unitario_item": "",
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

Regras:
- Inclua SOMENTE códigos fiscais em "outros_codigos_fiscais".
- NÃO inclua IE, IM, COO, CCF, MD5, chaves, versões de software,
ou identificadores técnicos.
- Se um campo não estiver presente, deixe string vazia "".
- Apenas JSON válido, sem comentários nem crases.
""".strip()
