# chroma_utils.py - Realiza a consulta no ChromaDB 
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import chromadb
import logging
import re
import hashlib
from keybert import KeyBERT

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Inicialização do modelo KeyBERT para extração de palavras-chave
kw_model = KeyBERT('neuralmind/bert-base-portuguese-cased')


def get_snippet_chroma(collection, query, model, window=800):
    """
    Recupera snippets relevantes do ChromaDB com base na consulta.

    Args:
        collection: Objeto de coleção do ChromaDB.
        query (str): Consulta do usuário.
        model: Modelo de embedding usado para codificar a consulta.
        window (int): Tamanho da janela de contexto ao redor da correspondência.

    Returns:
        dict: Dicionário contendo o texto do snippet e os arquivos relacionados.
    """
    try:
        # Obtém o número total de documentos na coleção
        total_docs = collection.count()
        # Define o número de resultados a serem retornados (máximo 10)
        n_results = min(10, total_docs) if total_docs > 0 else 1

        # Codifica a consulta usando o modelo de embedding
        query_embedding = model.encode(query).tolist()

        # Realiza a consulta no ChromaDB
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=['documents', 'metadatas', 'distances']
        )

        # Extrai palavras-chave da consulta usando o modelo KeyBERT
        query_keywords = kw_model.extract_keywords(
            query, keyphrase_ngram_range=(1, 2), top_n=3)
        query_keywords = [kw[0].lower() for kw in query_keywords]

        best_chunks = []
        for doc, meta, distance in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
            # Extrai palavras-chave do documento
            doc_keywords = [kw.strip().lower()
                            for kw in meta.get('palavras_chave', '').split(',')]
            # Calcula a correspondência de palavras-chave
            keyword_match = len(set(query_keywords) & set(doc_keywords))
            # Calcula a pontuação combinando distância e correspondência de palavras-chave
            score = (1 - distance) * 0.6 + keyword_match * 0.4

            # Adiciona o chunk à lista se a pontuação for alta ou se a consulta estiver no texto
            if score > 0.3 or query.lower() in doc.lower():
                best_chunks.append({
                    "text": doc,
                    "score": score,
                    "position": meta.get('chunk_position', 0),
                    "file_path": meta.get('file_path', '')
                })

        if not best_chunks:
            logger.warning(
                f"[get_snippet_chroma] Nenhum snippet encontrado para consulta '{query}'.")
            return {"text": "", "files": []}

        # Ordena os chunks por pontuação e posição
        best_chunks.sort(key=lambda x: (-x['score'], x['position']))

        combined_text = []
        current_end = -1
        for chunk in best_chunks[:3]:
            start_pos = chunk['text'].lower().find(query.lower())
            if start_pos != -1:
                start = max(0, start_pos - window//2)
                end = min(len(chunk['text']), start_pos + window//2)
                if start > current_end:
                    combined_text.append(chunk['text'][start:end])
                    current_end = end

        return {
            "text": "\n\n[...]\n\n".join(combined_text) if combined_text else "",
            "files": list(set([chunk['file_path'] for chunk in best_chunks if chunk['file_path']]))
        }

    except Exception as e:
        logger.error(
            f"[get_snippet_chroma] Erro ao recuperar snippet para consulta '{query}': {str(e)}", exc_info=True)
        return {"text": "", "files": []}


def refine_snippet_chroma(collection, snippet, model):
    """
    Refina o snippet obtido do ChromaDB.

    Args:
        collection: Objeto de coleção do ChromaDB.
        snippet (str): Texto do snippet inicial.
        model: Modelo de embedding usado para codificar o snippet.

    Returns:
        dict: Dicionário contendo o texto refinado e os arquivos relacionados.
    """
    try:
        if not snippet.strip():
            logger.warning(
                "[refine_snippet_chroma] Snippet vazio recebido para refinamento.")
            return {"text": "", "files": []}

        # Obtém o número total de documentos na coleção
        total_docs = collection.count()
        # Define o número de resultados a serem retornados (máximo 3)
        n_results = min(3, total_docs) if total_docs > 0 else 1

        # Codifica o snippet usando o modelo de embedding
        snippet_embedding = model.encode(snippet).tolist()

        # Realiza a consulta no ChromaDB
        results = collection.query(
            query_embeddings=[snippet_embedding],
            n_results=n_results,
            include=['documents', 'metadatas'],
            where={"document_type": {"$ne": "image"}}
        )

        # Combina os documentos retornados em um texto refinado
        refined_texts = [doc for doc in results['documents']
                         [0] if len(doc.strip()) > 50]
        refined_text = "\n\n".join(refined_texts)[
            :2000] if refined_texts else snippet[:2000]

        # Extrai os caminhos dos arquivos dos metadados
        files = list(set([meta.get('file_path', '')
                     for meta in results['metadatas'][0]]))

        return {"text": refined_text, "files": files}

    except Exception as e:
        logger.error(
            f"[refine_snippet_chroma] Erro ao refinar snippet: {str(e)}", exc_info=True)
        return {"text": snippet, "files": []}


def sanitize_collection_name(name: str) -> str:
    """
    Sanitiza o nome da coleção para garantir compatibilidade com o ChromaDB.

    Args:
        name (str): Nome original da coleção.

    Returns:
        str: Nome sanitizado da coleção.
    """
    # Remove caracteres não permitidos
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Remove underscores e hífens duplicados
    sanitized = re.sub(r'_{2,}', '_', sanitized)
    sanitized = re.sub(r'-{2,}', '-', sanitized)
    # Remove underscores, hífens e pontos no início e no final
    sanitized = sanitized.strip('_-.')

    # Se o nome sanitizado for muito curto, usa um hash como fallback
    if len(sanitized) < 3:
        hash_fallback = hashlib.sha1(name.encode()).hexdigest()[:8]
        sanitized_name = f"col_{hash_fallback}"
    else:
        # Limita o tamanho do nome a 63 caracteres
        sanitized_name = sanitized[:63].rstrip('_-')

    # Verifica se o nome sanitizado atende aos requisitos do ChromaDB
    if not re.match(r'^[a-zA-Z0-9][\w-]{1,61}[a-zA-Z0-9]$', sanitized_name):
        sanitized_name = f"col_{sanitized_name[:54]}_{hashlib.sha1(name.encode()).hexdigest()[:4]}"

    logger.debug(
        f"[sanitize_collection_name] Nome original '{name}' sanitizado para '{sanitized_name}'.")
    return sanitized_name
