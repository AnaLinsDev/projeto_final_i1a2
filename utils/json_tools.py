import json
import re


def strip_md_fences(s: str) -> str:
    """
    Remove cercas de markdown ``` ou ```json no início/fim, se existirem.
    """
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def ensure_pretty_json(s: str) -> str:
    """
    Tenta converter 's' em JSON bonito. Se falhar, devolve o texto como veio.
    """
    try:
        obj = json.loads(strip_md_fences(s))
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except Exception:
        return s.strip()
