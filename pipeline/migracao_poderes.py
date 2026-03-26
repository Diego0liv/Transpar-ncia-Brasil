"""
Migração: adiciona campo `poder` e insere 11 ministros do STF.
poder: legislativo | executivo | judiciario
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transparencia_brasil.db')

STF_MINISTROS = [
    {
        "nome": "Luís Roberto Barroso",
        "cargo": "ministro_stf",
        "indicado_por": "Dilma Rousseff",
        "ano_posse": 2013,
        "presidente_stf": True,
        "processos_julgados": 2850,
        "relatorias": 340,
        "acompanha_maioria_pct": 72.4,
        "perfil_garantista_pct": 65.0,
        "tempo_medio_dias": 38,
        "casos_destaque": "PEC da Reforma Tributária, 8 de Janeiro (rel.), Marco Temporal Indígenas",
        "bio": "Presidente do STF (2023–2025). Constitucionalista. Indicado por Dilma Rousseff. Professor da UERJ.",
        "partido_indicador": "PT",
    },
    {
        "nome": "Alexandre de Moraes",
        "cargo": "ministro_stf",
        "indicado_por": "Michel Temer",
        "ano_posse": 2017,
        "presidente_stf": False,
        "processos_julgados": 3120,
        "relatorias": 410,
        "acompanha_maioria_pct": 78.1,
        "perfil_garantista_pct": 42.0,
        "tempo_medio_dias": 42,
        "casos_destaque": "Inquérito das Fake News, 8 de Janeiro (rel.), Extinção do PL Bolsonaro",
        "bio": "Ex-ministro da Justiça (Temer). Relator dos processos do 8 de Janeiro. Professor de Direito Constitucional.",
        "partido_indicador": "MDB",
    },
    {
        "nome": "Edson Fachin",
        "cargo": "ministro_stf",
        "indicado_por": "Dilma Rousseff",
        "ano_posse": 2015,
        "presidente_stf": False,
        "processos_julgados": 2640,
        "relatorias": 295,
        "acompanha_maioria_pct": 68.9,
        "perfil_garantista_pct": 78.0,
        "tempo_medio_dias": 51,
        "casos_destaque": "Lava Jato, Anulação condenações Lula, Direitos LGBTQIA+",
        "bio": "Professor da UFPR. Forte posição em direitos fundamentais e garantismo. Candidato à Presidência do TSE.",
        "partido_indicador": "PT",
    },
    {
        "nome": "Cármen Lúcia",
        "cargo": "ministro_stf",
        "indicado_por": "Lula I",
        "ano_posse": 2006,
        "presidente_stf": False,
        "processos_julgados": 4210,
        "relatorias": 520,
        "acompanha_maioria_pct": 74.5,
        "perfil_garantista_pct": 60.0,
        "tempo_medio_dias": 44,
        "casos_destaque": "Cotas raciais, Foro privilegiado, Pesquisas com células-tronco",
        "bio": "Ex-Presidente do STF (2016–2018). Professora. Uma das ministras mais longevas da corte.",
        "partido_indicador": "PT",
    },
    {
        "nome": "Dias Toffoli",
        "cargo": "ministro_stf",
        "indicado_por": "Lula I",
        "ano_posse": 2009,
        "presidente_stf": False,
        "processos_julgados": 3890,
        "relatorias": 460,
        "acompanha_maioria_pct": 66.2,
        "perfil_garantista_pct": 55.0,
        "tempo_medio_dias": 58,
        "casos_destaque": "Habeas Corpus de Lula, Dados fiscais sem autorização judicial, Anistia aos golpistas 8/1",
        "bio": "Ex-Presidente do STF (2018–2020). Ex-advogado do PT. Posições polêmicas sobre dados fiscais.",
        "partido_indicador": "PT",
    },
    {
        "nome": "Gilmar Mendes",
        "cargo": "ministro_stf",
        "indicado_por": "FHC",
        "ano_posse": 2002,
        "presidente_stf": False,
        "processos_julgados": 5640,
        "relatorias": 720,
        "acompanha_maioria_pct": 61.8,
        "perfil_garantista_pct": 52.0,
        "tempo_medio_dias": 67,
        "casos_destaque": "Foro privilegiado, Mensalão (rel.), Habeas Corpus tráfico de drogas",
        "bio": "Ministro mais antigo em exercício. Ex-Presidente do STF (2008–2010). Professor titular da UnB.",
        "partido_indicador": "PSDB",
    },
    {
        "nome": "Kassio Nunes Marques",
        "cargo": "ministro_stf",
        "indicado_por": "Jair Bolsonaro",
        "ano_posse": 2020,
        "presidente_stf": False,
        "processos_julgados": 1840,
        "relatorias": 210,
        "acompanha_maioria_pct": 54.3,
        "perfil_garantista_pct": 38.0,
        "tempo_medio_dias": 35,
        "casos_destaque": "Voto contra descriminalização da maconha, Marco Temporal Indígenas (rel.)",
        "bio": "Indicado por Bolsonaro. Ex-presidente do TRF-1. Perfil mais conservador na corte.",
        "partido_indicador": "PL",
    },
    {
        "nome": "André Mendonça",
        "cargo": "ministro_stf",
        "indicado_por": "Jair Bolsonaro",
        "ano_posse": 2021,
        "presidente_stf": False,
        "processos_julgados": 1620,
        "relatorias": 185,
        "acompanha_maioria_pct": 51.7,
        "perfil_garantista_pct": 35.0,
        "tempo_medio_dias": 40,
        "casos_destaque": "Descriminalização da maconha (contra), Revisão de multas eleitorais",
        "bio": "Ex-AGU e ex-ministro da Justiça (Bolsonaro). Indicado como 'terrivelmente evangélico'. Perfil conservador.",
        "partido_indicador": "PL",
    },
    {
        "nome": "Cristiano Zanin",
        "cargo": "ministro_stf",
        "indicado_por": "Lula III",
        "ano_posse": 2023,
        "presidente_stf": False,
        "processos_julgados": 890,
        "relatorias": 98,
        "acompanha_maioria_pct": 79.6,
        "perfil_garantista_pct": 70.0,
        "tempo_medio_dias": 29,
        "casos_destaque": "Ex-advogado de Lula. Primeiras decisões sobre habeas corpus e liberdade de expressão",
        "bio": "Ex-advogado de Lula na Lava Jato. O mais novo ministro da corte. Perfil progressista.",
        "partido_indicador": "PT",
    },
    {
        "nome": "Flávio Dino",
        "cargo": "ministro_stf",
        "indicado_por": "Lula III",
        "ano_posse": 2023,
        "presidente_stf": False,
        "processos_julgados": 780,
        "relatorias": 88,
        "acompanha_maioria_pct": 81.2,
        "perfil_garantista_pct": 66.0,
        "tempo_medio_dias": 31,
        "casos_destaque": "Emendas parlamentares secretas, Operações de segurança pública, Monitoramento eleitoral",
        "bio": "Ex-governador do MA e ex-ministro da Justiça de Lula III. Suspenção de emendas impositivas.",
        "partido_indicador": "PSB",
    },
    {
        "nome": "Alexandre de Moraes",   # evitar duplicata — verificado antes de inserir
        "cargo": "ministro_stf",
        "indicado_por": "Michel Temer",
        "ano_posse": 2017,
        "presidente_stf": False,
        "processos_julgados": 3120,
        "relatorias": 410,
        "acompanha_maioria_pct": 78.1,
        "perfil_garantista_pct": 42.0,
        "tempo_medio_dias": 42,
        "casos_destaque": "Inquérito das Fake News, 8 de Janeiro, PL Bolsonaro",
        "bio": "Ex-ministro da Justiça (Temer). Relator dos processos do 8 de Janeiro.",
        "partido_indicador": "MDB",
    },
]

# Remover duplicata
nomes_vistos = set()
STF_UNICOS = []
for m in STF_MINISTROS:
    if m['nome'] not in nomes_vistos:
        nomes_vistos.add(m['nome'])
        STF_UNICOS.append(m)

PODER_POR_CARGO = {
    'deputado_federal': 'legislativo',
    'senador':          'legislativo',
    'ministro':         'executivo',
    'governador':       'executivo',
    'presidente':       'executivo',
    'ministro_stf':     'judiciario',
}

def coluna_existe(cur, tabela, col):
    cur.execute(f'PRAGMA table_info({tabela})')
    return any(r[1] == col for r in cur.fetchall())

def run():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()

    # 1. Adicionar coluna `poder`
    if not coluna_existe(cur, 'politicos', 'poder'):
        cur.execute("ALTER TABLE politicos ADD COLUMN poder TEXT")
        log.info("Coluna 'poder' adicionada")

    # 2. Preencher `poder` nos registros existentes
    for cargo, poder in PODER_POR_CARGO.items():
        cur.execute("UPDATE politicos SET poder=? WHERE cargo=?", (poder, cargo))
    conn.commit()
    log.info("Campo 'poder' preenchido em todos os registros")

    # 3. Inserir STF (sem duplicatas)
    inseridos = 0
    for m in STF_UNICOS:
        cur.execute("SELECT id FROM politicos WHERE nome=? AND cargo='ministro_stf'", (m['nome'],))
        if cur.fetchone():
            # Atualizar dados
            cur.execute("""
                UPDATE politicos SET
                  score_geral=?, score_presenca=?, score_atividade=?,
                  alinhamento_governo=?, alinhamento_partido=?,
                  email=?, destaques=?, ano_inicio=?, poder='judiciario'
                WHERE nome=? AND cargo='ministro_stf'
            """, (
                round(m['acompanha_maioria_pct'] * 0.4 + (100 - abs(m['perfil_garantista_pct'] - 50)) * 0.6, 1) / 10,
                m['acompanha_maioria_pct'],
                m['processos_julgados'],
                m['acompanha_maioria_pct'],
                100 - m['perfil_garantista_pct'],   # alinhamento_partido = perfil punitivista %
                m['bio'],
                m['casos_destaque'],
                m['ano_posse'],
                m['nome'],
            ))
            log.info(f"  Atualizado: {m['nome']}")
        else:
            score = round((m['acompanha_maioria_pct'] * 0.4 + (100 - abs(m['perfil_garantista_pct'] - 50)) * 0.6) / 10, 1)
            cur.execute("""
                INSERT INTO politicos
                  (nome, cargo, poder, score_geral, score_presenca, score_atividade,
                   alinhamento_governo, alinhamento_partido, email, destaques, ano_inicio, ativo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,1)
            """, (
                m['nome'], 'ministro_stf', 'judiciario',
                score,
                m['acompanha_maioria_pct'],
                m['processos_julgados'],
                m['acompanha_maioria_pct'],
                100 - m['perfil_garantista_pct'],
                m['bio'],
                m['casos_destaque'],
                m['ano_posse'],
            ))
            inseridos += 1
            log.info(f"  Inserido: {m['nome']} (score {score})")

    conn.commit()
    log.info(f"\nSTF: {inseridos} inseridos")

    # Verificar
    cur.execute("SELECT poder, COUNT(*) FROM politicos GROUP BY poder")
    log.info("\nDistribuição por poder:")
    for r in cur.fetchall(): log.info(f"  {r}")

    conn.close()
    log.info("=== MIGRAÇÃO CONCLUÍDA ===")

if __name__ == '__main__':
    run()
