# pdf_utils.py - Processa um PDF, extraindo os dados  
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import PyPDF2
import logging
import os
from typing import List
import pikepdf
import io

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

def process_pdf(file_path: str) -> List[str]:
    """
    Processa um arquivo PDF e extrai o texto de todas as páginas.
    Funciona com PDFs protegidos e não protegidos.

    Args:
        file_path (str): Caminho completo para o arquivo PDF.

    Returns:
        List[str]: Uma lista onde cada elemento é o texto extraído de uma página do PDF.
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"O arquivo PDF não foi encontrado: {file_path}")

        # Lista para armazenar o texto de cada página
        pages_text = []

        # Tenta abrir o PDF com pikepdf primeiro (para PDFs protegidos)
        try:
            with pikepdf.Pdf.open(file_path) as pdf:
                # Converte o pikepdf.Pdf para um objeto que PyPDF2 pode ler
                pdf_bytes = io.BytesIO(pdf.save())
                pdf_reader = PyPDF2.PdfReader(pdf_bytes)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append(text)
        except Exception as e:
            # Se falhar com pikepdf, tenta abrir normalmente com PyPDF2
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        pages_text.append(text)

        # Retorna a lista com o texto de todas as páginas
        return pages_text

    except Exception as e:
        # Captura quaisquer erros que possam ocorrer
        logger.error(f"Erro ao processar o PDF {file_path}: {str(e)}", exc_info=True)
        return []

def get_pdf_metadata(file_path: str) -> dict:
    """
    Extrai metadados de um arquivo PDF.

    Args:
        file_path (str): Caminho completo para o arquivo PDF.

    Returns:
        dict: Um dicionário contendo os metadados do PDF.
    """
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            metadata = pdf_reader.metadata

            # Cria um dicionário com os metadados relevantes
            return {
                "Title": metadata.get('/Title', 'Sem título'),
                "Author": metadata.get('/Author', 'Autor desconhecido'),
                "Subject": metadata.get('/Subject', 'Sem assunto'),
                "Creator": metadata.get('/Creator', 'Criador desconhecido'),
                "Producer": metadata.get('/Producer', 'Produtor desconhecido'),
                "CreationDate": metadata.get('/CreationDate', 'Data de criação desconhecida'),
                "ModDate": metadata.get('/ModDate', 'Data de modificação desconhecida'),
                "NumberOfPages": len(pdf_reader.pages)
            }
    except Exception as e:
        logger.error(f"Erro ao extrair metadados do PDF {file_path}: {str(e)}", exc_info=True)
        return {}

# Esta função pode ser usada para validar se um arquivo é um PDF válido
def is_valid_pdf(file_path: str) -> bool:
    """
    Verifica se um arquivo é um PDF válido.

    Args:
        file_path (str): Caminho completo para o arquivo a ser verificado.

    Returns:
        bool: True se o arquivo for um PDF válido, False caso contrário.
    """
    try:
        with open(file_path, 'rb') as file:
            PyPDF2.PdfReader(file)
        return True
    except PyPDF2.errors.PdfReadError:
        return False
    except Exception as e:
        logger.error(f"Erro ao validar o PDF {file_path}: {str(e)}", exc_info=True)
        return False
