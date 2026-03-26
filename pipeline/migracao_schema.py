"""
Migração: adiciona colunas dedicadas ao banco para eliminar gambiarras.
- politicos: ministerio, destaques, ano_inicio, ano_fim, codigo_externo
- Migra dados dos campos errados para os corretos
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3, logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

DB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'transparencia_brasil.db')

def coluna_existe(cur, tabela, coluna):
    cur.execute(f'PRAGMA table_info({tabela})')
    return any(r[1] == coluna for r in cur.fetchall())

def run():
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()

    # Adicionar colunas novas
    novas = [
        ('ministerio',    'TEXT'),
        ('destaques',     'TEXT'),
        ('ano_inicio',    'INTEGER'),
        ('ano_fim',       'INTEGER'),
        ('codigo_externo','TEXT'),
    ]
    for col, tipo in novas:
        if not coluna_existe(cur, 'politicos', col):
            cur.execute(f'ALTER TABLE politicos ADD COLUMN {col} {tipo}')
            log.info(f'Coluna adicionada: {col}')
        else:
            log.info(f'Coluna já existe: {col}')

    conn.commit()

    # Migrar ministros: email → ministerio, uf → destaques
    cur.execute("SELECT id, email, uf FROM politicos WHERE cargo='ministro'")
    ministros = cur.fetchall()
    for pid, email, uf_val in ministros:
        # uf_val contém os destaques (texto longo), email contém o ministério
        cur.execute(
            "UPDATE politicos SET ministerio=?, destaques=?, uf=NULL WHERE id=?",
            (email, uf_val, pid)
        )
    conn.commit()
    log.info(f'Ministros migrados: {len(ministros)}')

    # Migrar presidentes: score_presenca → ano_inicio, score_atividade → ano_fim
    cur.execute("SELECT id, score_presenca, score_atividade FROM politicos WHERE cargo='presidente'")
    presidentes = cur.fetchall()
    for pid, sp, sa in presidentes:
        cur.execute(
            "UPDATE politicos SET ano_inicio=?, ano_fim=?, score_presenca=NULL, score_atividade=NULL WHERE id=?",
            (int(sp) if sp else None, int(sa) if sa else None, pid)
        )
    conn.commit()
    log.info(f'Presidentes migrados: {len(presidentes)}')

    # Verificar resultado
    cur.execute("SELECT nome, ministerio, destaques FROM politicos WHERE cargo='ministro' LIMIT 2")
    log.info('Ministros após migração:')
    for r in cur.fetchall(): log.info(f'  {r[0]} | {r[1]} | {str(r[2])[:60]}...')

    cur.execute("SELECT nome, ano_inicio, ano_fim FROM politicos WHERE cargo='presidente' LIMIT 3")
    log.info('Presidentes após migração:')
    for r in cur.fetchall(): log.info(f'  {r}')

    conn.close()
    log.info('=== MIGRAÇÃO CONCLUÍDA ===')

if __name__ == '__main__':
    run()
