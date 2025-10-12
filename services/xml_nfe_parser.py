import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from domain.models import DestinatarioInfo, EmitenteInfo, ItemInfo, NFeExtract

NFE_NS = {"nfe": "http://www.portalfiscal.inf.br/nfe"}


def _tx(elem: Optional[ET.Element], path: str) -> str:
    if elem is None:
        return ""
    v = elem.findtext(path, namespaces=NFE_NS)
    return v.strip() if v else ""


def _addr(end) -> str:
    if end is None:
        return ""
    xLgr = _tx(end, "nfe:xLgr")
    nro = _tx(end, "nfe:nro")
    xBairro = _tx(end, "nfe:xBairro")
    xMun = _tx(end, "nfe:xMun")
    UF = _tx(end, "nfe:UF")
    CEP = _tx(end, "nfe:CEP")
    parts = []
    if xLgr:
        parts.append(xLgr)
    if nro:
        parts.append(nro)
    meio = " - ".join(filter(None, [xBairro]))
    cidade = "/".join(filter(None, [xMun, UF]))
    tail = f"CEP {CEP}" if CEP else ""
    bloco = ", ".join(parts)
    restos = ", ".join(filter(None, [meio, cidade, tail]))
    return (bloco + (", " if bloco and restos else "") + restos).strip()


def parse_nfe_xml_to_model(xml_bytes: bytes) -> NFeExtract:
    """
    Faz o parse determinístico de uma NF-e v4.00 (namespace oficial) "
    para o modelo de domínio.
    """
    root = ET.fromstring(xml_bytes)

    inf = root.find(".//nfe:infNFe", NFE_NS)
    if inf is None:
        raise ValueError("XML não parece ser NF-e v4.00: nó infNFe ausente.")

    ide = inf.find("nfe:ide", NFE_NS)
    dhEmi = _tx(ide, "nfe:dhEmi")

    emit = inf.find("nfe:emit", NFE_NS)
    emit_end = emit.find("nfe:enderEmit", NFE_NS) if emit is not None else None
    emitente = EmitenteInfo(
        nome=_tx(emit, "nfe:xNome"),
        cnpj=_tx(emit, "nfe:CNPJ"),
        endereco=_addr(emit_end),
        telefone=_tx(emit_end, "nfe:fone")
    )

    dest = inf.find("nfe:dest", NFE_NS)
    dest_end = dest.find("nfe:enderDest", NFE_NS) if dest is not None else None
    cpf_cnpj = _tx(dest, "nfe:CNPJ") or _tx(dest, "nfe:CPF")
    destinatario = DestinatarioInfo(
        nome=_tx(dest, "nfe:xNome"),
        cpf_cnpj=cpf_cnpj,
        endereco=_addr(dest_end),
        telefone=_tx(dest_end, "nfe:fone")
    )

    itens: List[ItemInfo] = []
    for det in inf.findall("nfe:det", NFE_NS):
        prod = det.find("nfe:prod", NFE_NS)
        if prod is None:
            continue
        itens.append(ItemInfo(
            descricao=_tx(prod, "nfe:xProd"),
            quantidade=_tx(prod, "nfe:qCom"),
            valor_unitario_item=_tx(prod, "nfe:vUnCom"),
            valor_total_item=_tx(prod, "nfe:vProd"),
        ))

    icms_tot = inf.find("nfe:total/nfe:ICMSTot", NFE_NS)
    vNF = _tx(icms_tot, "nfe:vNF")
    vICMS = _tx(icms_tot, "nfe:vICMS")
    vIPI = _tx(icms_tot, "nfe:vIPI")
    vPIS = _tx(icms_tot, "nfe:vPIS")
    vCOFINS = _tx(icms_tot, "nfe:vCOFINS")

    cfop, cst = "", ""
    first_det = inf.find("nfe:det", NFE_NS)
    if first_det is not None:
        prod = first_det.find("nfe:prod", NFE_NS)
        cfop = _tx(prod, "nfe:CFOP") if prod is not None else ""
        cst_node = first_det.find(".//nfe:ICMS//nfe:CST", NFE_NS)
        if cst_node is not None and cst_node.text:
            cst = cst_node.text.strip()

    outros_codigos_fiscais: Dict[str, str] = {}
    if first_det is not None:
        prod = first_det.find("nfe:prod", NFE_NS)
        if prod is not None:
            ncm = _tx(prod, "nfe:NCM")
            if ncm:
                outros_codigos_fiscais["NCM"] = ncm

        icms_any = first_det.find(".//nfe:ICMS/*", NFE_NS)
        if icms_any is not None:
            modBC = icms_any.find("nfe:modBC", NFE_NS)
            if modBC is not None and modBC.text:
                outros_codigos_fiscais["modBC"] = modBC.text.strip()

    return NFeExtract(
        emitente_info=emitente,
        destinatario_info=destinatario,
        info_nota=itens,
        data_hora_emissao=dhEmi,
        valor_total_nota=vNF,
        icms=vICMS,
        ipi=vIPI,
        pis=vPIS,
        cofins=vCOFINS,
        cfop=cfop,
        cst=cst,
        outros_codigos_fiscais=outros_codigos_fiscais or {}
    )
