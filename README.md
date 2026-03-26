# Transparência Brasil

Plataforma nacional de dados governamentais que transforma informações públicas em visualizações simples e acessíveis.

## Visão Geral

O projeto coleta dados de fontes oficiais (IBGE, Câmara dos Deputados, Senado Federal, Portal da Transparência e STF), processa os dados via pipeline Python e os expõe através de uma API FastAPI, consumida por um frontend HTML/JS moderno.

```
APIs Oficiais → Pipeline Python → Banco SQLite → FastAPI → Frontend HTML/JS → Usuário
```

---

## Status das Fases

| Fase | Descrição | Status |
|------|-----------|--------|
| Fase 1 | Fundação MVP — estados, ranking, banco, API | ✅ Concluída |
| Fase 2 | Indicadores completos — educação, saúde, segurança, economia | ✅ Concluída |
| Fase 3 | Dados políticos — deputados, senadores, governadores, ministros, presidentes, STF | ✅ Concluída |
| Fase 4 | Municípios — 5.570 cidades com ranking e indicadores locais | ✅ Concluída |
| Fase 5 | Mapa interativo — SVG clicável por estado e cidade | Planejada |
| Fase 6 | Dashboard profissional — gráficos, filtros, histórico | Planejada |
| Fase 7 | Dinheiro público — emendas, contratos, gastos por estado | Planejada |
| Fase 8 | Inteligência — IA para tendências e análise de discursos | Planejada |

---

## Banco de Dados

- **27 estados** com scores de educação, saúde, segurança e economia
- **668 políticos** — deputados federais, senadores, governadores, ministros, presidentes e ministros do STF
- **5.570 municípios** com indicadores e ranking

---

## Tecnologias

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, Uvicorn |
| Banco | SQLite (desenvolvimento) |
| Frontend | HTML5, CSS3, JavaScript puro |
| Gráficos | Chart.js 4 |
| Pipeline | Python (requests, sqlite3) |

---

## Estrutura do Projeto

```
TransparenciaBrasil/
├── backend/
│   ├── main.py          # Endpoints da API (FastAPI)
│   ├── models.py        # Models SQLAlchemy
│   ├── schemas.py       # Schemas Pydantic
│   └── database.py      # Conexão com o banco
├── pipeline/
│   ├── collect_ibge.py          # Fase 1 — coleta de estados
│   ├── fase2_indicadores.py     # Fase 2 — indicadores por estado
│   ├── fase3_politicos.py       # Fase 3 — deputados e senadores
│   ├── melhorias.py             # Governadores, ministros, presidentes
│   ├── migracao_poderes.py      # Migração campo `poder` + STF
│   ├── fase4_municipios.py      # Fase 4 — municípios via API IBGE
│   └── fase4_seed_offline.py    # Fase 4 — gerador offline (sem rede)
├── database/
│   └── schema.sql       # Schema de referência
├── index.html           # Frontend principal
├── app.js               # Lógica do frontend
├── styles.css           # Estilos
├── requirements.txt     # Dependências Python
└── transparencia_brasil.db  # Banco SQLite
```

---

## Instalação e Execução

### Requisitos

- Python 3.11 ou superior

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Popular o banco de dados

```bash
# Fase 1 — Estados
python pipeline/collect_ibge.py

# Fase 2 — Indicadores
python pipeline/fase2_indicadores.py

# Fase 3 — Políticos
python pipeline/fase3_politicos.py
python pipeline/melhorias.py
python pipeline/migracao_poderes.py

# Fase 4 — Municípios (sem internet)
python pipeline/fase4_seed_offline.py

# Fase 4 — Municípios (com internet, dados reais do IBGE)
python pipeline/fase4_municipios.py
```

### 3. Iniciar o backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Abrir o frontend

Abra o arquivo `index.html` diretamente no navegador.

---

## API — Endpoints Principais

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/estados` | Lista todos os estados com scores |
| GET | `/estados/{uf}` | Detalhe de um estado |
| GET | `/politicos` | Lista paginada de políticos (filtro: cargo, uf, partido) |
| GET | `/politicos/{id}` | Perfil completo + votações |
| GET | `/senadores` | Lista de senadores |
| GET | `/governadores` | Lista de governadores |
| GET | `/ministros` | Lista de ministros |
| GET | `/presidentes` | Linha do tempo de presidentes |
| GET | `/stf` | Ministros do Supremo Tribunal Federal |
| GET | `/municipios` | Lista paginada de municípios (filtro: uf, regiao, busca) |
| GET | `/municipios/ranking` | Top municípios por score |
| GET | `/municipios/{id}` | Detalhe de um município |
| GET | `/comparar/politicos` | Comparação lado a lado (até 4) |
| GET | `/historico/comparar/estados` | Série histórica por indicador |
| GET | `/health` | Status da API |

Documentação interativa disponível em: `http://localhost:8000/docs`

---

## Funcionalidades do Frontend

- **Ranking de estados** — score geral e por indicador, com gráfico radar
- **Comparação de estados** — lado a lado com gráficos
- **Série histórica** — evolução dos indicadores ao longo do tempo
- **Presidentes** — linha do tempo visual desde 1985
- **Ministros** — cards com orçamento e execução orçamentária
- **Governadores** — cards vinculados ao score do estado
- **Senadores** — cards com atividade legislativa
- **Deputados Federais** — cards com votações e presença
- **Comparador de políticos** — análise lado a lado
- **Ranking de políticos** — ordenado por presença e atividade
- **STF** — perfil decisório (garantista ↔ punitivista), DNA judicial, filtros
- **Municípios** — 5.570 cidades com ranking, indicadores e modal com radar
- **Sistema de 3 poderes** — cores distintas: Legislativo (azul), Executivo (verde), Judiciário (roxo)
- **DNA político** — tags automáticas de perfil baseadas em scores

---

## Fontes de Dados

| Fonte | Dados |
|-------|-------|
| IBGE API | Estados, municípios, população |
| IBGE SIDRA | PIB per capita municipal |
| Câmara dos Deputados API | Deputados federais, votações |
| Senado Federal API | Senadores |
| Portal da Transparência | Ministros, orçamento |
| STF | Ministros do Supremo |
| INEP | IDEB (educação) |
| FBSP | Segurança pública |

---

## Licença

Dados públicos — fontes oficiais do governo brasileiro.
