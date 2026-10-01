"""
prompts.py -- os PROMPTS da Aula 7 (já prontos): um por especialista.

Cada função devolve o TEXTO do prompt. Você o passa a modelo.gerar(...).
Todos seguem o mesmo cuidado: dizer o PAPEL, o que ENTRA, o que SAI (curto) e proibir invenção.
(Com LLM real, um prompt solto como "analise isto" inventa fatos. O Investigador só extrai o que está na denúncia.)
"""

REGRA = "Use SOMENTE as informações fornecidas. Não invente valores, nomes, datas nem fatos que não estejam no texto."


def tudo(solicitacao: str) -> str:
    """Agente generalista (exemplo 01): faz tudo de uma vez."""
    return (
        "Você é um analista de controle interno.\n"
        "Com base na denúncia abaixo, faça, em sequência e em no máximo 6 linhas no total: "
        "(1) investigue os fatos; (2) faça a análise jurídica; (3) avalie o risco (BAIXO, MÉDIO ou ALTO); "
        "(4) recomende as providências.\n"
        f"{REGRA}\n"
        f"Denúncia: {solicitacao}"
    )


def investigar(solicitacao: str) -> str:
    return (
        "Você é o INVESTIGADOR de um órgão de controle.\n"
        "Liste, em no máximo 3 frases, apenas os FATOS verificáveis da denúncia abaixo. "
        "Não opine, não cite leis e não avalie risco.\n"
        f"{REGRA}\n"
        f"Denúncia: {solicitacao}"
    )


def juridico(fatos: str) -> str:
    return (
        "Você é o ASSESSOR JURÍDICO de um órgão de controle.\n"
        "Com base nos fatos abaixo, indique, em no máximo 3 frases, quais normas podem ter sido violadas "
        "(por exemplo, a Lei 14.133/2021, Lei de Licitações) e por quê. "
        "Não avalie risco e não recomende ações. Se não tiver certeza de um artigo, escreva 'artigo a confirmar'.\n"
        f"Fatos: {fatos}"
    )


def risco(fatos: str, enquadramento: str = "") -> str:
    """Sem `enquadramento` o risco é avaliado só pelos fatos (exemplo 08, em paralelo com o jurídico)."""
    juridico_ = f"\nEnquadramento jurídico: {enquadramento}" if enquadramento else ""
    return (
        "Você é o ANALISTA de risco de um órgão de controle.\n"
        "Classifique o risco em BAIXO, MÉDIO ou ALTO e justifique em UMA frase. "
        "Comece a resposta pela palavra do nível (por exemplo: 'ALTO: ...').\n"
        f"Fatos: {fatos}{juridico_}"
    )


def recomendar(fatos: str, enquadramento: str, nivel_risco: str, feedback: str = "") -> str:
    """1ª versão: um RASCUNHO curto (o humano vai avaliar). Com feedback do revisor: versão completa."""
    base = (
        "Você é o ANALISTA de um órgão de controle.\n"
        f"Fatos: {fatos}\n"
        + (f"Enquadramento jurídico: {enquadramento}\n" if enquadramento else "")
        + f"Risco: {nivel_risco}\n"
    )
    if feedback:
        return (
            base
            + f"Um revisor humano REJEITOU a versão anterior com este feedback: {feedback}\n"
            "Refaça a recomendação atendendo ao feedback: escreva de 3 a 4 ações em itens numerados (1), 2), 3)...), "
            "cada uma com o responsável e o prazo. "
            "Não cite números de lei nem de artigos nas ações. "
            + REGRA
        )
    return base + "Escreva um RASCUNHO curto da recomendação: no máximo 2 frases, sem numerar, e sem citar números de lei ou de artigos. " + REGRA


def comunicar(texto: str) -> str:
    return (
        "Você é o especialista em COMUNICAÇÃO de um órgão de controle.\n"
        "Avalie a CLAREZA do texto abaixo em no máximo 2 frases e diga o que melhoraria. "
        "Não altere o conteúdo jurídico nem o risco.\n"
        f"Texto: {texto}"
    )


def classificar_risco(solicitacao: str, fatos: str) -> str:
    """Desafio 1: decide se precisa de humano (ALTO) ou não (BAIXO). Em dúvida, o parser trata como ALTO."""
    return (
        "Você classifica o risco de uma denúncia sobre contratação pública.\n"
        "- ALTO: valor elevado, indício de direcionamento ou de vínculo entre as partes.\n"
        "- BAIXO: valor reduzido e sem nenhum indício de irregularidade grave.\n"
        "Responda com UMA palavra: ALTO ou BAIXO.\n"
        f"Denúncia: {solicitacao}\n"
        f"Fatos: {fatos}"
    )


def nivel_de(texto: str) -> str:
    """'ALTO' / 'Baixo.' / 'é BAIXO' -> 'alto' | 'baixo'. Em dúvida (nenhum ou os dois), 'alto': melhor pedir humano."""
    t = texto.upper()
    return "baixo" if "BAIXO" in t and "ALTO" not in t else "alto"


def conformidade(fatos: str) -> str:
    """Exercício do exemplo 08: um terceiro especialista, em paralelo com o jurídico e o risco."""
    return (
        "Você é o especialista em CONFORMIDADE de um órgão de controle.\n"
        "Com base nos fatos abaixo, aponte, em no máximo 2 frases, quais procedimentos internos podem ter sido "
        "descumpridos (por exemplo, pesquisa de preços, publicidade do edital, segregação de funções). "
        f"{REGRA}\n"
        f"Fatos: {fatos}"
    )
