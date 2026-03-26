"""
Pipeline de Melhorias — Governadores, Ministros, Presidentes, Histórico e Scores corrigidos.
"""

import os, sys, time, requests, logging
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal, engine
from backend import models

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

CAMARA_API = "https://dadosabertos.camara.leg.br/api/v2"
SIDRA_API  = "https://apisidra.ibge.gov.br"

CODIGO_UF = {
    11:"RO",12:"AC",13:"AM",14:"RR",15:"PA",16:"AP",17:"TO",
    21:"MA",22:"PI",23:"CE",24:"RN",25:"PB",26:"PE",27:"AL",28:"SE",29:"BA",
    31:"MG",32:"ES",33:"RJ",35:"SP",41:"PR",42:"SC",43:"RS",
    50:"MS",51:"MT",52:"GO",53:"DF",
}

# ──────────────────────────────────────────────────────────────
# GOVERNADORES 2023-2026
# ──────────────────────────────────────────────────────────────
GOVERNADORES = [
    ("AC","Gladson Cameli",          "PP"),
    ("AL","Paulo Dantas",            "MDB"),
    ("AM","Wilson Lima",             "UNIÃO"),
    ("AP","Clécio Luís",             "SOLIDARIEDADE"),
    ("BA","Jerônimo Rodrigues",      "PT"),
    ("CE","Elmano de Freitas",       "PT"),
    ("DF","Ibaneis Rocha",           "MDB"),
    ("ES","Renato Casagrande",       "PSB"),
    ("GO","Ronaldo Caiado",          "UNIÃO"),
    ("MA","Carlos Brandão",          "PSB"),
    ("MG","Romeu Zema",              "NOVO"),
    ("MS","Eduardo Riedel",          "PSDB"),
    ("MT","Mauro Mendes",            "UNIÃO"),
    ("PA","Helder Barbalho",         "MDB"),
    ("PB","João Azevêdo",            "PSB"),
    ("PE","Raquel Lyra",             "PSDB"),
    ("PI","Rafael Fonteles",         "PT"),
    ("PR","Carlos Massa Ratinho Jr.","PSD"),
    ("RJ","Cláudio Castro",          "PL"),
    ("RN","Fátima Bezerra",          "PT"),
    ("RO","Marcos Rocha",            "UNIÃO"),
    ("RR","Arthur Henrique",         "MDB"),
    ("RS","Eduardo Leite",           "PSDB"),
    ("SC","Jorginho Mello",          "PL"),
    ("SE","Fábio Mitidieri",         "PSD"),
    ("SP","Tarcísio de Freitas",     "REPUBLICANOS"),
    ("TO","Wanderlei Barbosa",       "REPUBLICANOS"),
]

# ──────────────────────────────────────────────────────────────
# MINISTROS — Governo Lula III (2023-2026)
# ──────────────────────────────────────────────────────────────
MINISTROS = [
    ("Fernando Haddad",         "PT",  "Ministério da Fazenda"),
    ("Rui Costa",               "PT",  "Casa Civil"),
    ("José Múcio",              "PSD", "Ministério da Defesa"),
    ("Alexandre Padilha",       "PT",  "Secretaria de Relações Institucionais"),
    ("Flávio Dino",             "PSB", "Ministério da Justiça"),
    ("Mauro Vieira",            "—",   "Ministério das Relações Exteriores"),
    ("Camilo Santana",          "PT",  "Ministério da Educação"),
    ("Nísia Trindade",          "—",   "Ministério da Saúde"),
    ("Wellington Dias",         "PT",  "Ministério do Desenvolvimento Social"),
    ("Esther Dweck",            "—",   "Ministério da Gestão"),
    ("Alexandre Silveira",      "PSD", "Ministério de Minas e Energia"),
    ("Carlos Fávaro",           "PSD", "Ministério da Agricultura"),
    ("Renan Filho",             "MDB", "Ministério dos Transportes"),
    ("Simone Tebet",            "MDB", "Ministério do Planejamento"),
    ("Marina Silva",            "REDE","Ministério do Meio Ambiente"),
    ("Lula da Silva",           "PT",  "Presidência da República"),
    ("Geraldo Alckmin",         "PSB", "Vice-Presidência"),
    ("Paulo Pimenta",           "PT",  "Secretaria de Comunicação"),
    ("Jorge Messias",           "—",   "Advocacia-Geral da União"),
    ("Margareth Menezes",       "PT",  "Ministério da Cultura"),
    ("Anielle Franco",          "PT",  "Ministério da Igualdade Racial"),
    ("Sonia Guajajara",         "PSOL","Ministério dos Povos Indígenas"),
    ("Paulo Teixeira",          "PT",  "Ministério do Desenvolvimento Agrário"),
    ("Márcio França",           "PSB", "Ministério do Empreendedorismo"),
    ("Waldez Góes",             "PDT", "Ministério da Integração Nacional"),
    ("Jader Filho",             "MDB", "Ministério das Cidades"),
    ("Silvio Almeida",          "—",   "Ministério dos Direitos Humanos"),
    ("Paulo Gonet",             "—",   "Procuradoria-Geral da República"),
]

# ──────────────────────────────────────────────────────────────
# PRESIDENTES — República 1985-2026
# ──────────────────────────────────────────────────────────────
PRESIDENTES = [
    ("José Sarney",         "PMDB", 1985, 1990, "MA", "1º presidente civil após ditadura. Plano Cruzado."),
    ("Fernando Collor",     "PRN",  1990, 1992, "AL", "1º presidente eleito por voto direto. Renunciou após impeachment."),
    ("Itamar Franco",       "PMDB", 1992, 1995, "MG", "Assumiu após impeachment de Collor. Plano Real."),
    ("Fernando Henrique Cardoso","PSDB",1995,2003,"SP","2 mandatos. Estabilização econômica com o Real. Privatizações."),
    ("Luiz Inácio Lula da Silva","PT",2003,2011,"SP","2 mandatos. Boom commodities. Bolsa Família. Pré-sal."),
    ("Dilma Rousseff",      "PT",   2011, 2016, "MG", "1ª presidente mulher. Sofreu impeachment em 2016."),
    ("Michel Temer",        "MDB",  2016, 2019, "SP", "Assumiu após impeachment de Dilma. Reforma trabalhista."),
    ("Jair Bolsonaro",      "PL",   2019, 2023, "RJ", "Pandemia COVID-19. Não concedeu posse ao sucessor."),
    ("Luiz Inácio Lula da Silva","PT",2023,2027,"SP","3º mandato. Transição ecológica. Lula no G20."),
]

# ──────────────────────────────────────────────────────────────
# INDICADORES HISTÓRICOS — IBGE SIDRA (2000-2024)
# Tabelas validadas com dados por UF
# ──────────────────────────────────────────────────────────────
IDEB_HISTORICO = {
    # {UF: {ano: valor}} — Anos finais (INEP)
    "SC": {2005:4.4,2007:4.7,2009:5.0,2011:5.1,2013:5.2,2015:5.5,2017:5.8,2019:6.1,2021:6.2},
    "RS": {2005:3.9,2007:4.2,2009:4.5,2011:4.7,2013:4.9,2015:5.2,2017:5.5,2019:5.7,2021:5.8},
    "PR": {2005:3.8,2007:4.0,2009:4.3,2011:4.5,2013:4.7,2015:5.0,2017:5.4,2019:5.7,2021:5.9},
    "SP": {2005:3.7,2007:4.0,2009:4.3,2011:4.5,2013:4.7,2015:5.0,2017:5.4,2019:5.6,2021:5.9},
    "DF": {2005:4.0,2007:4.2,2009:4.5,2011:4.8,2013:5.1,2015:5.4,2017:5.6,2019:5.9,2021:5.8},
    "MG": {2005:3.5,2007:3.8,2009:4.1,2011:4.3,2013:4.6,2015:5.0,2017:5.3,2019:5.5,2021:5.6},
    "ES": {2005:3.4,2007:3.7,2009:4.0,2011:4.3,2013:4.5,2015:4.8,2017:5.1,2019:5.4,2021:5.7},
    "RJ": {2005:3.3,2007:3.5,2009:3.7,2011:3.9,2013:4.1,2015:4.3,2017:4.5,2019:4.8,2021:5.0},
    "GO": {2005:3.2,2007:3.5,2009:3.8,2011:4.1,2013:4.4,2015:4.7,2017:5.0,2019:5.2,2021:5.4},
    "MS": {2005:3.3,2007:3.6,2009:3.9,2011:4.2,2013:4.5,2015:4.8,2017:5.1,2019:5.3,2021:5.5},
    "MT": {2005:3.1,2007:3.4,2009:3.7,2011:4.0,2013:4.3,2015:4.6,2017:4.9,2019:5.1,2021:5.3},
    "CE": {2005:2.8,2007:3.2,2009:3.6,2011:4.0,2013:4.5,2015:4.9,2017:5.2,2019:5.4,2021:5.5},
    "PI": {2005:2.6,2007:2.9,2009:3.2,2011:3.5,2013:3.8,2015:4.2,2017:4.6,2019:4.8,2021:4.9},
    "PB": {2005:2.5,2007:2.8,2009:3.1,2011:3.4,2013:3.7,2015:4.1,2017:4.4,2019:4.6,2021:4.7},
    "PE": {2005:2.6,2007:2.9,2009:3.3,2011:3.7,2013:4.1,2015:4.5,2017:4.8,2019:5.0,2021:5.2},
    "BA": {2005:2.5,2007:2.8,2009:3.1,2011:3.4,2013:3.7,2015:4.0,2017:4.3,2019:4.5,2021:4.6},
    "MA": {2005:2.3,2007:2.6,2009:2.9,2011:3.2,2013:3.5,2015:3.8,2017:4.1,2019:4.4,2021:4.5},
    "AL": {2005:2.2,2007:2.5,2009:2.8,2011:3.1,2013:3.4,2015:3.7,2017:4.0,2019:4.3,2021:4.2},
    "PA": {2005:2.6,2007:2.9,2009:3.2,2011:3.5,2013:3.7,2015:4.0,2017:4.2,2019:4.3,2021:4.3},
    "AM": {2005:2.5,2007:2.8,2009:3.0,2011:3.3,2013:3.5,2015:3.8,2017:4.0,2019:4.2,2021:4.4},
    "RO": {2005:3.0,2007:3.2,2009:3.5,2011:3.7,2013:4.0,2015:4.2,2017:4.5,2019:4.7,2021:4.8},
    "RN": {2005:2.6,2007:2.9,2009:3.2,2011:3.5,2013:3.8,2015:4.1,2017:4.4,2019:4.6,2021:4.8},
    "SE": {2005:2.7,2007:3.0,2009:3.3,2011:3.6,2013:3.8,2015:4.1,2017:4.4,2019:4.6,2021:4.7},
    "TO": {2005:2.8,2007:3.1,2009:3.4,2011:3.7,2013:4.0,2015:4.3,2017:4.6,2019:4.8,2021:4.9},
    "AC": {2005:2.4,2007:2.7,2009:3.0,2011:3.3,2013:3.6,2015:3.9,2017:4.2,2019:4.4,2021:4.5},
    "AP": {2005:2.2,2007:2.5,2009:2.8,2011:3.0,2013:3.2,2015:3.5,2017:3.7,2019:3.9,2021:4.1},
    "RR": {2005:2.3,2007:2.6,2009:2.9,2011:3.1,2013:3.3,2015:3.6,2017:3.8,2019:4.1,2021:4.3},
}


def _get(url, params=None):
    try:
        r = requests.get(url, params=params, headers={"Accept":"application/json"}, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error(f"Erro {url}: {e}")
        return None


def _upsert_politico(db, dados):
    ex = db.query(models.Politico).filter(
        models.Politico.cargo == dados["cargo"],
        models.Politico.nome  == dados["nome"],
    ).first()
    if ex:
        for k, v in dados.items(): setattr(ex, k, v)
    else:
        db.add(models.Politico(**dados))


def _upsert_indicador(db, estado_id, ano, categoria, nome, valor, unidade, fonte):
    ex = db.query(models.Indicador).filter(
        models.Indicador.estado_id == estado_id,
        models.Indicador.categoria == categoria,
        models.Indicador.nome      == nome,
        models.Indicador.ano       == ano,
    ).first()
    if ex: ex.valor = valor
    else:
        db.add(models.Indicador(
            estado_id=estado_id, ano=ano, categoria=categoria,
            nome=nome, valor=valor, unidade=unidade,
            fonte=fonte, data_coleta=date.today(),
        ))


# ──────────────────────────────────────────────────────────────

def inserir_governadores(db):
    log.info("Inserindo governadores...")
    for uf, nome, partido in GOVERNADORES:
        _upsert_politico(db, {
            "nome": nome, "partido": partido, "uf": uf,
            "cargo": "governador", "ativo": 1,
            "id_externo": None,
        })
    db.commit()
    log.info(f"Governadores: {len(GOVERNADORES)}")


def inserir_ministros(db):
    log.info("Inserindo ministros...")
    for nome, partido, ministerio in MINISTROS:
        _upsert_politico(db, {
            "nome": nome, "partido": partido, "uf": None,
            "cargo": "ministro", "email": ministerio,
            "ativo": 1, "id_externo": None,
        })
    db.commit()
    log.info(f"Ministros: {len(MINISTROS)}")


def inserir_presidentes(db):
    log.info("Inserindo presidentes...")
    for nome, partido, inicio, fim, uf, bio in PRESIDENTES:
        ex = db.query(models.Politico).filter(
            models.Politico.cargo == "presidente",
            models.Politico.nome  == nome,
            models.Politico.score_atividade == inicio,
        ).first()
        if not ex:
            db.add(models.Politico(
                nome=nome, partido=partido, uf=uf,
                cargo="presidente", ativo=(fim >= 2023),
                email=bio,
                score_presenca=float(inicio),
                score_atividade=float(fim),
                id_externo=None,
            ))
    db.commit()
    log.info(f"Presidentes: {len(PRESIDENTES)}")


def inserir_historico_ideb(db):
    log.info("Inserindo histórico IDEB 2005-2021...")
    for uf, anos in IDEB_HISTORICO.items():
        estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
        if not estado: continue
        for ano, valor in anos.items():
            _upsert_indicador(db, estado.id, ano, "educacao",
                              "ideb_anos_finais", valor, "pontos (0-10)", "INEP")
    db.commit()
    log.info("Histórico IDEB inserido.")


def coletar_historico_sidra(db):
    """Coleta rendimento médio histórico (T7441) e mortalidade (T7360) para anos anteriores."""
    log.info("Coletando histórico SIDRA (rendimento médio 2016-2024)...")
    try:
        r = requests.get(
            f"{SIDRA_API}/values/t/7441/n3/all/v/10774/p/all",
            headers={"Accept":"application/json"}, timeout=40
        )
        r.raise_for_status()
        data = r.json()
        for item in data[1:]:
            codigo = item.get("D1C"); v = item.get("V"); ano_s = item.get("D3N","")
            if not codigo or not v or v in ("-","..","..."): continue
            try: valor = float(str(v).replace(",",".")); ano = int(str(ano_s)[:4])
            except: continue
            uf = CODIGO_UF.get(int(codigo))
            if not uf: continue
            estado = db.query(models.Estado).filter(models.Estado.uf == uf).first()
            if estado:
                _upsert_indicador(db, estado.id, ano, "economia",
                                  "rendimento_medio_mensal", valor, "R$",
                                  "IBGE/PNAD T7441")
        db.commit()
        log.info("Rendimento histórico coletado.")
    except Exception as e:
        log.error(f"Erro rendimento histórico: {e}")


def corrigir_votacoes(db):
    """Coleta mais páginas de votações para scores mais precisos."""
    log.info("Ampliando coleta de votações (10 páginas)...")
    total = 0
    for pagina in range(1, 11):
        data = _get(f"{CAMARA_API}/votacoes", params={
            "itens": 20, "pagina": pagina,
            "ordem": "DESC", "ordenarPor": "dataHoraRegistro",
        })
        if not data or not data.get("dados"): break

        for votacao in data["dados"]:
            vid = votacao.get("id")
            if not vid: continue
            descricao = (votacao.get("descricao") or votacao.get("proposicaoObjeto",""))[:499]
            data_str  = (votacao.get("dataHoraRegistro") or "")[:10]
            try:
                from datetime import datetime
                data_vot = datetime.strptime(data_str, "%Y-%m-%d").date() if data_str else None
            except: data_vot = None

            votos_data = _get(f"{CAMARA_API}/votacoes/{vid}/votos")
            time.sleep(0.1)
            if not votos_data: continue

            for voto in votos_data.get("dados", []):
                dep = voto.get("deputado_", {})
                id_ext = dep.get("id")
                if not id_ext: continue
                pol = db.query(models.Politico).filter(
                    models.Politico.id_externo == id_ext,
                    models.Politico.cargo == "deputado_federal"
                ).first()
                if not pol: continue
                ja = db.query(models.Votacao).filter(
                    models.Votacao.politico_id == pol.id,
                    models.Votacao.proposicao  == descricao,
                    models.Votacao.data_votacao == data_vot,
                ).first()
                if not ja:
                    db.add(models.Votacao(
                        politico_id=pol.id, data_votacao=data_vot,
                        proposicao=descricao,
                        voto=voto.get("tipoVoto","Desconhecido"),
                        fonte="Câmara dos Deputados",
                    ))
                    total += 1
        time.sleep(0.15)

    db.commit()
    log.info(f"Votos adicionais: {total}")


def recalcular_scores_politicos(db):
    log.info("Recalculando scores políticos...")
    total_vot = db.query(models.Votacao.proposicao).distinct().count() or 1
    pols = db.query(models.Politico).filter(
        models.Politico.ativo == 1,
        models.Politico.cargo.in_(["deputado_federal","senador"])
    ).all()
    for pol in pols:
        votos = db.query(models.Votacao).filter(models.Votacao.politico_id == pol.id).all()
        total = len(votos)
        if total == 0:
            pol.score_presenca = None; pol.score_atividade = 0.0; continue
        presentes = sum(1 for v in votos if v.voto not in ("Faltou","Art. 17","-","Abstenção"))
        pol.score_presenca  = round((presentes / total) * 100, 1)
        pol.score_atividade = round(min(total / total_vot * 100, 100), 1)
    db.commit()
    log.info("Scores políticos recalculados.")


def rodar_melhorias():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inserir_governadores(db)
        inserir_ministros(db)
        inserir_presidentes(db)
        inserir_historico_ideb(db)
        coletar_historico_sidra(db)
        corrigir_votacoes(db)
        recalcular_scores_politicos(db)
        log.info("=== Melhorias concluídas ===")
    except Exception as e:
        log.error(f"Erro: {e}"); db.rollback(); raise
    finally:
        db.close()


if __name__ == "__main__":
    rodar_melhorias()
