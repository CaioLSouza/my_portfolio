"""Esquema da extracao estruturada de cada teleconferencia de resultados.

A taxonomia de temas e fechada de proposito: so com a mesma lista de temas em
todas as empresas e trimestres da para comparar "quanto se falou de X" ao
longo do tempo e entre setores. Se um tema novo ficar recorrente em "outros",
e sinal de que vale promove-lo a tema proprio (e reprocessar o historico).
"""
from typing import Literal

from pydantic import BaseModel, Field

Tema = Literal[
    "demanda_e_volumes",
    "precos_e_margens",
    "custos_e_inflacao",
    "credito_e_inadimplencia",
    "juros_e_endividamento",
    "capex_e_expansao",
    "dividendos_e_recompra",
    "fusoes_e_aquisicoes",
    "regulacao_e_governo",
    "cambio_e_exterior",
    "macro_brasil",
    "concorrencia",
    "tecnologia_e_ia",
    "esg_e_clima",
    "gestao_e_governanca",
    "outros",
]

# -2 = muito negativo/cauteloso, 0 = neutro, +2 = muito positivo/confiante
Nota = Literal[-2, -1, 0, 1, 2]


class TemaDiscutido(BaseModel):
    tema: Tema
    sentimento: Nota = Field(description="Como a gestao fala desse tema: -2 muito negativo a +2 muito positivo.")
    intensidade: Literal[1, 2, 3] = Field(
        description="Peso do tema na teleconferencia: 1 = mencao lateral, 2 = discutido, 3 = tema central."
    )
    destaque: str = Field(description="Uma frase, em portugues, com o que foi dito sobre o tema.")
    citacao: str = Field(description="Trecho literal da transcricao que sustenta o destaque, no idioma original.")


class MudancaGuidance(BaseModel):
    metrica: str = Field(description="Ex.: 'capex 2025', 'margem EBITDA', 'crescimento da carteira de credito'.")
    direcao: Literal["eleva", "mantem", "reduz", "introduz", "retira"]
    detalhe: str
    citacao: str


class PerguntaAnalista(BaseModel):
    tema: Tema
    pergunta: str = Field(description="Resumo da pergunta em uma frase, em portugues.")
    resposta_evasiva: bool = Field(
        description="True se a gestao desviou, nao respondeu ou respondeu so de forma generica."
    )


class ExtracaoTeleconferencia(BaseModel):
    tom_geral: Nota = Field(description="Tom geral da gestao na teleconferencia.")
    justificativa_tom: str = Field(description="Duas ou tres frases explicando a nota de tom.")
    resumo: str = Field(description="Resumo de ate 5 frases, em portugues, do que importa para o investidor.")
    temas: list[TemaDiscutido]
    guidance: list[MudancaGuidance] = Field(description="Vazio se nao houve nenhuma mencao a guidance.")
    perguntas_analistas: list[PerguntaAnalista]
