"""
Recalcula score_presenca e score_atividade separadamente para deputados e senadores.
Critério: presença = votações em que participou / total de votações do mesmo grupo (cargo)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transparencia_brasil.db')

def recalcular(conn, cargo, fonte):
    cur = conn.cursor()

    # Total de proposições únicas votadas por parlamentares deste cargo
    cur.execute("""
        SELECT COUNT(DISTINCT v.proposicao)
        FROM votacoes v
        JOIN politicos p ON v.politico_id = p.id
        WHERE p.cargo = ? AND v.fonte = ?
    """, (cargo, fonte))
    total_proposicoes = cur.fetchone()[0]

    if total_proposicoes == 0:
        log.warning(f'Nenhuma votação encontrada para {cargo} / {fonte}')
        return 0

    log.info(f'{cargo}: {total_proposicoes} proposições únicas ({fonte})')

    cur.execute("SELECT id, nome FROM politicos WHERE cargo = ?", (cargo,))
    parlamentares = cur.fetchall()

    atualizados = 0
    for pid, nome in parlamentares:
        cur.execute("""
            SELECT COUNT(DISTINCT proposicao), COUNT(*)
            FROM votacoes WHERE politico_id = ? AND fonte = ?
        """, (pid, fonte))
        distintas, total = cur.fetchone()
        if distintas > 0:
            presenca  = round(min(100.0, distintas / total_proposicoes * 100), 1)
            atividade = total
            cur.execute(
                "UPDATE politicos SET score_presenca=?, score_atividade=? WHERE id=?",
                (presenca, atividade, pid)
            )
            atualizados += 1

    conn.commit()
    log.info(f'  {atualizados}/{len(parlamentares)} {cargo}s com score atualizado')
    return atualizados

def run():
    conn = sqlite3.connect(DB)
    recalcular(conn, 'deputado_federal', 'Câmara dos Deputados')
    recalcular(conn, 'senador',          'Senado Federal')

    # Amostra para validar
    cur = conn.cursor()
    cur.execute("""
        SELECT nome, score_presenca, score_atividade
        FROM politicos WHERE cargo='deputado_federal' AND score_presenca IS NOT NULL
        ORDER BY score_presenca DESC LIMIT 5
    """)
    log.info('Top 5 deputados por presença:')
    for r in cur.fetchall(): log.info(f'  {r}')

    cur.execute("""
        SELECT nome, score_presenca, score_atividade
        FROM politicos WHERE cargo='deputado_federal' AND score_presenca IS NOT NULL
        ORDER BY score_presenca ASC LIMIT 5
    """)
    log.info('Bottom 5 deputados por presença:')
    for r in cur.fetchall(): log.info(f'  {r}')

    conn.close()
    log.info('=== SCORES RECALCULADOS ===')

if __name__ == '__main__':
    run()
