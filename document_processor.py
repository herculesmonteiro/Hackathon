# document_processor.py - Processamento dos documentos dentro das coleções  
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================

import os
import logging
from pdf_utils import process_pdf
from excel_utils import process_excel
from docx_utils import process_docx
from text_utils import process_txt
from image_utils import process_image
from audio_utils import process_audio
from embedding_utils import embedding_model
from chroma_utils import sanitize_collection_name
from keybert import KeyBERT
from nltk.corpus import stopwords
from datetime import datetime
import re
import nltk

nltk.download('stopwords')

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Inicialização do modelo KeyBERT para extração de palavras-chave
kw_model = KeyBERT('distilbert-base-nli-mean-tokens')

def process_document(file_path: str) -> list:
    """
    Identifica a extensão do arquivo e delega para o módulo adequado.
    Args:
        file_path (str): Caminho completo do arquivo a ser processado.
    Returns:
        list: Lista de textos extraídos do documento.
    """
    # Obtém a extensão do arquivo
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # Delega o processamento para o módulo específico baseado na extensão
        if ext == '.pdf':
            return process_pdf(file_path)
        elif ext in ['.xls', '.xlsx']:
            return process_excel(file_path)
        elif ext == '.docx':
            return process_docx(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
            return process_image(file_path)
        elif ext in ['.mp3', '.wav', '.ogg']:
            return process_audio(file_path)
        else:
            # Para outros tipos de arquivo, assume-se que é texto
            return process_txt(file_path)
    except Exception as e:
        # Registra o erro no log e propaga a exceção
        logger.error(f"Erro ao processar documento {file_path}: {e}", exc_info=True)
        raise

def split_into_chunks(text: str, max_chunk_size: int = 1000) -> list:
    """
    Divide o texto em chunks menores.
    Args:
        text (str): Texto a ser dividido.
        max_chunk_size (int): Tamanho máximo de cada chunk.
    Returns:
        list: Lista de chunks de texto.
    """
    # Divide o texto em sentenças
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current_chunk, current_length = [], [], 0

    # Agrupa sentenças em chunks
    for sentence in sentences:
        sent_length = len(sentence)
        if current_length + sent_length > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk, current_length = [], 0
        current_chunk.append(sentence)
        current_length += sent_length

    # Adiciona o último chunk se houver
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def generate_metadata(text: str, doc_name: str, client_name: str, file_path: str) -> dict:
    """
    Gera metadados para o texto processado.
    Args:
        text (str): Texto do documento.
        doc_name (str): Nome do documento.
        client_name (str): Nome do cliente.
        file_path (str): Caminho do arquivo.
    Returns:
        dict: Dicionário com os metadados gerados.
    """
    try:
        # Extrai palavras-chave do texto
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words=stopwords.words('portuguese'),
            top_n=5
        )

        # Gera o dicionário de metadados
        return {
            "titulo": os.path.splitext(doc_name)[0],
            "autor": client_name,
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "colecoes": ', '.join([kw[0] for kw in keywords[:2]]),
            "palavras_chave": ', '.join([kw[0] for kw in keywords]),
            "file_path": file_path
        }
    except Exception as e:
        # Registra o erro no log e retorna um dicionário vazio
        logger.error(f"Erro ao gerar metadados: {e}", exc_info=True)
        return {
            "titulo": os.path.splitext(doc_name)[0],
            "autor": client_name,
            "data_publicacao": datetime.now().strftime("%Y-%m-%d"),
            "colecoes": "default",
            "palavras_chave": "default",
            "file_path": file_path
        }

# Função auxiliar para processar e adicionar documento ao ChromaDB
def process_and_add_to_chroma(file_path: str, client_name: str, collection):
    """
    Processa um documento e adiciona ao ChromaDB.
    Args:
        file_path (str): Caminho do arquivo a ser processado.
        client_name (str): Nome do cliente.
        collection: Objeto de coleção do ChromaDB.
    """
    try:
        # Processa o documento
        textos = process_document(file_path)
        collection_name = sanitize_collection_name(os.path.basename(file_path))

        # Processa cada texto extraído do documento
        for idx, texto in enumerate(textos):
            chunks = split_into_chunks(texto)
            for chunk_idx, chunk in enumerate(chunks):
                # Gera metadados para o chunk
                metadata = generate_metadata(chunk, os.path.basename(file_path), client_name, file_path)
                # Gera embedding para o chunk
                embedding = embedding_model.encode(chunk).tolist()
                # Adiciona o chunk à coleção do ChromaDB
                collection.add(
                    ids=[f"{collection_name}chunk{idx}{chunk_idx}"],
                    documents=[chunk],
                    metadatas=[metadata],
                    embeddings=[embedding]
                )

        logger.info(f"Documento {file_path} processado e adicionado com sucesso.")
    except Exception as e:
        logger.error(f"Erro ao processar e adicionar documento {file_path}: {e}", exc_info=True)
        raise

def process_document(file_path: str) -> list:
    """
    Identifica a extensão do arquivo e delega para o módulo adequado.
    Args:
        file_path (str): Caminho completo do arquivo a ser processado.
    Returns:
        list: Lista de textos extraídos do documento.
    """
    # Obtém a extensão do arquivo
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # Delega o processamento para o módulo específico baseado na extensão
        if ext == '.pdf':
            return process_pdf(file_path)
        elif ext in ['.xls', '.xlsx']:
            return process_excel(file_path)
        elif ext == '.docx':
            return process_docx(file_path)
        elif ext in ['.png', '.jpg', '.jpeg', '.gif']:
            return process_image(file_path)
        elif ext in ['.mp3', '.wav', '.ogg']:
            return process_audio(file_path)
        else:
            # Para outros tipos de arquivo, assume-se que é texto
            return process_txt(file_path)
    except Exception as e:
        # Registra o erro no log e propaga a exceção
        logger.error(f"Erro ao processar documento {file_path}: {e}", exc_info=True)
        raise

def split_into_chunks(text: str, max_chunk_size: int = 1000) -> list:
    """
    Divide o texto em chunks menores.
    Args:
        text (str): Texto a ser dividido.
        max_chunk_size (int): Tamanho máximo de cada chunk.
    Returns:
        list: Lista de chunks de texto.
    """
    # Divide o texto em sentenças
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current_chunk, current_length = [], [], 0

    # Agrupa sentenças em chunks
    for sentence in sentences:
        sent_length = len(sentence)
        if current_length + sent_length > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk, current_length = [], 0
        current_chunk.append(sentence)
        current_length += sent_length

    # Adiciona o último chunk se houver
    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


