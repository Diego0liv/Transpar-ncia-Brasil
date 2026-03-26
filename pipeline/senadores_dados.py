import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time, logging, urllib.request, json
from datetime import date
from backend.database import SessionLocal
from backend import models

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

API = 'https://legis.senado.leg.br/dadosabertos'

def get_json(url):
    try:
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=20) as r:
            chunks = []
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            return json.loads(b''.join(chunks))
    except Exception as e:
        log.warning(f'Erro GET {url}: {e}')
        return None

def parse_date(s):
    try:
        return date.fromisoformat(s[:10]) if s else None
    except Exception:
        return None

def run():
    db = SessionLocal()
    try:
        # 1. Buscar lista com fotos
        log.info('Buscando lista de senadores...')
        d = get_json(f'{API}/senador/lista/atual.json')
        if not d:
            log.error('Falha ao buscar lista'); return

        senadores_api = d['ListaParlamentarEmExercicio']['Parlamentares']['Parlamentar']
        mapa = {}
        for s in senadores_api:
            ident = s['IdentificacaoParlamentar']
            mapa[ident['NomeParlamentar'].strip()] = {
                'codigo': ident['CodigoParlamentar'],
                'foto':   ident.get('UrlFotoParlamentar'),
            }

        # 2. Atualizar fotos
        senadores_db = db.query(models.Politico).filter(models.Politico.cargo == 'senador').all()
        fotos = 0
        for sen in senadores_db:
            dados = mapa.get(sen.nome)
            if not dados:
                for nome_api, d_api in mapa.items():
                    if nome_api.lower() in sen.nome.lower() or sen.nome.lower() in nome_api.lower():
                        dados = d_api; break
            if dados:
                sen.foto_url = dados['foto']
                sen.codigo_externo = dados['codigo']
                fotos += 1
        db.commit()
        log.info(f'Fotos atualizadas: {fotos}/81')

        # 3. Buscar votações — votos JA VEM dentro do JSON de cada votação
        votos_inseridos = 0
        # 2024: API retorna JSON muito grande e corrompido; buscar por semestre
        periodos = [
            ('2024', '2024-01-01', '2024-06-30'),
            ('2024', '2024-07-01', '2024-12-31'),
            ('2023', None, None),
        ]
        for (ano, d_ini, d_fim) in periodos:
            if d_ini:
                url = f'{API}/votacao?dataInicio={d_ini}&dataFim={d_fim}&format=json'
                label = f'{d_ini[:7]} → {d_fim[:7]}'
            else:
                url = f'{API}/votacao?ano={ano}&format=json'
                label = ano
            log.info(f'Buscando votações do Senado {label}...')
            lista = get_json(url)
            if not lista:
                log.warning(f'Sem dados para {label}'); continue

            log.info(f'  {len(lista)} votações em {label}')
            for i, votacao in enumerate(lista):
                descricao = (votacao.get('descricaoVotacao') or votacao.get('identificacao', ''))[:200]
                data_sessao = (votacao.get('dataSessao') or '')[:10]
                votos = votacao.get('votos') or []
                if not isinstance(votos, list):
                    votos = [votos]

                for voto_item in votos:
                    nome_sen  = (voto_item.get('nomeParlamentar') or '').strip()
                    sigla_voto = (voto_item.get('siglaVotoParlamentar') or '').strip()
                    if not nome_sen or not sigla_voto:
                        continue

                    # Mapear sigla para texto legível
                    mapa_voto = {
                        'Sim': 'Sim', 'Não': 'Não', 'Nao': 'Não',
                        'Abstenção': 'Abstenção', 'Abstencao': 'Abstenção',
                        'Votou': 'Sim', 'NCom': 'Não Compareceu',
                        'P-OD': 'Obstrução', 'Obstrução': 'Obstrução',
                    }
                    voto_val = mapa_voto.get(sigla_voto, sigla_voto)

                    # Encontrar senador no banco
                    sen_db = next((s for s in senadores_db if s.nome == nome_sen), None)
                    if not sen_db:
                        sen_db = next((s for s in senadores_db
                                       if nome_sen.lower() in s.nome.lower()
                                       or s.nome.lower() in nome_sen.lower()), None)
                    if not sen_db:
                        continue

                    # Evitar duplicata
                    existe = db.query(models.Votacao).filter(
                        models.Votacao.politico_id == sen_db.id,
                        models.Votacao.proposicao  == descricao,
                    ).first()
                    if existe:
                        continue

                    db.add(models.Votacao(
                        politico_id=sen_db.id,
                        proposicao=descricao,
                        voto=voto_val,
                        data_votacao=parse_date(data_sessao),
                        fonte='Senado Federal',
                    ))
                    votos_inseridos += 1

                if (i + 1) % 20 == 0:
                    db.commit()
                    log.info(f'    {i+1}/{len(lista)} processadas, {votos_inseridos} votos até agora')

            db.commit()
            time.sleep(0.5)
        log.info(f'Total de votos inseridos: {votos_inseridos}')

        # 4. Calcular scores
        log.info('Calculando scores de presença...')
        total_votacoes = db.query(models.Votacao.proposicao).distinct().count()
        for sen in senadores_db:
            qtd_distintas = db.query(models.Votacao.proposicao).filter(
                models.Votacao.politico_id == sen.id
            ).distinct().count()
            qtd_total = db.query(models.Votacao).filter(
                models.Votacao.politico_id == sen.id
            ).count()
            if qtd_distintas > 0 and total_votacoes > 0:
                sen.score_presenca  = round(min(100, qtd_distintas / total_votacoes * 100), 1)
                sen.score_atividade = qtd_total
        db.commit()

        votos_banco = db.query(models.Votacao).join(models.Politico).filter(
            models.Politico.cargo == 'senador'
        ).count()
        log.info(f'\n=== CONCLUÍDO ===')
        log.info(f'Fotos: {fotos} | Votos no banco: {votos_banco}')

    finally:
        db.close()

if __name__ == '__main__':
    run()
