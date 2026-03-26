import sqlite3
import random
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "transparencia_brasil.db")

MUNICIPIOS_POR_UF = {
    "RO": 52,  "AC": 22,  "AM": 62,  "RR": 15,  "PA": 144, "AP": 16,
    "TO": 139, "MA": 217, "PI": 224, "CE": 184,  "RN": 167, "PB": 223,
    "PE": 185, "AL": 102, "SE": 75,  "BA": 417,  "MG": 853, "ES": 78,
    "RJ": 92,  "SP": 645, "PR": 399, "SC": 295,  "RS": 497, "MS": 79,
    "MT": 141, "GO": 246, "DF": 1,
}

CODIGO_UF = {
    "AC": 12, "AL": 27, "AM": 13, "AP": 16, "BA": 29, "CE": 23,
    "DF": 53, "ES": 32, "GO": 52, "MA": 21, "MG": 31, "MS": 50,
    "MT": 51, "PA": 15, "PB": 25, "PE": 26, "PI": 22, "PR": 41,
    "RJ": 33, "RN": 24, "RO": 11, "RR": 14, "RS": 43, "SC": 42,
    "SE": 28, "SP": 35, "TO": 17,
}

SCORE_BASE = {
    "SC": 77.1, "PR": 75.4, "RS": 76.5, "SP": 76.8, "DF": 82.1, "MG": 67.1,
    "ES": 61.5, "RJ": 51.3, "GO": 56.1, "MS": 57.9, "MT": 55.2, "TO": 47.3,
    "PA": 39.8, "AM": 42.1, "RO": 52.3, "AC": 44.5, "AP": 38.7, "RR": 41.2,
    "BA": 44.8, "CE": 46.2, "MA": 35.1, "PI": 36.4, "PB": 45.1, "PE": 44.9,
    "AL": 38.3, "SE": 46.7, "RN": 47.5,
}

REGIOES = {
    "AC": "N",  "AM": "N",  "AP": "N",  "PA": "N",  "RO": "N",  "RR": "N",  "TO": "N",
    "AL": "NE", "BA": "NE", "CE": "NE", "MA": "NE", "PB": "NE", "PE": "NE",
    "PI": "NE", "RN": "NE", "SE": "NE",
    "DF": "CO", "GO": "CO", "MS": "CO", "MT": "CO",
    "ES": "SE", "MG": "SE", "RJ": "SE", "SP": "SE",
    "PR": "S",  "RS": "S",  "SC": "S",
}

PREFIXES = [
    "São", "Santa", "Santo", "Vila", "Novo", "Nova", "Boa", "Bom",
    "Porto", "Serra", "Rio", "Alto", "Monte", "Campo", "Campina",
    "Lagoa", "Palmeira", "Cachoeira", "Barra", "Água", "Ponta", "Presidente",
]

SUFFIXES = [
    "Verde", "Alegre", "Grande", "Novo", "Belo", "Formoso", "Lindo",
    "Florido", "Bonito", "Dourado", "Claro", "Rico", "Fundo", "Largo",
    "Branco", "Preto", "Azul", "Real", "Nobre", "Bom",
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS municipios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  codigo_ibge TEXT UNIQUE,
  nome TEXT NOT NULL,
  uf TEXT NOT NULL,
  regiao TEXT,
  populacao INTEGER,
  area_km2 REAL,
  educacao REAL,
  saude REAL,
  seguranca REAL,
  economia REAL,
  score REAL,
  ano INTEGER DEFAULT 2023
)
"""

UPSERT_SQL = """
INSERT INTO municipios
    (codigo_ibge, nome, uf, regiao, populacao, area_km2, educacao, saude, seguranca, economia, score, ano)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 2023)
ON CONFLICT(codigo_ibge) DO UPDATE SET
    nome=excluded.nome,
    uf=excluded.uf,
    regiao=excluded.regiao,
    populacao=excluded.populacao,
    area_km2=excluded.area_km2,
    educacao=excluded.educacao,
    saude=excluded.saude,
    seguranca=excluded.seguranca,
    economia=excluded.economia,
    score=excluded.score,
    ano=excluded.ano
"""


def generate_name(uf, seq, codigo_ibge):
    rng = random.Random(int(codigo_ibge) + 7)
    prefix = PREFIXES[(seq - 1) % len(PREFIXES)]
    suffix = SUFFIXES[rng.randint(0, len(SUFFIXES) - 1)]

    style = rng.randint(0, 3)
    if style == 0:
        return f"{prefix} {suffix}"
    elif style == 1:
        return f"{prefix} {suffix} de {uf}"
    elif style == 2:
        return f"{prefix} {suffix} do {uf}"
    else:
        return f"{prefix} {suffix} {seq}"


def generate_row(uf, seq):
    uf_code = CODIGO_UF[uf]
    codigo_ibge = f"{uf_code:02d}{seq:05d}"
    seed = int(codigo_ibge)
    rng = random.Random(seed)

    nome = generate_name(uf, seq, codigo_ibge)
    regiao = REGIOES[uf]
    populacao = rng.randint(1000, 500000)
    area_km2 = round(rng.uniform(10.0, 50000.0), 2)

    base = SCORE_BASE[uf]
    variation = 20.0

    educacao  = round(max(10.0, min(95.0, base + rng.uniform(-variation, variation))), 2)
    saude     = round(max(10.0, min(95.0, base + rng.uniform(-variation, variation))), 2)
    seguranca = round(max(10.0, min(95.0, base + rng.uniform(-variation, variation))), 2)
    economia  = round(max(10.0, min(95.0, base + rng.uniform(-variation, variation))), 2)
    score     = round((educacao + saude + seguranca + economia) / 4, 2)

    return (codigo_ibge, nome, uf, regiao, populacao, area_km2, educacao, saude, seguranca, economia, score)


def main():
    db_path = os.path.normpath(DB_PATH)
    print(f"Conectando ao banco: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()

    total_inserido = 0

    for uf, count in MUNICIPIOS_POR_UF.items():
        rows = []
        for seq in range(1, count + 1):
            rows.append(generate_row(uf, seq))

        cur.executemany(UPSERT_SQL, rows)
        conn.commit()
        total_inserido += len(rows)
        print(f"  {uf}: {len(rows)} municipios inseridos/atualizados")

    cur.execute("SELECT COUNT(*) FROM municipios")
    count_db = cur.fetchone()[0]
    conn.close()

    print(f"\nConcluido. Total gerado: {total_inserido} | Total na tabela: {count_db}")


if __name__ == "__main__":
    main()
