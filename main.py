# main.py - Plataforma busca pessoas desaparecidas  
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import logging
import os
import tkinter as tk
from tkinter import messagebox
from chatbot_gui import ChatbotGUI, BASE_CHROMA_PERSIST_DIR, PDF_DIR

# Configuração inicial detalhada do logging para registrar eventos importantes no arquivo log.txt.
logging.basicConfig(
    filename='log.txt',
    level=logging.DEBUG,  # Alterado para DEBUG para maior detalhamento dos logs
    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s',
    filemode='a'
)

logger = logging.getLogger(__name__)

def criar_diretorio_se_nao_existir(caminho: str):
    """
    Cria o diretório especificado se ele não existir.

    Args:
        file_path (str): Caminho completo do diretório a ser verificado/criado.
    """
    try:
        if not os.path.exists(file_path):
            os.makedirs(file_path, exist_ok=True)
            logger.info(f"[main] Diretório criado com sucesso: {file_path}")
        else:
            logger.debug(f"[main] Diretório já existente: {file_path}")
    except Exception as e:
        logger.error(f"[main] Falha ao criar diretório {file_path}: {str(e)}", exc_info=True)
        raise

def main():
    """
    Função principal que inicializa a aplicação chatbot GenAI.
    """
    try:
        # Verifica e cria diretórios essenciais para o funcionamento correto da aplicação.
        criar_diretorios_essenciais()

        # Inicializa a interface gráfica principal do chatbot.
        logger.info("[main] Inicializando a interface gráfica ChatbotGUI.")
        app = ChatbotGUI()
        app.mainloop()
        logger.info("[main] Interface gráfica ChatbotGUI encerrada normalmente.")

    except Exception as e:
        # Captura qualquer exceção crítica durante a inicialização da aplicação.
        logger.critical(f"[main] Falha crítica na inicialização da aplicação: {str(e)}", exc_info=True)
        tk.messagebox.showerror(
            "Erro Fatal", f"Aplicação encerrada devido a um erro crítico:\n{str(e)}"
        )
        raise SystemExit("Erro fatal. Verifique log.txt para mais detalhes.")

def criar_diretorios_essenciais():
    """
    Verifica e cria os diretórios essenciais utilizados pela aplicação.
    """
    try:
        diretorios = [BASE_CHROMA_PERSIST_DIR, PDF_DIR]
        for diretorio in diretorios:
            if not os.path.exists(diretorio):
                os.makedirs(diretorio, exist_ok=True)
                logger.info(f"[criar_diretorios_essenciais] Diretório criado: {diretorio}")
            else:
                logger.debug(f"[criar_diretorios_essenciais] Diretório já existe: {diretorio}")
    except Exception as e:
        logger.error(f"[criar_diretorios_essenciais] Erro ao criar diretórios essenciais: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    # Inicia o programa principal GenAI.
    logger.info("[main] Iniciando o programa GenAI.")
    main()
