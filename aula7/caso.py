"""
caso.py -- os casos da Aula 7 (dados FICTÍCIOS e didáticos).

Com LLM real, o modelo só pode trabalhar com o que está no texto: por isso cada denúncia traz os FATOS.
O Investigador extrai fatos da denúncia (não inventa), o Jurídico enquadra e o Analista avalia.
"""

# Caso principal de toda a aula: contratação de grande valor, com vários indícios.
DENUNCIA_045 = (
    "Denúncia anônima sobre o Pregão 045/2026: o contrato, de R$ 2,8 milhões, teve o edital divulgado com apenas "
    "3 dias de antecedência da abertura das propostas. Houve um único proponente e um dos sócios da empresa "
    "vencedora é ex-servidor do órgão contratante."
)

# Segunda denúncia (exemplo 03: estado x memória).
DENUNCIA_051 = (
    "Denúncia sobre o Pregão 051/2026: em 10 dias o órgão firmou três contratações de material de escritório com "
    "a mesma empresa, de R$ 48 mil cada, todas logo abaixo do limite de R$ 50 mil para dispensa de licitação."
)

# Caso de baixo risco (desafios): valor pequeno e sem indícios de direcionamento.
DENUNCIA_BAIXO_VALOR = (
    "Denúncia sobre a compra de 200 canetas por R$ 300, de baixo valor, feita sem cotação de preços. "
    "Não há indício de vínculo entre o servidor e o fornecedor."
)
