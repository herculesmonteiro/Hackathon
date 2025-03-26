# text_utils.py - Processa um TXT, extraindo os dados 
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import os
import logging
import chardet

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

def process_txt(file_path: str) -> list:
    """
    Processa um arquivo de texto e extrai seu conteúdo.
    
    Args:
        file_path (str): Caminho completo para o arquivo de texto.
    
    Returns:
        list: Uma lista contendo o texto extraído do arquivo.
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"O arquivo de texto não foi encontrado: {file_path}")
        
        # Detecta a codificação do arquivo
        with open(file_path, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        
        # Lê o conteúdo do arquivo com a codificação detectada
        with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
            content = file.read()
        
        # Retorna o conteúdo em uma lista
        return [content]
    
    except Exception as e:
        # Captura e registra qualquer erro que possa ocorrer durante o processamento
        logger.error(f"Erro ao processar o arquivo de texto {file_path}: {str(e)}", exc_info=True)
        # Retorna uma lista vazia em caso de erro
        return []

def get_text_metadata(file_path: str) -> dict:
    """
    Extrai metadados básicos de um arquivo de texto.
    
    Args:
        file_path (str): Caminho completo para o arquivo de texto.
    
    Returns:
        dict: Um dicionário contendo os metadados do arquivo de texto.
    """
    try:
        # Obtém informações básicas do arquivo
        file_stats = os.stat(file_path)
        
        # Cria um dicionário com os metadados
        metadata = {
            "filename": os.path.basename(file_path),
            "file_size": file_stats.st_size,
            "creation_time": file_stats.st_ctime,
            "modification_time": file_stats.st_mtime,
            "access_time": file_stats.st_atime
        }
        
        return metadata
    except Exception as e:
        logger.error(f"Erro ao extrair metadados do arquivo de texto {file_path}: {str(e)}", exc_info=True)
        return {}

def is_valid_text_file(file_path: str) -> bool:
    """
    Verifica se um arquivo é um arquivo de texto válido.
    
    Args:
        file_path (str): Caminho completo para o arquivo a ser verificado.
    
    Returns:
        bool: True se o arquivo for um texto válido, False caso contrário.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            file.read()
        return True
    except UnicodeDecodeError:
        # Se falhar com UTF-8, tenta detectar a codificação
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                result = chardet.detect(raw_data)
                encoding = result['encoding']
            with open(file_path, 'r', encoding=encoding) as file:
                file.read()
            return True
        except Exception:
            return False
    except Exception as e:
        logger.error(f"Erro ao validar o arquivo de texto {file_path}: {str(e)}", exc_info=True)
        return False

def count_words(text: str) -> int:
    """
    Conta o número de palavras em um texto.
    
    Args:
        text (str): O texto a ser analisado.
    
    Returns:
        int: O número de palavras no texto.
    """
    try:
        # Divide o texto em palavras e conta
        words = text.split()
        return len(words)
    except Exception as e:
        logger.error(f"Erro ao contar palavras: {str(e)}", exc_info=True)
        return 0
