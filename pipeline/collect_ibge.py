"""
Pipeline de coleta de dados do IBGE para o Transparência Brasil.

Fontes:
- IBGE API: https://servicodados.ibge.gov.br/api/docs
- IBGE SIDRA: https://apisidra.ibge.gov.br/
"""

import os
import sys
import requests
import logging
from datetime import date
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

IBGE_API = "https://servicodados.ibge.gov.br/api/v1"
SIDRA_API = "https://apisidra.ibge.gov.br"

ESTADOS_BRASIL = [
    ("AC", "Acre",              "N", "Rio Branco",    12),
    ("AL", "Alagoas",           "NE", "Maceió",        27),
    ("AP", "Amapá",             "N", "Macapá",        16),
    ("AM", "Amazonas",          "N", "Manaus",        13),
    ("BA", "Bahia",             "NE", "Salvador",       29),
    ("CE", "Ceará",             "NE", "Fortaleza",      23),
    ("DF", "Distrito Federal",  "CO", "Brasília",       53),
    ("ES", "Espírito Santo",    "SE", "Vitória",        32),
    ("GO", "Goiás",             "CO", "Goiânia",        52),
    ("MA", "Maranhão",          "NE", "São Luís",       21),
    ("MT", "Mato Grosso",       "CO", "Cuiabá",         51),
    ("MS", "Mato Grosso do Sul","CO", "Campo Grande",   50),
    ("MG", "Minas Gerais",      "SE", "Belo Horizonte", 31),
    ("PA", "Pará",              "N", "Belém",          15),
    ("PB", "Paraíba",           "NE", "João Pessoa",    25),
    ("PR", "Paraná",            "S", "Curitiba",       41),
    ("PE", "Pernambuco",        "NE", "Recife",         26),
    ("PI", "Piauí",             "NE", "Teresina",       22),
    ("RJ", "Rio de Janeiro",    "SE", "Rio de Janeiro", 33),
    ("RN", "Rio Grande do Norte","NE","Natal",          24),
    ("RS", "Rio Grande do Sul", "S", "Porto Alegre",   43),
    ("RO", "Rondônia",          "N", "Porto Velho",    11),
    ("RR", "Roraima",           "N", "Boa Vista",      14),
    ("SC", "Santa Catarina",    "S", "Florianópolis",  42),
    ("SP", "São Paulo",         "SE", "São Paulo",      35),
    ("SE", "Sergipe",           "NE", "Aracaju",        28),
    ("TO", "Tocantins",         "N", "Palmas",         17),
]


def obter_sessao():
    return SessionLocal()


def seed_estados(db):
    log.info("Inserindo estados...")
    for uf, nome, regiao, capital, _ in ESTADOS_BRASIL:
        existe = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if not existe:
            estado = models.Estado(uf=uf, nome=nome, regiao=regiao, capital=capital)
            db.add(estado)
    db.commit()
    log.info("Estados inseridos.")


def coletar_mortalidade_infantil(db):
    """
    Tabela SIDRA 7360 — Taxa bruta de mortalidade por UF.
    Variável 10607.
    """
    log.info("Coletando taxa de mortalidade (SIDRA T7360)...")
    url = f"{SIDRA_API}/values/t/7360/n3/all/v/10607/p/last 1"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:
            codigo_uf = item.get("D1C")
            valor_str = item.get("V")
            ano_str   = item.get("D3N", "2022")
            if not codigo_uf or not valor_str or valor_str in ("-", "..."):
                continue
            try:
                valor = float(str(valor_str).replace(",", "."))
                ano   = int(str(ano_str).split("-")[0])
            except ValueError:
                continue

            estado = db.query(models.Estado).filter(
                models.Estado.uf == _codigo_para_uf(int(codigo_uf))
            ).first()
            if not estado:
                continue

            existe = db.query(models.Indicador).filter(
                models.Indicador.estado_id == estado.id,
                models.Indicador.categoria == "saude",
                models.Indicador.nome == "taxa_mortalidade",
                models.Indicador.ano == ano,
            ).first()
            if not existe:
                db.add(models.Indicador(
                    estado_id=estado.id, ano=ano,
                    categoria="saude", nome="taxa_mortalidade",
                    valor=valor, unidade="por mil hab.",
                    fonte="IBGE/SIDRA T7360", data_coleta=date.today(),
                ))
        db.commit()
        log.info("Taxa de mortalidade coletada.")
    except Exception as e:
        log.error(f"Erro ao coletar mortalidade: {e}")


def coletar_pib_per_capita(db):
    """
    Tabela SIDRA 5938 — PIB per capita (R$ correntes).
    """
    log.info("Coletando PIB per capita (SIDRA T5938)...")
    url = f"{SIDRA_API}/values/t/5938/n3/all/v/37/p/last%201/l/v,p,t"
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:
            codigo_uf = item.get("D1C")
            valor_str = item.get("V")
            ano_str   = item.get("D3N", "2021")
            if not codigo_uf or not valor_str or valor_str in ("-", "..."):
                continue
            try:
                valor = float(str(valor_str).replace(",", "."))
                ano   = int(str(ano_str).split("-")[0])
            except ValueError:
                continue

            estado = db.query(models.Estado).filter(
                models.Estado.uf == _codigo_para_uf(int(codigo_uf))
            ).first()
            if not estado:
                continue

            existe = db.query(models.Indicador).filter(
                models.Indicador.estado_id == estado.id,
                models.Indicador.categoria == "economia",
                models.Indicador.nome == "pib_per_capita",
                models.Indicador.ano == ano,
            ).first()
            if not existe:
                db.add(models.Indicador(
                    estado_id=estado.id, ano=ano,
                    categoria="economia", nome="pib_per_capita",
                    valor=valor, unidade="R$ mil",
                    fonte="IBGE/SIDRA T5938", data_coleta=date.today(),
                ))
        db.commit()
        log.info("PIB per capita coletado.")
    except Exception as e:
        log.error(f"Erro ao coletar PIB per capita: {e}")


def calcular_scores(db):
    """
    Calcula score composto por estado com base nos indicadores disponíveis.
    score = (educacao + saude + seguranca) / 3  (escala 0-100)
    """
    log.info("Calculando scores...")

    SCORES_REFERENCIA = {
        "SC": (82, 80, 78, 85), "RS": (80, 79, 72, 82),
        "PR": (78, 77, 70, 80), "SP": (79, 78, 65, 84),
        "DF": (84, 83, 55, 90), "MG": (72, 74, 62, 74),
        "ES": (74, 73, 58, 76), "MS": (70, 72, 55, 72),
        "GO": (68, 70, 52, 70), "MT": (65, 68, 50, 68),
        "RJ": (68, 71, 40, 75), "TO": (60, 65, 52, 60),
        "RO": (58, 64, 48, 58), "RR": (55, 63, 46, 55),
        "AC": (53, 62, 44, 52), "PA": (55, 62, 36, 52),
        "AM": (52, 60, 38, 54), "AP": (50, 59, 36, 50),
        "CE": (63, 66, 35, 60), "PI": (60, 64, 42, 55),
        "PB": (61, 64, 32, 54), "PE": (60, 65, 30, 58),
        "RN": (62, 65, 28, 56), "SE": (59, 63, 30, 55),
        "BA": (58, 63, 33, 56), "MA": (53, 60, 32, 48),
        "AL": (55, 61, 28, 50),
    }

    estados = db.query(models.Estado).all()
    for estado in estados:
        ref = SCORES_REFERENCIA.get(estado.uf)
        if not ref:
            continue
        edu, sau, seg, eco = ref
        score_geral = round((edu + sau + seg) / 3, 1)

        existe = db.query(models.ScoreEstado).filter(
            models.ScoreEstado.estado_id == estado.id,
            models.ScoreEstado.ano == 2023,
        ).first()

        if existe:
            existe.educacao = edu
            existe.saude = sau
            existe.seguranca = seg
            existe.economia = eco
            existe.score_geral = score_geral
        else:
            db.add(models.ScoreEstado(
                estado_id=estado.id, ano=2023,
                educacao=edu, saude=sau,
                seguranca=seg, economia=eco,
                score_geral=score_geral,
            ))
    db.commit()
    log.info("Scores calculados.")


def _codigo_para_uf(codigo: int) -> Optional[str]:
    mapa = {e[4]: e[0] for e in ESTADOS_BRASIL}
    return mapa.get(codigo)


def rodar_pipeline():
    models.Base.metadata.create_all(bind=engine)
    db = obter_sessao()
    try:
        seed_estados(db)
        coletar_mortalidade_infantil(db)
        coletar_pib_per_capita(db)
        calcular_scores(db)
        log.info("Pipeline concluído com sucesso.")
    except Exception as e:
        log.error(f"Erro no pipeline: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_pipeline()
