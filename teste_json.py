import json
import re

def salvar_relatorio_json(conteudo: str) -> str:
    conteudo_limpo = re.sub(r"^```(?:json)?|```$", "", conteudo.strip(), flags=re.MULTILINE).strip()
    print(conteudo_limpo)


texto_do_modelo = """
```json
{
  "emitente_info": {
    "nome": "Loja XPTO",
    "cnpj": "12.345.678/0001-90"
  },
  "valor_total_nota": "R$ 123,45"
}
```
"""
salvar_relatorio_json(texto_do_modelo)