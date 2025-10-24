from dataclasses import asdict, dataclass
from typing import Dict, List


@dataclass
class EmitenteInfo:
    nome: str = ""
    cnpj: str = ""
    endereco: str = ""
    telefone: str = ""


@dataclass
class DestinatarioInfo:
    nome: str = ""
    cpf_cnpj: str = ""
    endereco: str = ""
    telefone: str = ""


@dataclass
class ItemInfo:
    descricao: str = ""
    quantidade: str = ""
    valor_unitario_item: str = ""
    valor_total_item: str = ""
    codigos_fiscais_item: Dict[str, str] = None

    def to_dict(self) -> Dict:
        d = asdict(self)
        if d.get("codigos_fiscais_item") is None:
            d["codigos_fiscais_item"] = {}
        return d

@dataclass
class NFeExtract:
    emitente_info: EmitenteInfo
    destinatario_info: DestinatarioInfo
    info_nota: List[ItemInfo]
    data_hora_emissao: str = ""
    valor_total_nota: str = ""
    icms: str = ""
    ipi: str = ""
    pis: str = ""
    cofins: str = ""
    cfop: str = ""
    cst: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self)
        if not d.get("info_nota"):
            d["info_nota"] = [asdict(ItemInfo())]
        return d
