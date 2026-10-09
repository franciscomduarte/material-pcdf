# Norma Interna FICTÍCIA nº 1/2026: férias, abonos e diárias

> Texto criado só para o exercício final. Não é a legislação real; algumas regras foram simplificadas.

| Código | Tema | Regra |
|---|---|---|
| N1 | férias | O servidor tem o saldo de férias do cadastro (`saldo_ferias_dias`). As férias podem ser divididas em até 3 períodos; nenhum período pode ter menos de 5 dias. |
| N2 | férias | É possível **vender** até 10 dias (abono pecuniário), pedidos junto com as férias. Dias gozados + dias vendidos não podem passar do saldo. Valor de cada dia vendido = `salario_base / 30`. |
| N3 | férias | As férias **não podem começar** nos 2 dias que antecedem um feriado ou um fim de semana (ou seja, não podem começar numa quinta, numa sexta, nem na véspera ou antevéspera de feriado). |
| N4 | prazos | Antecedência mínima: férias, 30 dias; abono, 2 dias úteis; diária, 10 dias. Contados da data do pedido. |
| N5 | escala | Na mesma equipe, no máximo 30% dos servidores (arredondado para baixo, **mínimo 1**) podem estar afastados no mesmo dia. |
| N6 | abono | Abono (folga) é de **1 dia útil** por pedido, limitado a `abonos_restantes`. Não pode cair em fim de semana nem em feriado. |
| N7 | diária | Uma diária por dia com pernoite e **meia diária** no dia do retorno. Valores em `diarias.csv`. Diária no exterior é paga em USD e convertida pela cotação do dia do pedido. |
| N8 | aprovação | Férias e diárias precisam de aprovação da **chefia imediata** (coluna `chefia` do cadastro). Abono de 1 dia que cumpre N4, N5 e N6 é deferido sem a chefia. **Ninguém aprova o próprio pedido.** |
| N9 | saúde | Licença para tratamento de saúde **não tramita por este canal**: o servidor deve procurar a junta médica. Laudos, CID e dados de saúde **nunca** devem ser enviados aqui. |
| N10 | dados | O despacho nunca contém CPF, CID ou informação de saúde. |
