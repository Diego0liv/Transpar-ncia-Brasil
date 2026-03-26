import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from backend import models
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
log = logging.getLogger(__name__)

# LOA 2024 — orçamento autorizado por ministério (R$ bilhões)
# Fonte: SIAFI / Portal da Transparência / LOA 2024
MINISTROS_DATA = [
    {
        "nome": "Fernando Haddad",
        "ministerio": "Ministério da Fazenda",
        "orcamento_bi": 5200.0,   # Gerencia todo o orçamento federal
        "execucao_pct": 94.2,
        "foto": "https://www.gov.br/fazenda/pt-br/@@images/imagem_ministro/large",
        "destaques": "Arcabouço fiscal, reforma tributária (IBS/CBS/IS), programa Desenrola Brasil, revisão de isentos de IR",
    },
    {
        "nome": "Rui Costa",
        "ministerio": "Casa Civil da Presidência",
        "orcamento_bi": 2.1,
        "execucao_pct": 88.5,
        "foto": None,
        "destaques": "Coordenação do governo, PAC (R$ 1,7 tri em investimentos), programa Minha Casa Minha Vida",
    },
    {
        "nome": "José Múcio",
        "ministerio": "Ministério da Defesa",
        "orcamento_bi": 120.4,
        "execucao_pct": 91.7,
        "foto": None,
        "destaques": "Reaparelhamento das Forças Armadas, operações de defesa civil, SIPAM, combate ao tráfico nas fronteiras",
    },
    {
        "nome": "Alexandre Padilha",
        "ministerio": "Secretaria de Relações Institucionais",
        "orcamento_bi": 1.2,
        "execucao_pct": 85.0,
        "foto": None,
        "destaques": "Articulação política no Congresso, reforma ministerial, aprovação do arcabouço fiscal",
    },
    {
        "nome": "Flávio Dino",
        "ministerio": "Ministério da Justiça e Segurança Pública",
        "orcamento_bi": 18.3,
        "execucao_pct": 89.4,
        "foto": None,
        "destaques": "Operação Escudo, combate ao crime organizado, regulamentação do porte de armas, FNSP",
    },
    {
        "nome": "Ricardo Lewandowski",
        "ministerio": "Ministério da Justiça e Segurança Pública",
        "orcamento_bi": 18.3,
        "execucao_pct": 87.0,
        "foto": None,
        "destaques": "Substituiu Flávio Dino (STF). Foco em segurança pública, combate ao tráfico e sistema prisional",
    },
    {
        "nome": "Nísia Trindade",
        "ministerio": "Ministério da Saúde",
        "orcamento_bi": 234.7,
        "execucao_pct": 93.1,
        "foto": None,
        "destaques": "Programa Mais Médicos, Farmácia Popular, vacinação COVID/Dengue, reconstrução do SUS pós-pandemia",
    },
    {
        "nome": "Camilo Santana",
        "ministerio": "Ministério da Educação",
        "orcamento_bi": 156.8,
        "execucao_pct": 91.5,
        "foto": None,
        "destaques": "PNEM, PNLD, expansão de escolas em tempo integral, revisão do ENEM, PROUNI e FIES",
    },
    {
        "nome": "Wellington Dias",
        "ministerio": "Ministério do Desenvolvimento Social",
        "orcamento_bi": 243.5,
        "execucao_pct": 97.8,
        "foto": None,
        "destaques": "Bolsa Família (21 mi famílias), CadÚnico, programa de alimentação escolar, Benefício de Prestação Continuada",
    },
    {
        "nome": "Alexandre Silveira",
        "ministerio": "Ministério de Minas e Energia",
        "orcamento_bi": 12.6,
        "execucao_pct": 82.3,
        "foto": None,
        "destaques": "Transição energética, leilões de petróleo, expansão de energias renováveis, programa Luz para Todos",
    },
    {
        "nome": "Renan Filho",
        "ministerio": "Ministério dos Transportes",
        "orcamento_bi": 48.9,
        "execucao_pct": 78.6,
        "foto": None,
        "destaques": "PAC Rodovias, duplicação de BRs, PPPs de ferrovias, recuperação de rodovias federais",
    },
    {
        "nome": "Paulo Teixeira",
        "ministerio": "Ministério do Desenvolvimento Agrário",
        "orcamento_bi": 9.4,
        "execucao_pct": 86.2,
        "foto": None,
        "destaques": "Reforma agrária, PRONAF, agricultura familiar, assentamentos do MST, crédito rural",
    },
    {
        "nome": "Carlos Fávaro",
        "ministerio": "Ministério da Agricultura e Pecuária",
        "orcamento_bi": 32.1,
        "execucao_pct": 90.4,
        "foto": None,
        "destaques": "Plano Safra R$ 364 bi, agronegócio, defesa agropecuária, abertura de mercados externos",
    },
    {
        "nome": "Jorge Messias",
        "ministerio": "Advocacia-Geral da União",
        "orcamento_bi": 3.8,
        "execucao_pct": 88.1,
        "foto": None,
        "destaques": "Defesa jurídica da União, recuperação de créditos públicos, revisão de contratos",
    },
    {
        "nome": "Márcio Macêdo",
        "ministerio": "Secretaria-Geral da Presidência",
        "orcamento_bi": 1.6,
        "execucao_pct": 79.5,
        "foto": None,
        "destaques": "Participação social, conselhos nacionais, programa Brasil Participativo",
    },
    {
        "nome": "Paulo Pimenta",
        "ministerio": "Secretaria de Comunicação Social",
        "orcamento_bi": 3.2,
        "execucao_pct": 84.7,
        "foto": None,
        "destaques": "Comunicação do governo federal, combate à desinformação, EBC, Agência Brasil",
    },
    {
        "nome": "Anielle Franco",
        "ministerio": "Ministério da Igualdade Racial",
        "orcamento_bi": 3.1,
        "execucao_pct": 76.3,
        "foto": None,
        "destaques": "Política de cotas, combate ao racismo, quilombolas, reparação histórica",
    },
    {
        "nome": "Aparecida Gonçalves",
        "ministerio": "Ministério das Mulheres",
        "orcamento_bi": 2.4,
        "execucao_pct": 73.8,
        "foto": None,
        "destaques": "Programa Pé-de-Meia, combate à violência doméstica, Casa da Mulher Brasileira, Lei Maria da Penha",
    },
    {
        "nome": "Silvio Almeida",
        "ministerio": "Ministério dos Direitos Humanos",
        "orcamento_bi": 2.8,
        "execucao_pct": 71.4,
        "foto": None,
        "destaques": "Programa Nacional de Direitos Humanos, proteção de povos indígenas, combate ao trabalho escravo",
    },
    {
        "nome": "Sônia Guajajara",
        "ministerio": "Ministério dos Povos Indígenas",
        "orcamento_bi": 2.6,
        "execucao_pct": 80.9,
        "foto": None,
        "destaques": "Demarcação de terras indígenas (26 TIs), saúde indígena (SESAI), proteção Yanomami",
    },
    {
        "nome": "Marina Silva",
        "ministerio": "Ministério do Meio Ambiente",
        "orcamento_bi": 8.7,
        "execucao_pct": 88.6,
        "foto": None,
        "destaques": "Desmatamento Amazônia -50% (2023), PPCDAm, Fundo Amazônia (R$ 3,2 bi), COP30 Belém 2025",
    },
    {
        "nome": "Margareth Menezes",
        "ministerio": "Ministério da Cultura",
        "orcamento_bi": 4.2,
        "execucao_pct": 83.1,
        "foto": None,
        "destaques": "Vale Cultura, Ancine, Funarte, fomento ao audiovisual e patrimônio cultural",
    },
    {
        "nome": "Lula da Silva",
        "ministerio": "Presidência da República",
        "orcamento_bi": 9.5,
        "execucao_pct": 95.0,
        "foto": None,
        "destaques": "Chefia do Poder Executivo Federal",
    },
    {
        "nome": "Geraldo Alckmin",
        "ministerio": "Ministério do Desenvolvimento, Indústria e Comércio",
        "orcamento_bi": 28.4,
        "execucao_pct": 86.7,
        "foto": None,
        "destaques": "Nova Indústria Brasil, BNDES, Missão Espacial Brasileira, semicondutores, reindustrialização",
    },
    {
        "nome": "Esther Dweck",
        "ministerio": "Ministério da Gestão e Inovação",
        "orcamento_bi": 310.2,
        "execucao_pct": 92.4,
        "foto": None,
        "destaques": "Gestão da folha de pagamento, servidores públicos, concursos federais, desburocratização",
    },
    {
        "nome": "Simone Tebet",
        "ministerio": "Ministério do Planejamento e Orçamento",
        "orcamento_bi": 2.1,
        "execucao_pct": 90.1,
        "foto": None,
        "destaques": "LOA 2024/2025, revisão de gastos, arcabouço fiscal, meta fiscal, Novo PAC orçamentário",
    },
    {
        "nome": "Nísia Trindade Lima",
        "ministerio": "Ministério da Saúde",
        "orcamento_bi": 234.7,
        "execucao_pct": 93.1,
        "foto": None,
        "destaques": "Programa Mais Médicos, Farmácia Popular, reconstrução do SUS",
    },
    {
        "nome": "Jorge Lima",
        "ministerio": "Ministério do Esporte",
        "orcamento_bi": 3.6,
        "execucao_pct": 74.5,
        "foto": None,
        "destaques": "Bolsa Atleta, Copa do Mundo 2030, infraestrutura esportiva, Jogos Olímpicos 2024",
    },
    {
        "nome": "Sonia Guajajara",
        "ministerio": "Ministério dos Povos Indígenas",
        "orcamento_bi": 2.6,
        "execucao_pct": 80.9,
        "foto": None,
        "destaques": "Demarcação de 26 terras indígenas, saúde indígena (SESAI), proteção Yanomami, FUNAI",
    },
    {
        "nome": "Mauro Vieira",
        "ministerio": "Ministério das Relações Exteriores",
        "orcamento_bi": 6.8,
        "execucao_pct": 89.3,
        "foto": None,
        "destaques": "Presidência do G20 Brasil 2024, COP30 Belém 2025, acordos comerciais Mercosul-UE, política externa ativa",
    },
    {
        "nome": "Márcio França",
        "ministerio": "Ministério dos Portos e Aeroportos",
        "orcamento_bi": 14.2,
        "execucao_pct": 76.8,
        "foto": None,
        "destaques": "Concessões de portos e aeroportos, PAC infraestrutura logística, dragagem de portos",
    },
    {
        "nome": "Waldez Góes",
        "ministerio": "Ministério da Integração e Desenvolvimento Regional",
        "orcamento_bi": 22.7,
        "execucao_pct": 83.4,
        "foto": None,
        "destaques": "Reconstrução RS após enchentes, Defesa Civil nacional, SUDENE, SUDAM, obras de infraestrutura regional",
    },
    {
        "nome": "Jader Filho",
        "ministerio": "Ministério das Cidades",
        "orcamento_bi": 38.5,
        "execucao_pct": 85.9,
        "foto": None,
        "destaques": "Minha Casa Minha Vida (2 mi unidades), saneamento básico, mobilidade urbana, PAC Cidades",
    },
    {
        "nome": "Paulo Gonet",
        "ministerio": "Procuradoria-Geral da República",
        "orcamento_bi": 4.1,
        "execucao_pct": 91.2,
        "foto": None,
        "destaques": "Chefia do Ministério Público Federal, ações do STF sobre 8 de janeiro, investigações de corrupção",
    },
    {
        "nome": "Aparecida Gonçalves",
        "ministerio": "Ministério das Mulheres",
        "orcamento_bi": 2.4,
        "execucao_pct": 73.8,
        "foto": None,
        "destaques": "Casa da Mulher Brasileira, combate à violência doméstica, Lei Maria da Penha, Pé-de-Meia Mulher",
    },
    {
        "nome": "Márcio Macêdo",
        "ministerio": "Secretaria-Geral da Presidência",
        "orcamento_bi": 1.6,
        "execucao_pct": 79.5,
        "foto": None,
        "destaques": "Participação social, conselhos nacionais, programa Brasil Participativo, ouvidorias",
    },
]

def run():
    db = SessionLocal()
    try:
        ministros_db = db.query(models.Politico).filter(
            models.Politico.cargo == 'ministro'
        ).all()

        atualizados = 0
        for min_db in ministros_db:
            # Buscar dados por nome
            dados = next((d for d in MINISTROS_DATA if
                d['nome'].lower() in min_db.nome.lower() or
                min_db.nome.lower() in d['nome'].lower()), None)

            if dados:
                # Armazenar orçamento em score_atividade (R$ bilhões)
                min_db.score_atividade = dados['orcamento_bi']
                # Armazenar execução % em score_presenca
                min_db.score_presenca = dados['execucao_pct']
                # Atualizar ministerio (via campo email)
                min_db.email = dados['ministerio']
                # Foto se disponível
                if dados.get('foto'):
                    min_db.foto_url = dados['foto']
                # Destaques no campo uf (workaround — campo texto livre)
                # Precisamos de uma coluna dedicada; usar uf para destaques
                min_db.uf = dados['destaques'][:200]
                atualizados += 1
                log.info(f"  {min_db.nome}: R$ {dados['orcamento_bi']} bi | {dados['execucao_pct']}%")
            else:
                log.warning(f"  Sem dados para: {min_db.nome}")

        db.commit()
        log.info(f"\n=== CONCLUÍDO: {atualizados}/{len(ministros_db)} ministros atualizados ===")

    finally:
        db.close()

if __name__ == '__main__':
    run()
