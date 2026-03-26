from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from .database import engine, get_db
from . import models, schemas

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Transparência Brasil API",
    description="API de dados governamentais do Brasil — IBGE, Câmara e Portal da Transparência",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"projeto": "Transparência Brasil", "versao": "2.0.0", "docs": "/docs", "status": "online"}


@app.get("/estados", response_model=List[schemas.EstadoRankingSchema])
def listar_estados(regiao: Optional[str] = None, db: Session = Depends(get_db)):
    query = (
        db.query(
            models.Estado.uf,
            models.Estado.nome,
            models.Estado.regiao,
            models.ScoreEstado.educacao,
            models.ScoreEstado.saude,
            models.ScoreEstado.seguranca,
            models.ScoreEstado.economia,
            models.ScoreEstado.score_geral.label("score"),
        )
        .join(models.ScoreEstado, models.ScoreEstado.estado_id == models.Estado.id)
        .order_by(models.ScoreEstado.score_geral.desc())
    )
    if regiao:
        query = query.filter(models.Estado.regiao == regiao.upper())

    rows = query.all()
    return [
        schemas.EstadoRankingSchema(
            uf=r.uf, nome=r.nome, regiao=r.regiao,
            educacao=round(r.educacao or 0, 1),
            saude=round(r.saude or 0, 1),
            seguranca=round(r.seguranca or 0, 1),
            economia=round(r.economia or 0, 1),
            score=round(r.score or 0, 1),
        )
        for r in rows
    ]


@app.get("/estados/{uf}")
def detalhe_estado(uf: str, db: Session = Depends(get_db)):
    estado = db.query(models.Estado).filter(models.Estado.uf == uf.upper()).first()
    if not estado:
        raise HTTPException(status_code=404, detail=f"Estado '{uf}' não encontrado.")

    score = (
        db.query(models.ScoreEstado)
        .filter(models.ScoreEstado.estado_id == estado.id)
        .order_by(models.ScoreEstado.ano.desc())
        .first()
    )

    indicadores = (
        db.query(models.Indicador)
        .filter(models.Indicador.estado_id == estado.id)
        .order_by(models.Indicador.categoria, models.Indicador.ano.desc())
        .all()
    )

    ind_por_categoria = {}
    for i in indicadores:
        ind_por_categoria.setdefault(i.categoria, []).append({
            "nome": i.nome, "valor": i.valor,
            "unidade": i.unidade, "fonte": i.fonte, "ano": i.ano,
        })

    return {
        "uf": estado.uf,
        "nome": estado.nome,
        "regiao": estado.regiao,
        "capital": estado.capital,
        "score": {
            "geral": round(score.score_geral, 1) if score else None,
            "educacao": round(score.educacao, 1) if score else None,
            "saude": round(score.saude, 1) if score else None,
            "seguranca": round(score.seguranca, 1) if score else None,
            "economia": round(score.economia, 1) if score else None,
        },
        "indicadores": ind_por_categoria,
    }


@app.get("/indicadores/categoria/{categoria}")
def indicadores_por_categoria(categoria: str, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Estado.uf, models.Estado.nome, models.Estado.regiao,
                 models.Indicador.nome.label("indicador"),
                 models.Indicador.valor, models.Indicador.unidade, models.Indicador.ano)
        .join(models.Indicador, models.Indicador.estado_id == models.Estado.id)
        .filter(models.Indicador.categoria == categoria.lower())
        .order_by(models.Estado.uf, models.Indicador.ano.desc())
        .all()
    )
    return [
        {"uf": r.uf, "nome": r.nome, "regiao": r.regiao,
         "indicador": r.indicador, "valor": r.valor,
         "unidade": r.unidade, "ano": r.ano}
        for r in rows
    ]


@app.get("/comparar")
def comparar_estados(ufs: str, db: Session = Depends(get_db)):
    """
    Compara múltiplos estados. Exemplo: /comparar?ufs=SP,RJ,MG
    """
    lista_ufs = [u.strip().upper() for u in ufs.split(",") if u.strip()]
    if not lista_ufs:
        raise HTTPException(status_code=400, detail="Informe ao menos um UF.")

    resultado = []
    for uf in lista_ufs:
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if not estado:
            continue
        score = (
            db.query(models.ScoreEstado)
            .filter(models.ScoreEstado.estado_id == estado.id)
            .order_by(models.ScoreEstado.ano.desc())
            .first()
        )
        indicadores = (
            db.query(models.Indicador)
            .filter(models.Indicador.estado_id == estado.id)
            .order_by(models.Indicador.categoria, models.Indicador.ano.desc())
            .all()
        )
        resultado.append({
            "uf": estado.uf,
            "nome": estado.nome,
            "regiao": estado.regiao,
            "scores": {
                "geral": round(score.score_geral, 1) if score else None,
                "educacao": round(score.educacao, 1) if score else None,
                "saude": round(score.saude, 1) if score else None,
                "seguranca": round(score.seguranca, 1) if score else None,
                "economia": round(score.economia, 1) if score else None,
            },
            "indicadores": {i.nome: {"valor": i.valor, "unidade": i.unidade, "ano": i.ano}
                            for i in indicadores},
        })
    return resultado


@app.get("/resumo")
def resumo_nacional(db: Session = Depends(get_db)):
    total = db.query(models.Estado).count()
    scores = db.query(models.ScoreEstado).all()
    if not scores:
        return {"total_estados": total}

    medias = {
        "score_geral":  round(sum(s.score_geral for s in scores) / len(scores), 1),
        "educacao":     round(sum(s.educacao    for s in scores) / len(scores), 1),
        "saude":        round(sum(s.saude       for s in scores) / len(scores), 1),
        "seguranca":    round(sum(s.seguranca   for s in scores) / len(scores), 1),
        "economia":     round(sum(s.economia    for s in scores) / len(scores), 1),
    }
    melhor = db.query(models.Estado.nome, models.Estado.uf, models.ScoreEstado.score_geral) \
        .join(models.ScoreEstado, models.ScoreEstado.estado_id == models.Estado.id) \
        .order_by(models.ScoreEstado.score_geral.desc()).first()
    pior = db.query(models.Estado.nome, models.Estado.uf, models.ScoreEstado.score_geral) \
        .join(models.ScoreEstado, models.ScoreEstado.estado_id == models.Estado.id) \
        .order_by(models.ScoreEstado.score_geral.asc()).first()

    return {
        "total_estados": total,
        "medias_nacionais": medias,
        "melhor_estado": {"nome": melhor.nome, "uf": melhor.uf, "score": round(melhor.score_geral, 1)},
        "pior_estado":   {"nome": pior.nome,   "uf": pior.uf,   "score": round(pior.score_geral, 1)},
    }


@app.get("/politicos")
def listar_politicos(
    cargo: Optional[str] = None,
    uf: Optional[str] = None,
    partido: Optional[str] = None,
    busca: Optional[str] = None,
    ordem_presenca: Optional[str] = None,
    pagina: int = 1,
    itens: int = 50,
    db: Session = Depends(get_db),
):
    query = db.query(models.Politico).filter(models.Politico.ativo == 1)
    if cargo:   query = query.filter(models.Politico.cargo == cargo.lower())
    if uf:      query = query.filter(models.Politico.uf == uf.upper())
    if partido: query = query.filter(models.Politico.partido.ilike(f"%{partido}%"))
    if busca:   query = query.filter(models.Politico.nome.ilike(f"%{busca}%"))

    total = query.count()
    if ordem_presenca == 'asc':
        query = query.order_by(models.Politico.score_presenca.asc().nullslast(), models.Politico.nome)
    elif ordem_presenca == 'desc':
        query = query.order_by(models.Politico.score_presenca.desc().nullslast(), models.Politico.nome)
    else:
        query = query.order_by(models.Politico.nome)

    politicos = query.offset((pagina - 1) * itens).limit(itens).all()
    return {
        "total": total, "pagina": pagina, "itens": itens,
        "dados": [
            {"id": p.id, "nome": p.nome, "partido": p.partido, "uf": p.uf,
             "cargo": p.cargo, "foto_url": p.foto_url,
             "score_presenca":  p.score_presenca,
             "score_atividade": p.score_atividade,
             "score_geral":     round(p.score_geral, 1) if p.score_geral else None,
             "alinhamento_partido": p.alinhamento_partido,
             "alinhamento_governo": p.alinhamento_governo}
            for p in politicos
        ],
    }


@app.get("/governadores")
def listar_governadores(db: Session = Depends(get_db)):
    rows = db.query(models.Politico).filter(
        models.Politico.cargo == "governador",
        models.Politico.ativo == 1,
    ).order_by(models.Politico.uf).all()
    return [
        {"id": p.id, "nome": p.nome, "partido": p.partido,
         "uf": p.uf, "foto_url": p.foto_url}
        for p in rows
    ]


@app.get("/ministros")
def listar_ministros(db: Session = Depends(get_db)):
    rows = db.query(models.Politico).filter(
        models.Politico.cargo == "ministro",
        models.Politico.ativo == 1,
    ).order_by(models.Politico.nome).all()
    return [
        {
            "id": p.id,
            "nome": p.nome,
            "partido": p.partido,
            "ministerio": p.ministerio,
            "foto_url": p.foto_url,
            "orcamento_bi": p.score_atividade,
            "execucao_pct": p.score_presenca,
            "destaques": p.destaques,
        }
        for p in rows
    ]


@app.get("/presidentes")
def listar_presidentes(db: Session = Depends(get_db)):
    rows = db.query(models.Politico).filter(
        models.Politico.cargo == "presidente"
    ).order_by(models.Politico.ano_inicio.asc()).all()
    return [
        {"id": p.id, "nome": p.nome, "partido": p.partido, "uf": p.uf,
         "ano_inicio": p.ano_inicio,
         "ano_fim":    p.ano_fim,
         "bio": p.email, "ativo": bool(p.ativo)}
        for p in rows
    ]


@app.get("/historico/{uf}")
def historico_estado(uf: str, indicador: str = "ideb_anos_finais", db: Session = Depends(get_db)):
    estado = db.query(models.Estado).filter(models.Estado.uf == uf.upper()).first()
    if not estado:
        raise HTTPException(status_code=404, detail="Estado não encontrado.")
    rows = db.query(models.Indicador).filter(
        models.Indicador.estado_id == estado.id,
        models.Indicador.nome      == indicador,
    ).order_by(models.Indicador.ano).all()
    return {
        "uf": estado.uf, "nome": estado.nome, "indicador": indicador,
        "serie": [{"ano": r.ano, "valor": r.valor, "unidade": r.unidade} for r in rows],
    }


@app.get("/historico/comparar/estados")
def historico_comparar(ufs: str, indicador: str = "ideb_anos_finais", db: Session = Depends(get_db)):
    lista_ufs = [u.strip().upper() for u in ufs.split(",") if u.strip()]
    resultado = []
    for uf in lista_ufs:
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if not estado: continue
        rows = db.query(models.Indicador).filter(
            models.Indicador.estado_id == estado.id,
            models.Indicador.nome      == indicador,
        ).order_by(models.Indicador.ano).all()
        resultado.append({
            "uf": estado.uf, "nome": estado.nome,
            "serie": [{"ano": r.ano, "valor": r.valor} for r in rows],
        })
    return resultado


@app.get("/politicos/{id}")
def detalhe_politico(id: int, db: Session = Depends(get_db)):
    pol = db.query(models.Politico).filter(models.Politico.id == id).first()
    if not pol:
        raise HTTPException(status_code=404, detail="Político não encontrado.")

    votos = (
        db.query(models.Votacao)
        .filter(models.Votacao.politico_id == pol.id)
        .order_by(models.Votacao.data_votacao.desc())
        .limit(50)
        .all()
    )

    # Contagem por tipo de voto
    contagem: dict = {}
    for v in votos:
        contagem[v.voto] = contagem.get(v.voto, 0) + 1

    # Classificar score
    sg = pol.score_geral or 0
    if sg >= 8:   prod = ("Alta", "🟢")
    elif sg >= 5: prod = ("Média", "🟡")
    else:         prod = ("Baixa", "🔴")

    pres = pol.score_presenca or 0
    if pres >= 85:  pres_label = ("Alta", "🟢")
    elif pres >= 60: pres_label = ("Média", "🟡")
    else:            pres_label = ("Baixa", "🔴")

    # Tags inteligentes
    tags = []
    if sg >= 8:                                       tags.append("Alto desempenho")
    if pol.alinhamento_partido and pol.alinhamento_partido >= 85: tags.append("Alinhado ao partido")
    if pol.alinhamento_partido and pol.alinhamento_partido < 60:  tags.append("Voto independente")
    if pres >= 90:                                    tags.append("Presença exemplar")
    if pres < 60:                                     tags.append("Alta ausência")
    if pol.alinhamento_governo and pol.alinhamento_governo >= 80: tags.append("Pró-governo")
    if pol.alinhamento_governo and pol.alinhamento_governo < 40:  tags.append("Oposição firme")

    return {
        "id": pol.id,
        "nome": pol.nome,
        "partido": pol.partido,
        "uf": pol.uf,
        "cargo": pol.cargo,
        "foto_url": pol.foto_url,
        "scores": {
            "geral":              round(sg, 1),
            "presenca":           pol.score_presenca,
            "atividade":          int(pol.score_atividade or 0),
            "alinhamento_partido": pol.alinhamento_partido,
            "alinhamento_governo": pol.alinhamento_governo,
        },
        "classificacao": {
            "produtividade": {"label": prod[0], "icone": prod[1]},
            "presenca":      {"label": pres_label[0], "icone": pres_label[1]},
        },
        "tags": tags,
        "resumo_votos": contagem,
        "ultimas_votacoes": [
            {"data": str(v.data_votacao), "proposicao": v.proposicao, "voto": v.voto}
            for v in votos
        ],
    }


@app.get("/stf")
def listar_stf(db: Session = Depends(get_db)):
    rows = db.query(models.Politico).filter(
        models.Politico.cargo == "ministro_stf",
        models.Politico.ativo == 1,
    ).order_by(models.Politico.ano_inicio.asc()).all()
    return [
        {
            "id":                p.id,
            "nome":              p.nome,
            "indicado_por":      p.partido,
            "ano_posse":         p.ano_inicio,
            "foto_url":          p.foto_url,
            "score_geral":       round(p.score_geral, 1) if p.score_geral else None,
            "processos_julgados":int(p.score_atividade or 0),
            "acompanha_maioria": p.score_presenca,
            "perfil_garantista": round(100 - (p.alinhamento_partido or 0), 1),
            "casos_destaque":    p.destaques,
            "bio":               p.email,
            "poder":             "judiciario",
        }
        for p in rows
    ]



@app.get("/comparar/politicos")
def comparar_politicos(ids: str, db: Session = Depends(get_db)):
    """Compara 2-4 políticos lado a lado. Ex: /politicos/comparar/lado-a-lado?ids=1,2,3"""
    lista_ids = [int(i) for i in ids.split(",") if i.strip().isdigit()][:4]
    resultado = []
    for pid in lista_ids:
        pol = db.query(models.Politico).filter(models.Politico.id == pid).first()
        if not pol: continue
        resultado.append({
            "id": pol.id,
            "nome": pol.nome,
            "partido": pol.partido,
            "uf": pol.uf,
            "cargo": pol.cargo,
            "foto_url": pol.foto_url,
            "score_geral":           round(pol.score_geral or 0, 1),
            "score_presenca":        pol.score_presenca,
            "score_atividade":       int(pol.score_atividade or 0),
            "alinhamento_partido":   pol.alinhamento_partido,
            "alinhamento_governo":   pol.alinhamento_governo,
        })
    return resultado


@app.get("/ranking/politicos")
def ranking_politicos(
    cargo: Optional[str] = None,
    uf: Optional[str] = None,
    itens: int = 50,
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Politico)
        .filter(
            models.Politico.ativo == 1,
            models.Politico.score_presenca.isnot(None),
        )
    )
    if cargo:
        query = query.filter(models.Politico.cargo == cargo.lower())
    if uf:
        query = query.filter(models.Politico.uf == uf.upper())

    politicos = query.order_by(models.Politico.score_presenca.desc()).limit(itens).all()

    return [
        {
            "posicao": i + 1,
            "id": p.id,
            "nome": p.nome,
            "partido": p.partido,
            "uf": p.uf,
            "cargo": p.cargo,
            "foto_url": p.foto_url,
            "score_presenca": p.score_presenca,
            "score_atividade": p.score_atividade,
        }
        for i, p in enumerate(politicos)
    ]


@app.get("/partidos/resumo")
def resumo_partidos(db: Session = Depends(get_db)):
    from sqlalchemy import func
    rows = (
        db.query(
            models.Politico.partido,
            func.count(models.Politico.id).label("total"),
            func.avg(models.Politico.score_presenca).label("media_presenca"),
        )
        .filter(models.Politico.ativo == 1, models.Politico.partido.isnot(None))
        .group_by(models.Politico.partido)
        .order_by(func.count(models.Politico.id).desc())
        .all()
    )
    return [
        {
            "partido": r.partido,
            "total_parlamentares": r.total,
            "media_presenca": round(r.media_presenca, 1) if r.media_presenca else None,
        }
        for r in rows
    ]


@app.get("/health")
def health():
    return {"status": "ok"}


# ── MUNICÍPIOS (Fase 4) ──────────────────────────────────────────────

@app.get("/municipios", response_model=dict)
def listar_municipios(
    uf:     Optional[str] = None,
    busca:  Optional[str] = None,
    regiao: Optional[str] = None,
    ordem:  str = "score",
    pagina: int = 1,
    itens:  int = 24,
    db: Session = Depends(get_db),
):
    q = db.query(models.Municipio)
    if uf:
        q = q.filter(models.Municipio.uf == uf.upper())
    if regiao:
        q = q.filter(models.Municipio.regiao == regiao.upper())
    if busca:
        q = q.filter(models.Municipio.nome.ilike(f"%{busca}%"))
    if ordem == "nome":
        q = q.order_by(models.Municipio.nome)
    elif ordem == "populacao":
        q = q.order_by(models.Municipio.populacao.desc().nullslast())
    else:
        q = q.order_by(models.Municipio.score.desc().nullslast())

    total   = q.count()
    offset  = (pagina - 1) * itens
    dados   = q.offset(offset).limit(itens).all()
    return {
        "total":   total,
        "pagina":  pagina,
        "itens":   itens,
        "paginas": (total + itens - 1) // itens,
        "dados":   [schemas.MunicipioOut.from_orm(m) for m in dados],
    }


@app.get("/municipios/ranking", response_model=List[schemas.MunicipioOut])
def ranking_municipios(
    uf:    Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(models.Municipio).filter(models.Municipio.score.isnot(None))
    if uf:
        q = q.filter(models.Municipio.uf == uf.upper())
    return q.order_by(models.Municipio.score.desc()).limit(limit).all()


@app.get("/municipios/estado/{uf}", response_model=List[schemas.MunicipioOut])
def municipios_por_estado(uf: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Municipio)
        .filter(models.Municipio.uf == uf.upper())
        .order_by(models.Municipio.score.desc())
        .all()
    )


@app.get("/municipios/{municipio_id}", response_model=schemas.MunicipioOut)
def detalhe_municipio(municipio_id: int, db: Session = Depends(get_db)):
    m = db.query(models.Municipio).filter(models.Municipio.id == municipio_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Município não encontrado")
    return m
