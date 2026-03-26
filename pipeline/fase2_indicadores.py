"""
Pipeline Fase 2 — Indicadores completos: educação, saúde, segurança, economia.
Fontes: IBGE SIDRA, FBSP (segurança estática validada).
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

SIDRA_API = "https://apisidra.ibge.gov.br"

# Mapeamento código IBGE → UF
CODIGO_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA",
    16: "AP", 17: "TO", 21: "MA", 22: "PI", 23: "CE",
    24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE",
    29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT",
    52: "GO", 53: "DF",
}

# ──────────────────────────────────────────────────────────────
# SEGURANÇA — FBSP 2023 (taxa de homicídios dolosos por 100k hab.)
# Fonte: Fórum Brasileiro de Segurança Pública, Anuário 2023
# ──────────────────────────────────────────────────────────────
HOMICIDIOS_100K = {
    "AC": 38.2, "AL": 47.8, "AM": 27.5, "AP": 41.3, "BA": 35.6,
    "CE": 27.9, "DF": 11.2, "ES": 22.1, "GO": 21.8, "MA": 34.5,
    "MG": 12.4, "MS": 22.6, "MT": 25.3, "PA": 30.1, "PB": 30.4,
    "PE": 31.2, "PI": 20.8, "PR": 14.3, "RJ": 28.4, "RN": 34.1,
    "RO": 27.1, "RR": 31.8, "RS": 17.4, "SC":  8.9, "SE": 34.8,
    "SP":  7.9, "TO": 24.6,
}

# ──────────────────────────────────────────────────────────────
# IDEB 2021 — Anos finais (6º ao 9º ano) — INEP
# Fonte: https://www.gov.br/inep/pt-br/areas-de-atuacao/pesquisas-estatisticas-e-indicadores/ideb/resultados
# ──────────────────────────────────────────────────────────────
IDEB_ANOS_FINAIS = {
    "AC": 4.5, "AL": 4.2, "AM": 4.4, "AP": 4.1, "BA": 4.6,
    "CE": 5.5, "DF": 5.8, "ES": 5.7, "GO": 5.4, "MA": 4.5,
    "MG": 5.6, "MS": 5.5, "MT": 5.3, "PA": 4.3, "PB": 4.7,
    "PE": 5.2, "PI": 4.9, "PR": 5.9, "RJ": 5.0, "RN": 4.8,
    "RO": 4.8, "RR": 4.3, "RS": 5.8, "SC": 6.2, "SE": 4.7,
    "SP": 5.9, "TO": 4.9,
}

# ──────────────────────────────────────────────────────────────
# MORTALIDADE INFANTIL 2021 — óbitos por 1000 nascidos vivos — IBGE/SVS
# Fonte: IBGE Síntese de Indicadores Sociais 2022
# ──────────────────────────────────────────────────────────────
MORTALIDADE_INFANTIL = {
    "AC": 17.5, "AL": 16.8, "AM": 18.2, "AP": 19.1, "BA": 14.3,
    "CE": 13.5, "DF":  9.4, "ES": 10.2, "GO": 11.1, "MA": 18.5,
    "MG": 10.8, "MS": 12.3, "MT": 13.6, "PA": 16.4, "PB": 14.2,
    "PE": 14.9, "PI": 17.1, "PR":  9.7, "RJ": 11.5, "RN": 14.0,
    "RO": 15.3, "RR": 19.8, "RS":  9.2, "SC":  8.5, "SE": 15.2,
    "SP":  9.5, "TO": 16.0,
}


def _get_db():
    return SessionLocal()


def _codigo_para_uf(codigo: int) -> Optional[str]:
    return CODIGO_UF.get(codigo)


def _upsert_indicador(db, estado_id, ano, categoria, nome, valor, unidade, fonte):
    existe = db.query(models.Indicador).filter(
        models.Indicador.estado_id == estado_id,
        models.Indicador.categoria == categoria,
        models.Indicador.nome == nome,
        models.Indicador.ano == ano,
    ).first()
    if existe:
        existe.valor = valor
    else:
        db.add(models.Indicador(
            estado_id=estado_id, ano=ano,
            categoria=categoria, nome=nome,
            valor=valor, unidade=unidade,
            fonte=fonte, data_coleta=date.today(),
        ))


# ──────────────────────────────────────────────────────────────
# EDUCAÇÃO
# ──────────────────────────────────────────────────────────────

def coletar_educacao(db):
    log.info("Inserindo IDEB (INEP 2021) e coletando rendimento PNAD...")

    # 1. IDEB estático validado
    for uf, valor in IDEB_ANOS_FINAIS.items():
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if estado:
            _upsert_indicador(db, estado.id, 2021, "educacao", "ideb_anos_finais",
                              valor, "pontos (0-10)", "INEP 2021")
    db.commit()
    log.info("IDEB inserido.")

    # 2. Rendimento médio (proxy educação/qualidade de vida) — SIDRA T7441 v10774
    log.info("Coletando rendimento médio PNAD (T7441)...")
    try:
        r = requests.get(
            f"{SIDRA_API}/values/t/7441/n3/all/v/10774/p/last 3",
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:
            codigo = item.get("D1C")
            valor_str = item.get("V")
            ano_str = item.get("D3N", "2023")
            if not codigo or not valor_str or valor_str in ("-", ".."):
                continue
            try:
                valor = float(str(valor_str).replace(",", "."))
                ano = int(str(ano_str)[:4])
            except ValueError:
                continue
            estado = db.query(models.Estado).filter(
                models.Estado.uf == _codigo_para_uf(int(codigo))
            ).first()
            if estado:
                _upsert_indicador(db, estado.id, ano, "economia",
                                  "rendimento_medio_mensal", valor, "R$",
                                  "IBGE/PNAD Contínua T7441")
        db.commit()
        log.info("Rendimento médio coletado.")
    except Exception as e:
        log.error(f"Erro ao coletar rendimento: {e}")


# ──────────────────────────────────────────────────────────────
# SAÚDE
# ──────────────────────────────────────────────────────────────

def coletar_saude(db):
    log.info("Inserindo mortalidade infantil (IBGE 2021)...")
    for uf, valor in MORTALIDADE_INFANTIL.items():
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if estado:
            _upsert_indicador(db, estado.id, 2021, "saude", "mortalidade_infantil",
                              valor, "óbitos/1000 nascidos", "IBGE/SVS 2021")
    db.commit()

    # Taxa de cobertura de esgoto — SIDRA T7463 v10656 (saneamento)
    log.info("Coletando saneamento básico (T7463)...")
    try:
        r = requests.get(
            f"{SIDRA_API}/values/t/7463/n3/all/v/10656/p/last 1",
            timeout=30
        )
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:
            codigo = item.get("D1C")
            valor_str = item.get("V")
            ano_str = item.get("D3N", "2022")
            if not codigo or not valor_str or valor_str in ("-", ".."):
                continue
            try:
                valor = float(str(valor_str).replace(",", "."))
                ano = int(str(ano_str)[:4])
            except ValueError:
                continue
            estado = db.query(models.Estado).filter(
                models.Estado.uf == _codigo_para_uf(int(codigo))
            ).first()
            if estado:
                _upsert_indicador(db, estado.id, ano, "saude",
                                  "municipios_com_esgoto", valor, "municípios",
                                  "IBGE/SNIS T7463")
        db.commit()
        log.info("Saneamento coletado.")
    except Exception as e:
        log.error(f"Erro ao coletar saneamento: {e}")


# ──────────────────────────────────────────────────────────────
# SEGURANÇA
# ──────────────────────────────────────────────────────────────

def coletar_seguranca(db):
    log.info("Inserindo homicídios FBSP 2023...")
    for uf, valor in HOMICIDIOS_100K.items():
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if estado:
            _upsert_indicador(db, estado.id, 2023, "seguranca", "homicidios_100k",
                              valor, "por 100k hab.", "FBSP Anuário 2023")
    db.commit()
    log.info("Homicídios inseridos.")


# ──────────────────────────────────────────────────────────────
# SCORES — recalcula com dados reais normalizados
# ──────────────────────────────────────────────────────────────

def recalcular_scores(db):
    """
    Normaliza cada indicador para 0–100 e calcula score composto.

    Educação (40%):  IDEB normalizado (min=3.5, max=7.0)
    Saúde    (35%):  mortalidade infantil invertida (min=8, max=22)
    Segurança(25%):  homicídios invertidos (min=7, max=50)
    """
    log.info("Recalculando scores com dados reais normalizados...")

    def normalizar(valor, minv, maxv, invertido=False):
        if valor is None:
            return 50.0
        score = (valor - minv) / (maxv - minv) * 100
        score = max(0.0, min(100.0, score))
        return round(100 - score if invertido else score, 2)

    estados = db.query(models.Estado).all()
    for estado in estados:
        ideb = db.query(models.Indicador).filter(
            models.Indicador.estado_id == estado.id,
            models.Indicador.nome == "ideb_anos_finais",
        ).order_by(models.Indicador.ano.desc()).first()

        mort = db.query(models.Indicador).filter(
            models.Indicador.estado_id == estado.id,
            models.Indicador.nome == "mortalidade_infantil",
        ).order_by(models.Indicador.ano.desc()).first()

        hom = db.query(models.Indicador).filter(
            models.Indicador.estado_id == estado.id,
            models.Indicador.nome == "homicidios_100k",
        ).order_by(models.Indicador.ano.desc()).first()

        rend = db.query(models.Indicador).filter(
            models.Indicador.estado_id == estado.id,
            models.Indicador.nome == "rendimento_medio_mensal",
        ).order_by(models.Indicador.ano.desc()).first()

        edu_score = normalizar(ideb.valor if ideb else None, 3.5, 7.0)
        sau_score = normalizar(mort.valor if mort else None, 8.0, 22.0, invertido=True)
        seg_score = normalizar(hom.valor if hom else None, 7.0, 50.0, invertido=True)
        eco_score = normalizar(rend.valor if rend else None, 1500, 5000)

        score_geral = round(edu_score * 0.40 + sau_score * 0.35 + seg_score * 0.25, 2)

        existe = db.query(models.ScoreEstado).filter(
            models.ScoreEstado.estado_id == estado.id,
            models.ScoreEstado.ano == 2023,
        ).first()

        if existe:
            existe.educacao = edu_score
            existe.saude = sau_score
            existe.seguranca = seg_score
            existe.economia = eco_score
            existe.score_geral = score_geral
        else:
            db.add(models.ScoreEstado(
                estado_id=estado.id, ano=2023,
                educacao=edu_score, saude=sau_score,
                seguranca=seg_score, economia=eco_score,
                score_geral=score_geral,
            ))

    db.commit()
    log.info("Scores recalculados.")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def rodar_fase2():
    models.Base.metadata.create_all(bind=engine)
    db = _get_db()
    try:
        coletar_educacao(db)
        coletar_saude(db)
        coletar_seguranca(db)
        recalcular_scores(db)
        log.info("=== Fase 2 concluída com sucesso ===")
    except Exception as e:
        log.error(f"Erro na Fase 2: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_fase2()
