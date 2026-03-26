from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class Estado(Base):
    __tablename__ = "estados"

    id      = Column(Integer, primary_key=True, index=True)
    uf      = Column(String(2), unique=True, nullable=False, index=True)
    nome    = Column(String(100), nullable=False)
    regiao  = Column(String(2), nullable=False)
    capital = Column(String(100))
    area_km2 = Column(Float)

    indicadores = relationship("Indicador", back_populates="estado")


class Indicador(Base):
    __tablename__ = "indicadores"

    id              = Column(Integer, primary_key=True, index=True)
    estado_id       = Column(Integer, ForeignKey("estados.id"), nullable=False)
    ano             = Column(Integer, nullable=False)
    categoria       = Column(String(50), nullable=False)
    nome            = Column(String(200), nullable=False)
    valor           = Column(Float)
    unidade         = Column(String(50))
    fonte           = Column(String(100))
    data_coleta     = Column(Date)

    estado = relationship("Estado", back_populates="indicadores")


class ScoreEstado(Base):
    __tablename__ = "scores_estados"

    id          = Column(Integer, primary_key=True, index=True)
    estado_id   = Column(Integer, ForeignKey("estados.id"), nullable=False)
    ano         = Column(Integer, nullable=False)
    educacao    = Column(Float, default=0.0)
    saude       = Column(Float, default=0.0)
    seguranca   = Column(Float, default=0.0)
    economia    = Column(Float, default=0.0)
    score_geral = Column(Float, default=0.0)

    estado = relationship("Estado")


class Politico(Base):
    __tablename__ = "politicos"

    id              = Column(Integer, primary_key=True, index=True)
    id_externo      = Column(Integer, index=True)
    nome            = Column(String(200), nullable=False)
    partido         = Column(String(50))
    uf              = Column(String(2), index=True)
    cargo           = Column(String(50))
    foto_url        = Column(Text)
    email           = Column(String(200))
    ativo           = Column(Integer, default=1)
    score_presenca  = Column(Float)
    score_atividade = Column(Float)
    ministerio      = Column(String(200))
    destaques       = Column(Text)
    ano_inicio      = Column(Integer)
    ano_fim         = Column(Integer)
    codigo_externo  = Column(String(50))

    poder               = Column(String(20))  # legislativo | executivo | judiciario
    alinhamento_partido = Column(Float)
    alinhamento_governo = Column(Float)
    score_geral         = Column(Float)

    votacoes = relationship("Votacao", back_populates="politico")


class Municipio(Base):
    __tablename__ = "municipios"

    id          = Column(Integer, primary_key=True, index=True)
    codigo_ibge = Column(String(10), unique=True, index=True)
    nome        = Column(String(200), nullable=False)
    uf          = Column(String(2), nullable=False, index=True)
    regiao      = Column(String(2))
    populacao   = Column(Integer)
    area_km2    = Column(Float)
    educacao    = Column(Float)
    saude       = Column(Float)
    seguranca   = Column(Float)
    economia    = Column(Float)
    score       = Column(Float, index=True)
    ano         = Column(Integer, default=2023)


class Votacao(Base):
    __tablename__ = "votacoes"

    id           = Column(Integer, primary_key=True, index=True)
    politico_id  = Column(Integer, ForeignKey("politicos.id"), nullable=False)
    data_votacao = Column(Date)
    proposicao   = Column(String(500))
    voto         = Column(String(50))   # Sim | Não | Abstenção | Faltou
    fonte        = Column(String(100))

    politico = relationship("Politico", back_populates="votacoes")
