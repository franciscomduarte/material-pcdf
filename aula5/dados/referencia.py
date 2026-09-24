"""
referencia.py -- dados de referência CANÔNICOS e fictícios da CISP.

Este módulo é importado por seed_postgres.py e seed_sqlserver.py.
É o que garante que os dois bancos, apesar de independentes, falem da
MESMA realidade: a tabela `unidades` existe nos dois sistemas, com o
mesmo `codigo` e a mesma região -- mas sem nenhuma FK entre os bancos.
O agente é quem vai cruzar essas informações, casando pelo `codigo`
ou pelo nome da região.

Todos os nomes, regiões e coordenadas são fictícios.
"""

# 12 regiões fictícias (alfabeto fonético -- não corresponde a nenhum
# município real). `peso_ocorrencias` e `peso_viaturas` controlam,
# de forma determinística, a concentração de dados em cada região:
# regiões "quentes" (peso_ocorrencias alto) recebem mais ocorrências
# e, propositalmente, proporção menor de viaturas disponíveis.
REGIOES = [
    # codigo    nome                 zona      peso_ocorrencias  peso_viaturas
    ("ALFA",    "Região Alfa",       "CENTRO",  1.6,              0.9),
    ("BRAVO",   "Região Bravo",      "NORTE",   2.4,              0.6),   # hotspot
    ("CHARLIE", "Região Charlie",    "NORTE",   1.1,              1.0),
    ("DELTA",   "Região Delta",      "SUL",     0.9,              1.1),
    ("ECHO",    "Região Echo",       "SUL",     1.0,              1.0),
    ("FOXTROT", "Região Foxtrot",    "LESTE",   2.1,              0.7),   # hotspot
    ("GOLF",    "Região Golf",       "LESTE",   1.2,              1.0),
    ("HOTEL",   "Região Hotel",      "OESTE",   0.8,              1.2),
    ("INDIA",   "Região Índia",      "OESTE",   0.7,              1.2),
    ("JULIETT", "Região Juliett",    "CENTRO",  1.3,              0.95),
    ("KILO",    "Região Kilo",       "NORTE",   1.9,              0.65),  # hotspot
    ("LIMA",    "Região Lima",       "SUL",     0.9,              1.05),
]

# 10 tipos de ocorrência.
TIPOS_OCORRENCIA = [
    # codigo               nome                          categoria     gravidade_base  peso_frequencia
    ("FURTO",              "Furto",                      "PATRIMONIAL", "BAIXA",   3.0),
    ("ROUBO",               "Roubo",                      "PATRIMONIAL", "ALTA",    2.2),
    ("ROUBO_VEICULO",       "Roubo de Veículo",           "PATRIMONIAL", "ALTA",    1.1),
    ("HOMICIDIO",           "Homicídio",                  "VIOLENTO",    "CRITICA", 0.15),
    ("LESAO_CORPORAL",      "Lesão Corporal",             "VIOLENTO",    "ALTA",    1.0),
    ("TRAFICO",             "Tráfico de Entorpecentes",   "VIOLENTO",    "ALTA",    0.8),
    ("VIOLENCIA_DOMESTICA", "Violência Doméstica",        "VIOLENTO",    "ALTA",    1.3),
    ("PERTURBACAO",         "Perturbação do Sossego",     "OUTROS",      "BAIXA",   1.6),
    ("DANO_PATRIMONIO",     "Dano ao Patrimônio Público", "PATRIMONIAL", "MEDIA",   0.9),
    ("ACIDENTE_TRANSITO",   "Acidente de Trânsito",       "TRANSITO",    "MEDIA",   1.9),
]

# 22 unidades, 1-2 por região. `tipo` só é usado no MCP Operações
# (no MCP Ocorrências a unidade só precisa de codigo/nome/regiao).
# lat/long são aproximadas e fictícias, dentro de uma caixa que não
# corresponde a nenhuma cidade real (a "Metrópole Central" fictícia
# da CISP).
UNIDADES = [
    # codigo         nome                                          regiao_codigo  tipo         lat        lon
    ("DP-ALFA-01",   "1ª Delegacia de Polícia - Alfa",              "ALFA",    "DELEGACIA",       -23.5100, -46.5000),
    ("BPM-ALFA-01",  "1º Batalhão de Polícia Militar - Alfa",       "ALFA",    "BATALHAO",        -23.5150, -46.5050),
    ("DP-BRAVO-01",  "2ª Delegacia de Polícia - Bravo",             "BRAVO",   "DELEGACIA",       -23.4700, -46.5200),
    ("BPM-BRAVO-01", "2º Batalhão de Polícia Militar - Bravo",      "BRAVO",   "BATALHAO",        -23.4650, -46.5250),
    ("CIA-BRAVO-01", "3ª Companhia PM - Bravo",                     "BRAVO",   "CIA_PM",          -23.4600, -46.5300),
    ("DP-CHARLIE-01","3ª Delegacia de Polícia - Charlie",           "CHARLIE", "DELEGACIA",       -23.4500, -46.4900),
    ("BPM-CHARLIE-01","4º Batalhão de Polícia Militar - Charlie",   "CHARLIE", "BATALHAO",        -23.4450, -46.4950),
    ("DP-DELTA-01",  "4ª Delegacia de Polícia - Delta",             "DELTA",   "DELEGACIA",       -23.5800, -46.4800),
    ("BPM-DELTA-01", "5º Batalhão de Polícia Militar - Delta",      "DELTA",   "BATALHAO",        -23.5850, -46.4850),
    ("DP-ECHO-01",   "5ª Delegacia de Polícia - Echo",              "ECHO",    "DELEGACIA",       -23.5900, -46.4600),
    ("BASE-ECHO-01", "Base Comunitária Echo",                       "ECHO",    "BASE_COMUNITARIA", -23.5950, -46.4650),
    ("DP-FOXTROT-01","6ª Delegacia de Polícia - Foxtrot",           "FOXTROT", "DELEGACIA",       -23.5200, -46.4300),
    ("BPM-FOXTROT-01","6º Batalhão de Polícia Militar - Foxtrot",   "FOXTROT", "BATALHAO",        -23.5250, -46.4250),
    ("CIA-FOXTROT-01","7ª Companhia PM - Foxtrot",                  "FOXTROT", "CIA_PM",          -23.5300, -46.4200),
    ("DP-GOLF-01",   "7ª Delegacia de Polícia - Golf",              "GOLF",    "DELEGACIA",       -23.4900, -46.4200),
    ("DP-HOTEL-01",  "8ª Delegacia de Polícia - Hotel",             "HOTEL",   "DELEGACIA",       -23.6100, -46.5500),
    ("BPM-HOTEL-01", "7º Batalhão de Polícia Militar - Hotel",      "HOTEL",   "BATALHAO",        -23.6150, -46.5550),
    ("DP-INDIA-01",  "9ª Delegacia de Polícia - Índia",             "INDIA",   "DELEGACIA",       -23.6300, -46.5700),
    ("DP-JULIETT-01","10ª Delegacia de Polícia - Juliett",          "JULIETT", "DELEGACIA",       -23.5000, -46.5100),
    ("BASE-KILO-01", "Base Comunitária Kilo",                       "KILO",    "BASE_COMUNITARIA",-23.4300, -46.5400),
    ("DP-KILO-01",   "11ª Delegacia de Polícia - Kilo",             "KILO",    "DELEGACIA",       -23.4350, -46.5450),
    ("DP-LIMA-01",   "12ª Delegacia de Polícia - Lima",             "LIMA",    "DELEGACIA",       -23.6000, -46.4400),
]

STATUS_OCORRENCIA = ["REGISTRADA", "EM_ANDAMENTO", "CONCLUIDA", "ARQUIVADA"]
STATUS_VIATURA = ["DISPONIVEL", "EM_ATENDIMENTO", "EM_DESLOCAMENTO", "MANUTENCAO", "INDISPONIVEL"]
TURNOS = ["DIURNO", "NOTURNO", "INTEGRAL"]
ESPECIALIDADES = ["PATRULHAMENTO", "INVESTIGACAO", "TATICO", "TRANSITO"]
TIPOS_VIATURA = ["VTR", "MOTO", "BLINDADO", "RESGATE"]

SEED_DETERMINISTICO = 2026  # mesma seed em ambos os geradores -> mesmos resultados para toda a turma
