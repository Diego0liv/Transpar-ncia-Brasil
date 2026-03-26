"""
Pipeline Fase 3 — Dados Políticos.
Fontes: API da Câmara dos Deputados + API do Senado Federal.
"""

import os
import sys
import time
import requests
import logging
from datetime import date, datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CAMARA_API = "https://dadosabertos.camara.leg.br/api/v2"
SENADO_API = "https://legis.senado.leg.br/dadosabertos"

HEADERS_JSON = {"Accept": "application/json"}

# Aguarda entre requisições para não sobrecarregar as APIs
DELAY = 0.15


def _get(url, params=None, retries=3):
    for tentativa in range(retries):
        try:
            r = requests.get(url, params=params, headers=HEADERS_JSON, timeout=15)
            if r.status_code == 429:
                log.warning("Rate limit. Aguardando 5s...")
                time.sleep(5)
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if tentativa == retries - 1:
                log.error(f"Falha em {url}: {e}")
                return None
            time.sleep(1)
    return None


def _upsert_politico(db, dados: dict) -> Optional[models.Politico]:
    id_ext = dados.get("id_externo")
    existente = db.query(models.Politico).filter(
        models.Politico.id_externo == id_ext,
        models.Politico.cargo == dados.get("cargo"),
    ).first()
    if existente:
        for k, v in dados.items():
            setattr(existente, k, v)
        return existente
    else:
        p = models.Politico(**dados)
        db.add(p)
        return p


# ──────────────────────────────────────────────────────────────
# DEPUTADOS FEDERAIS
# ──────────────────────────────────────────────────────────────

def coletar_deputados(db, max_paginas=6):
    """
    Coleta deputados em exercício da 57ª legislatura (atual).
    max_paginas × 100 itens = até 600 deputados (total ~513).
    """
    log.info("Coletando deputados federais...")
    total = 0
    pagina = 1

    while pagina <= max_paginas:
        data = _get(f"{CAMARA_API}/deputados", params={
            "itens": 100, "pagina": pagina,
            "ordem": "ASC", "ordenarPor": "nome",
        })
        if not data or not data.get("dados"):
            break

        for dep in data["dados"]:
            _upsert_politico(db, {
                "id_externo": dep["id"],
                "nome":       dep["nome"],
                "partido":    dep.get("siglaPartido"),
                "uf":         dep.get("siglaUf"),
                "cargo":      "deputado_federal",
                "foto_url":   dep.get("urlFoto"),
                "email":      dep.get("email"),
                "ativo":      True,
            })
            total += 1

        # Verifica se há próxima página
        links = data.get("links", [])
        if not any(l["rel"] == "next" for l in links):
            break
        pagina += 1
        time.sleep(DELAY)

    db.commit()
    log.info(f"Deputados coletados: {total}")


# ──────────────────────────────────────────────────────────────
# SENADORES
# ──────────────────────────────────────────────────────────────

def coletar_senadores(db):
    log.info("Coletando senadores em exercício...")
    data = _get(f"{SENADO_API}/senador/lista/atual")
    if not data:
        log.error("Falha ao buscar senadores.")
        return

    parlamentares = (
        data.get("ListaParlamentarEmExercicio", {})
            .get("Parlamentares", {})
            .get("Parlamentar", [])
    )
    total = 0
    for s in parlamentares:
        ident = s.get("IdentificacaoParlamentar", {})
        mandato = s.get("Mandato", {})
        partido_atual = (
            mandato.get("PartidoAtual", {})
                   .get("NomePartido") or
            ident.get("SiglaPartidoParlamentar")
        )
        _upsert_politico(db, {
            "id_externo": int(ident.get("CodigoParlamentar", 0)),
            "nome":       ident.get("NomeParlamentar"),
            "partido":    partido_atual,
            "uf":         mandato.get("UfParlamentar"),
            "cargo":      "senador",
            "foto_url":   ident.get("UrlFotoParlamentar"),
            "email":      ident.get("EmailParlamentar"),
            "ativo":      True,
        })
        total += 1
        time.sleep(DELAY)

    db.commit()
    log.info(f"Senadores coletados: {total}")


# ──────────────────────────────────────────────────────────────
# VOTAÇÕES — últimas 200 votações da Câmara
# ──────────────────────────────────────────────────────────────

def coletar_votacoes_camara(db, max_paginas=2):
    """
    Coleta as votações mais recentes do Plenário da Câmara
    e registra o voto de cada deputado.
    """
    log.info("Coletando votações da Câmara...")
    total_votos = 0
    pagina = 1

    while pagina <= max_paginas:
        data = _get(f"{CAMARA_API}/votacoes", params={
            "itens": 20, "pagina": pagina,
            "ordem": "DESC", "ordenarPor": "dataHoraRegistro",
        })
        if not data or not data.get("dados"):
            break

        for votacao in data["dados"]:
            vid = votacao.get("id")
            if not vid:
                continue
            descricao = votacao.get("descricao") or votacao.get("proposicaoObjeto", "")
            data_str  = (votacao.get("dataHoraRegistro") or "")[:10]
            try:
                data_vot = datetime.strptime(data_str, "%Y-%m-%d").date() if data_str else None
            except ValueError:
                data_vot = None

            # Votos individuais
            votos_data = _get(f"{CAMARA_API}/votacoes/{vid}/votos")
            time.sleep(DELAY)
            if not votos_data:
                continue

            for voto in votos_data.get("dados", []):
                dep_info = voto.get("deputado_", {})
                id_ext   = dep_info.get("id")
                if not id_ext:
                    continue

                politico = db.query(models.Politico).filter(
                    models.Politico.id_externo == id_ext,
                    models.Politico.cargo == "deputado_federal",
                ).first()
                if not politico:
                    continue

                # Evita duplicata
                ja_existe = db.query(models.Votacao).filter(
                    models.Votacao.politico_id == politico.id,
                    models.Votacao.proposicao  == descricao[:499],
                    models.Votacao.data_votacao == data_vot,
                ).first()
                if not ja_existe:
                    db.add(models.Votacao(
                        politico_id  = politico.id,
                        data_votacao = data_vot,
                        proposicao   = descricao[:499],
                        voto         = voto.get("tipoVoto", "Desconhecido"),
                        fonte        = "Câmara dos Deputados",
                    ))
                    total_votos += 1

            time.sleep(DELAY)

        links = data.get("links", [])
        if not any(l["rel"] == "next" for l in links):
            break
        pagina += 1

    db.commit()
    log.info(f"Votos registrados: {total_votos}")


# ──────────────────────────────────────────────────────────────
# CALCULAR SCORE DE POLÍTICO
# ──────────────────────────────────────────────────────────────

def calcular_score_politicos(db):
    """
    Score baseado em:
    - Presença (% votos Sim/Não vs total de votações com presença registrada)
    - Atividade (nº de votações participadas)
    """
    log.info("Calculando scores dos políticos...")

    politicos = db.query(models.Politico).filter(models.Politico.ativo == True).all()
    total_votacoes_ref = db.query(models.Votacao.proposicao).distinct().count() or 1

    for pol in politicos:
        votos = db.query(models.Votacao).filter(models.Votacao.politico_id == pol.id).all()
        total = len(votos)
        if total == 0:
            pol.score_presenca  = None
            pol.score_atividade = 0.0
            continue

        presentes = sum(1 for v in votos if v.voto not in ("Faltou", "Art. 17", "-"))
        pol.score_presenca  = round((presentes / total) * 100, 1) if total else 0.0
        pol.score_atividade = round(min(total / max(total_votacoes_ref, 1) * 100, 100), 1)

    db.commit()
    log.info("Scores calculados.")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def rodar_fase3():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        coletar_deputados(db)
        coletar_senadores(db)
        coletar_votacoes_camara(db)
        calcular_score_politicos(db)
        log.info("=== Fase 3 concluída com sucesso ===")
    except Exception as e:
        log.error(f"Erro na Fase 3: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_fase3()
