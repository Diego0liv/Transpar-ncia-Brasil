from typing import List, Optional
from pydantic import BaseModel


class IndicadorSchema(BaseModel):
    ano: int
    categoria: str
    nome: str
    valor: Optional[float]
    unidade: Optional[str]
    fonte: Optional[str]

    class Config:
        from_attributes = True


class ScoreSchema(BaseModel):
    ano: int
    educacao: float
    saude: float
    seguranca: float
    economia: float
    score_geral: float

    class Config:
        from_attributes = True


class EstadoSchema(BaseModel):
    uf: str
    nome: str
    regiao: str
    capital: Optional[str]

    class Config:
        from_attributes = True


class EstadoRankingSchema(BaseModel):
    uf: str
    nome: str
    regiao: str
    educacao: float
    saude: float
    seguranca: float
    economia: float = 0.0
    score: float

    class Config:
        from_attributes = True


class EstadoDetalheSchema(EstadoSchema):
    indicadores: List[IndicadorSchema] = []
    scores: List[ScoreSchema] = []

    class Config:
        from_attributes = True


class MunicipioOut(BaseModel):
    id:          int
    codigo_ibge: Optional[str]
    nome:        str
    uf:          str
    regiao:      Optional[str]
    populacao:   Optional[int]
    area_km2:    Optional[float]
    educacao:    Optional[float]
    saude:       Optional[float]
    seguranca:   Optional[float]
    economia:    Optional[float]
    score:       Optional[float]
    ano:         Optional[int]

    class Config:
        from_attributes = True
