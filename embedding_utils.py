# embedding_utils.py - Codificação do texto em um vetor de embedding  
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
# Importação da biblioteca SentenceTransformer para geração de embeddings
from sentence_transformers import SentenceTransformer

# Importação do módulo de logging para registro detalhado de eventos
import logging

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Definição do modelo de embedding a ser utilizado
# 'all-MiniLM-L6-v2' é um modelo pré-treinado que oferece um bom equilíbrio entre performance e qualidade
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def encode_text(text: str) -> list:
    """
    Função para codificar um texto em um vetor de embedding.

    Args:
        text (str): O texto a ser codificado.

    Returns:
        list: Um vetor de embedding representando o texto.
    """
    try:
        # Utiliza o modelo para codificar o texto em um vetor de embedding
        # O método encode() retorna um numpy array, que é convertido para uma lista Python
        embedding = embedding_model.encode(text).tolist()
        logger.debug(
            f"[encode_text] Embedding gerado com sucesso para o texto: '{text[:50]}...'")
        return embedding
    except Exception as e:
        # Em caso de erro, registra o problema no log com detalhes e retorna uma lista vazia
        logger.error(
            f"[encode_text] Erro ao gerar embedding para o texto '{text[:50]}...': {str(e)}", exc_info=True)
        return []


def batch_encode_texts(texts: list) -> list:
    """
    Função para codificar uma lista de textos em vetores de embedding.

    Args:
        texts (list): Uma lista de textos a serem codificados.

    Returns:
        list: Uma lista de vetores de embedding representando os textos.
    """
    try:
        # Utiliza o modelo para codificar múltiplos textos de uma vez
        # Isso é mais eficiente do que codificar cada texto individualmente
        embeddings = embedding_model.encode(texts).tolist()
        logger.debug(
            f"[batch_encode_texts] Embeddings gerados com sucesso para lote de {len(texts)} textos.")
        return embeddings
    except Exception as e:
        # Em caso de erro, registra o problema no log com detalhes e retorna uma lista vazia
        logger.error(
            f"[batch_encode_texts] Erro ao gerar embeddings em lote: {str(e)}", exc_info=True)
        return []


def reload_embedding_model():
    """
    Função para recarregar o modelo de embedding.
    Útil em casos onde o modelo precisa ser atualizado durante a execução.
    """
    global embedding_model
    try:
        # Recarrega o modelo com as mesmas configurações originais
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info(
            "[reload_embedding_model] Modelo de embedding recarregado com sucesso.")
    except Exception as e:
        # Em caso de erro na recarga, registra o problema no log com detalhes
        logger.error(
            f"[reload_embedding_model] Erro ao recarregar o modelo de embedding: {str(e)}", exc_info=True)


def test_embedding_model():
    """
    Função para testar o modelo de embedding.
    Útil para verificar se o modelo está funcionando corretamente.

    Returns:
        bool: True se o teste for bem-sucedido, False caso contrário.
    """
    try:
        # Tenta gerar um embedding para uma frase padrão de teste
        test_text = "Este é um teste do modelo de embedding."
        embedding = encode_text(test_text)

        # Verifica se o embedding foi gerado corretamente (lista não vazia)
        if isinstance(embedding, list) and len(embedding) > 0:
            logger.info(
                "[test_embedding_model] Teste do modelo de embedding bem-sucedido.")
            return True
        else:
            logger.warning(
                "[test_embedding_model] Falha no teste: Embedding inválido gerado.")
            return False
    except Exception as e:
        # Em caso de erro durante o teste, registra o problema no log com detalhes
        logger.error(
            f"[test_embedding_model] Erro durante teste do modelo: {str(e)}", exc_info=True)
        return False
