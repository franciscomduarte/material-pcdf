from agents import Agent, Runner, function_tool 
from provedor import configurar 

configurar() 

@function_tool 
def consultar_clima(cidade: str) -> str: 
    """Retorna o clima atual de uma cidade. Args: cidade: 
    nome da cidade a consultar. """ 
    dados = { "São Paulo": "22°C, nublado", "Brasília": "28°C, sol" } 
    return dados.get( cidade, "Cidade não encontrada." ) 

agente = Agent( 
    name="Assistente de Clima", 
    instructions=( "Você ajuda com informações de clima. " 
                  "Use a ferramenta quando perguntarem sobre o tempo." ), 
    tools=[ consultar_clima ], ) 

def executar_agente(mensagem: str):
    return Runner.run_sync( agente, mensagem )

if __name__ == "__main__":
    resultado = executar_agente( "Como está o tempo em Brasília hoje?" )
    print(resultado.final_output)