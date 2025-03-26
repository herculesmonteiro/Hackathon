# llm_utils.py - Retorna uma instância do modelo de linguagem escolhido  
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
from langchain_community.chat_models import ChatOpenAI
import logging
import os

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Chaves de API para os modelos de linguagem
OPENAI_API_KEY = "coloque_sua_chave_aqui"
DEEPSEEK_API_KEY = "coloque_sua_chave_aqui"

def get_llm(model_choice: str):
    """
    Retorna uma instância do modelo de linguagem escolhido.
    
    Args:
        model_choice (str): A escolha do modelo ('OpenAI' ou 'Deepseek').
    
    Returns:
        ChatOpenAI: Uma instância do modelo de chat escolhido.
    """
    try:
        if model_choice == "OpenAI":
            # Cria e retorna uma instância do modelo OpenAI
            return ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model_name="gpt-3.5-turbo",
                temperature=0.7
            )
        elif model_choice == "Deepseek":
            # Cria e retorna uma instância do modelo Deepseek
            return ChatOpenAI(
                api_key=DEEPSEEK_API_KEY,
                model_name="deepseek-chat",
                openai_api_base="https://api.deepseek.com/v1",
                temperature=0.7
            )
        else:
            # Lança uma exceção se a escolha do modelo for inválida
            raise ValueError(f"Modelo LLM não suportado: {model_choice}")
    except Exception as e:
        # Registra o erro e re-lança a exceção
        logger.error(f"Erro ao inicializar o modelo LLM {model_choice}: {str(e)}", exc_info=True)
        raise

def generate_llm_response(llm, context: str, query: str, prompt_template: str) -> str:
    """
    Gera uma resposta usando o modelo de linguagem especificado.
    
    Args:
        llm (ChatOpenAI): Instância do modelo de chat.
        context (str): O contexto para a pergunta.
        query (str): A pergunta do usuário.
        prompt_template (str): O template do prompt a ser usado.
    
    Returns:
        str: A resposta gerada pelo modelo.
    """
    try:
        # Formata o prompt com o contexto e a pergunta
        prompt = prompt_template.format(context=context, query=query)
        # Invoca o modelo LLM para gerar uma resposta
        response = llm.invoke(prompt)
        # Retorna o conteúdo da resposta
        return response.content
    except Exception as e:
        # Registra o erro e retorna uma mensagem de erro
        logger.error(f"Erro ao gerar resposta LLM: {str(e)}", exc_info=True)
        return "Desculpe, ocorreu um erro ao gerar a resposta. Por favor, tente novamente."

def validate_api_keys():
    """
    Valida se as chaves de API necessárias estão configuradas.
    
    Returns:
        bool: True se ambas as chaves estão configuradas, False caso contrário.
    """
    if not OPENAI_API_KEY:
        logger.warning("Chave de API OpenAI não configurada.")
        return False
    if not DEEPSEEK_API_KEY:
        logger.warning("Chave de API Deepseek não configurada.")
        return False
    return True

# Esta função pode ser usada para atualizar as chaves de API em tempo de execução
def update_api_key(api_type: str, new_key: str):
    """
    Atualiza a chave de API para o serviço especificado.
    
    Args:
        api_type (str): O tipo de API ('OpenAI' ou 'Deepseek').
        new_key (str): A nova chave de API.
    """
    global OPENAI_API_KEY, DEEPSEEK_API_KEY
    try:
        if api_type == "OpenAI":
            OPENAI_API_KEY = new_key
            os.environ["OPENAI_API_KEY"] = new_key
        elif api_type == "Deepseek":
            DEEPSEEK_API_KEY = new_key
            os.environ["DEEPSEEK_API_KEY"] = new_key
        else:
            raise ValueError(f"Tipo de API não suportado: {api_type}")
        logger.info(f"Chave de API {api_type} atualizada com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao atualizar chave de API {api_type}: {str(e)}", exc_info=True)
        raise
