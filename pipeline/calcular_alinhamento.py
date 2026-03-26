"""
Calcula alinhamento com partido e governo para deputados e senadores.
Resultado salvo em: alinhamento_partido, alinhamento_governo, score_geral
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)
DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transparencia_brasil.db')

PARTIDO_GOVERNO = 'PT'  # partido do presidente atual

def coluna_existe(cur, tabela, col):
    cur.execute(f'PRAGMA table_info({tabela})')
    return any(r[1] == col for r in cur.fetchall())

def run():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()

    # Adicionar novas colunas se não existirem
    for col, tipo in [('alinhamento_partido','REAL'), ('alinhamento_governo','REAL'), ('score_geral','REAL')]:
        if not coluna_existe(cur, 'politicos', col):
            cur.execute(f'ALTER TABLE politicos ADD COLUMN {col} {tipo}')
            log.info(f'Coluna adicionada: {col}')
    conn.commit()

    for cargo in ('deputado_federal', 'senador'):
        log.info(f'\nProcessando {cargo}...')
        cur.execute("SELECT id, nome, partido FROM politicos WHERE cargo=?", (cargo,))
        parlamentares = cur.fetchall()

        # Buscar todas as proposições com ao menos 10 votos
        cur.execute("""
            SELECT v.proposicao, COUNT(*) as total
            FROM votacoes v JOIN politicos p ON v.politico_id=p.id
            WHERE p.cargo=?
            GROUP BY v.proposicao HAVING total >= 10
        """, (cargo,))
        proposicoes = [r[0] for r in cur.fetchall()]
        log.info(f'  {len(proposicoes)} proposições com >= 10 votos')

        if not proposicoes:
            log.warning(f'  Sem proposições suficientes para {cargo}')
            continue

        # Para cada proposição calcular:
        # - maioria do partido
        # - voto do governo (maioria do PT)
        voto_maioria_partido = {}  # {(proposicao, partido): voto_maioria}
        voto_maioria_governo  = {}  # {proposicao: voto_maioria_PT}

        for prop in proposicoes:
            # Maioria por partido
            cur.execute("""
                SELECT p.partido, v.voto, COUNT(*) as n
                FROM votacoes v JOIN politicos p ON v.politico_id=p.id
                WHERE p.cargo=? AND v.proposicao=?
                  AND v.voto IN ('Sim','Não','Nao')
                GROUP BY p.partido, v.voto
                ORDER BY n DESC
            """, (cargo, prop))
            votos_partido = {}
            for partido, voto, n in cur.fetchall():
                if partido not in votos_partido:
                    votos_partido[partido] = voto
            for partido, voto in votos_partido.items():
                voto_maioria_partido[(prop, partido)] = voto

            # Maioria do governo (PT)
            cur.execute("""
                SELECT v.voto, COUNT(*) as n
                FROM votacoes v JOIN politicos p ON v.politico_id=p.id
                WHERE p.cargo=? AND v.proposicao=? AND p.partido=?
                  AND v.voto IN ('Sim','Não','Nao')
                GROUP BY v.voto ORDER BY n DESC LIMIT 1
            """, (cargo, prop, PARTIDO_GOVERNO))
            row = cur.fetchone()
            if row:
                voto_maioria_governo[prop] = row[0]

        log.info(f'  Maiorias calculadas para {len(voto_maioria_partido)} (partido,prop) pares')

        # Calcular alinhamento por parlamentar
        total_pols = len(parlamentares)
        for idx, (pid, nome, partido) in enumerate(parlamentares):
            cur.execute("""
                SELECT proposicao, voto FROM votacoes
                WHERE politico_id=? AND voto IN ('Sim','Não','Nao')
            """, (pid,))
            meus_votos = {r[0]: r[1] for r in cur.fetchall()}

            if not meus_votos:
                continue

            # Alinhamento partido
            props_com_maioria = [(p, v) for p, v in meus_votos.items()
                                  if (p, partido) in voto_maioria_partido]
            ali_partido = None
            if props_com_maioria:
                iguais = sum(1 for p, v in props_com_maioria
                             if v == voto_maioria_partido.get((p, partido)))
                ali_partido = round(iguais / len(props_com_maioria) * 100, 1)

            # Alinhamento governo
            props_gov = [(p, v) for p, v in meus_votos.items()
                          if p in voto_maioria_governo]
            ali_gov = None
            if props_gov:
                iguais_gov = sum(1 for p, v in props_gov
                                 if v == voto_maioria_governo.get(p))
                ali_gov = round(iguais_gov / len(props_gov) * 100, 1)

            # Score geral (0-10)
            presenca = None
            cur.execute("SELECT score_presenca, score_atividade FROM politicos WHERE id=?", (pid,))
            row = cur.fetchone()
            presenca  = row[0] or 0
            atividade = row[1] or 0

            # Normalizar atividade (deputados: ~200 votos = max, senadores: ~211 = max)
            max_ativ = 211 if cargo == 'senador' else 200
            ativ_norm = min(100, atividade / max_ativ * 100)

            score = round((
                presenca   * 0.40 +
                ativ_norm  * 0.30 +
                (ali_partido or 0) * 0.30
            ) / 10, 1)

            cur.execute("""
                UPDATE politicos
                SET alinhamento_partido=?, alinhamento_governo=?, score_geral=?
                WHERE id=?
            """, (ali_partido, ali_gov, score, pid))

            if (idx + 1) % 100 == 0:
                conn.commit()
                log.info(f'  {idx+1}/{total_pols} processados')

        conn.commit()
        log.info(f'  {cargo} concluído')

    # Amostra
    cur.execute("""
        SELECT nome, score_geral, score_presenca, alinhamento_partido, alinhamento_governo
        FROM politicos WHERE cargo='senador' AND score_geral IS NOT NULL
        ORDER BY score_geral DESC LIMIT 5
    """)
    log.info('\nTop 5 senadores por score_geral:')
    for r in cur.fetchall(): log.info(f'  {r}')

    conn.close()
    log.info('\n=== ALINHAMENTO CALCULADO ===')

if __name__ == '__main__':
    run()
