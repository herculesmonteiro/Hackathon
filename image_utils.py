# image_utils.py - Processa uma imagem, extraindo texto via OCR
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================

from PIL import Image
import pytesseract
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer
import logging
import os
import requests
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.exceptions import AzureError
from azure.core.credentials import AzureKeyCredential
from bs4 import BeautifulSoup
import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from urllib.parse import urljoin

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Configuração do caminho para o executável do Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'C:\Tesseract-OCR\tesseract.exe'

# Carregamento dos modelos de processamento de imagem
image_captioning_model = VisionEncoderDecoderModel.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
image_processor = ViTImageProcessor.from_pretrained("nlpconnect/vit-gpt2-image-captioning")
tokenizer = AutoTokenizer.from_pretrained("nlpconnect/vit-gpt2-image-captioning")

# Configurações da API Azure AI Vision
VISION_ENDPOINT = "coloque seu endpoint aqui"
VISION_KEY = "coloque sua chave aqui"
DESAPARECIDOS_URL = "https://www.desaparecidos.pr.gov.br/desaparecidos"

# Diretório temporário para imagens do site
TEMP_DIR = os.path.join(os.getcwd(), "temp_images")
if not os.path.exists(TEMP_DIR):
    try:
        os.makedirs(TEMP_DIR)
        logging.info(f"Diretório criado: {TEMP_DIR}")
    except Exception as e:
        logging.error(f"Erro ao criar diretório {TEMP_DIR}: {str(e)}")

def process_image(file_path: str) -> list:
    """
    Processa uma imagem, extraindo texto via OCR e gerando uma descrição.
    Args:
        file_path (str): Caminho para o arquivo de imagem.
    Returns:
        list: Lista contendo uma string com a descrição da imagem, texto extraído e metadados.
    """
    try:
        # Abre a imagem e converte para RGB
        image = Image.open(file_path).convert('RGB')

        # Extrai texto da imagem usando OCR
        ocr_text = pytesseract.image_to_string(image, lang="por")

        # Prepara a imagem para o modelo de captioning
        pixel_values = image_processor(images=image, return_tensors="pt").pixel_values

        # Gera a descrição da imagem
        generated_ids = image_captioning_model.generate(pixel_values, max_length=50)
        caption = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # Extrai metadados da imagem
        metadata = f"Formato: {image.format}, Tamanho: {image.size}, Modo: {image.mode}"

        # Analisa a imagem usando Azure AI Vision
        azure_analysis = analyze_image(file_path)

        # Verifica se a foto aparece no site de desaparecidos
        desaparecidos_info = check_photo_on_desaparecidos_site(file_path)

        # Combina todas as informações
        result = [
            f"Descrição da imagem: {caption}\n"
            f"Texto extraído: {ocr_text}\n"
            f"{metadata}\n"
            f"Análise Azure AI Vision: {azure_analysis}\n"
            f"Informações de Desaparecidos: {desaparecidos_info}"
        ]

        return result

    except Exception as e:
        # Registra o erro e retorna uma lista vazia
        logger.error(f"Erro no processamento da imagem {file_path}: {e}", exc_info=True)
        return []

def analyze_image(image_path):
    """
    Função para realizar análise de imagem usando Azure AI Vision.
    """
    try:
        logging.info(f"Iniciando análise da imagem: {image_path}")
        client = ImageAnalysisClient(
            endpoint=VISION_ENDPOINT,
            credential=AzureKeyCredential(VISION_KEY)
        )

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        features = [
            VisualFeatures.CAPTION,
            VisualFeatures.TAGS,
            VisualFeatures.OBJECTS
        ]

        result = client.analyze(image_data, features)
        # Log do resultado bruto da API
        logging.debug(f"Resultado bruto da API: {result}")

        analysis_result = []

        # Adicionar descrição
        if result.caption:
            analysis_result.append(f"**Descrição:** {result.caption.text} (confiança: {result.caption.confidence:.2f})")

        # Adicionar tags
        if result.tags:
            if isinstance(result.tags[0], str):  # Caso as tags sejam strings simples
                tags = [tag for tag in result.tags]
                analysis_result.append(f"**Tags detectadas:**\n - " + "\n - ".join(tags))
            else:  # Caso as tags sejam objetos com atributos
                tags = [f"{tag.name} (confiança: {tag.confidence:.2f})" for tag in result.tags]
                analysis_result.append(f"**Tags detectadas:**\n - " + "\n - ".join(tags))

        # Adicionar objetos detectados
        if result.objects:
            objects = [f"{obj.name} em {obj.bounding_box}" for obj in result.objects]
            analysis_result.append(f"**Objetos detectados:**\n - " + "\n - ".join(objects))

        return "\n".join(analysis_result)

    except Exception as e:
        error_msg = f"Erro na análise da imagem: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return error_msg



def check_photo_on_desaparecidos_site(image_path):
    """
    Verifica se a foto aparece no site de desaparecidos.
    Args:
        image_path (str): Caminho para a imagem local.
    Returns:
        str: Mensagem com os resultados da busca.
    """
    try:
        logging.info("Verificando se a foto aparece no site de desaparecidos...")
        response = requests.get(DESAPARECIDOS_URL)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            images = soup.find_all('img')

            for img in images:
                img_url = img['src']
                absolute_img_url = urljoin(DESAPARECIDOS_URL, img_url)
                img_response = requests.get(absolute_img_url)

                if img_response.status_code == 200:
                    site_image_path = os.path.join(TEMP_DIR, os.path.basename(image_path))
                    with open(site_image_path, "wb") as f:
                        f.write(img_response.content)

                    if compare_images(image_path, site_image_path):
                        dados_encontrados = extract_data_from_site(soup, absolute_img_url)
                        return f"✅ **Foto encontrada no site dos desaparecidos.**\n{dados_encontrados}"

                    os.remove(site_image_path)

            return "❌ **A foto não foi encontrada no site dos desaparecidos.**"

    except Exception as e:
        error_msg = f"Erro ao verificar foto no site de desaparecidos: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return error_msg


def compare_images(image1_path, image2_path):
    """
    Realiza a comparação de duas imagens usando OpenCV.
    Retorna True se forem similares.
    """
    try:
        image1 = cv2.imread(image1_path)
        image2 = cv2.imread(image2_path)

        if image1 is None or image2 is None:
            logging.error("Erro ao carregar uma ou ambas as imagens para comparação.")
            return False

        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

        gray1 = cv2.resize(gray1, (300, 300))
        gray2 = cv2.resize(gray2, (300, 300))

        score, _ = ssim(gray1, gray2, full=True)
        return score > 0.80
    except Exception as e:
        logging.error(f"Erro ao comparar imagens: {e}")
        return False

def extract_data_from_site(soup, img_url):
    """
    Extrai dados reais do site com base na URL da imagem encontrada.
    Args:
        soup (BeautifulSoup): Objeto BeautifulSoup contendo o HTML do site.
        img_url (str): URL da imagem encontrada.
    Returns:
        str: Dados formatados encontrados abaixo da imagem no site.
    """
    try:
        img_tag = soup.find('img', {'src': img_url})
        if img_tag and img_tag.parent:
            parent_tag = img_tag.parent
            dados_texto = parent_tag.get_text(separator="\n").strip()
            dados_encontrados = {}

            for linha in dados_texto.split("\n"):
                if ':' in linha:
                    chave, valor = linha.split(":", 1)
                    dados_encontrados[chave.strip()] = valor.strip()

            formatted_data = "\n".join([f"{k}: {v}" for k, v in dados_encontrados.items()])
            return formatted_data

        return "Nenhum dado adicional encontrado."
    except Exception as e:
        logging.error(f"Erro ao extrair dados do site: {e}")
        return "Erro ao extrair dados do site."


def validate_image(file_path: str) -> bool:
    """
    Valida se o arquivo é uma imagem válida.
    Args:
        file_path (str): Caminho para o arquivo de imagem.
    Returns:
        bool: True se for uma imagem válida, False caso contrário.
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.error(f"Arquivo inválido ou corrompido: {file_path}. Erro: {e}")
        return False

def get_image_metadata(file_path: str) -> dict:
    """
    Extrai metadados detalhados de uma imagem.
    Args:
        file_path (str): Caminho para o arquivo de imagem.
    Returns:
        dict: Dicionário contendo os metadados da imagem.
    """
    try:
        with Image.open(file_path) as img:
            metadata = {
                "filename": os.path.basename(file_path),
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
            }
            if "exif" in img.info:
                exif = img._getexif()
                if exif:
                    metadata["exif"] = {
                        ExifTags.TAGS[k]: v
                        for k, v in exif.items()
                        if k in ExifTags.TAGS
                    }
            return metadata
    except Exception as e:
        logger.error(f"Erro ao extrair metadados da imagem {file_path}: {e}", exc_info=True)
        return {}

def resize_image(file_path: str, max_size: int = 1024) -> Image.Image:
    """
    Redimensiona uma imagem mantendo a proporção.
    Args:
        file_path (str): Caminho para o arquivo de imagem.
        max_size (int): Tamanho máximo para o lado maior da imagem.
    Returns:
        Image.Image: Imagem redimensionada.
    """
    try:
        with Image.open(file_path) as img:
            img.thumbnail((max_size, max_size))
        return img
    except Exception as e:
        logger.error(f"Erro ao redimensionar a imagem {file_path}: {e}", exc_info=True)
        return None


def search_missing_persons(image_path):
    """
    Analisa a imagem e verifica se ela aparece no site de desaparecidos.
    Args:
    image_path (str): Caminho para o arquivo de imagem.
    Returns:
    str: Mensagem com os resultados da análise e busca.
    """
    try:
        logging.info(f"Iniciando busca por pessoas desaparecidas: {image_path}")
        
        # Analisar a imagem usando Azure AI Vision
        client = ImageAnalysisClient(
            endpoint=VISION_ENDPOINT,
            credential=AzureKeyCredential(VISION_KEY)
        )
        
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        
        features = [
            VisualFeatures.CAPTION,
            VisualFeatures.TAGS,
            VisualFeatures.OBJECTS
        ]
        
        result = client.analyze(image_data, features)
        
        analysis_results = []
        
        if result.caption:
            analysis_results.append(f"Descrição: {result.caption.text} (confiança: {result.caption.confidence:.2f})")
        
        if result.tags:
            tags = [f"{tag.name} (confiança: {tag.confidence:.2f})" for tag in result.tags if hasattr(tag, 'name') and hasattr(tag, 'confidence')]
            analysis_results.append(f"Tags: {', '.join(tags)}")
        
        if result.objects:
            objects = [f"{obj.name} em {obj.bounding_box}" for obj in result.objects if hasattr(obj, 'name') and hasattr(obj, 'bounding_box')]
            analysis_results.append(f"Objetos: {', '.join(objects)}")
        
        # Verificar no site de desaparecidos
        desaparecidos_info = check_photo_on_desaparecidos_site(image_path)
        analysis_results.append(desaparecidos_info)
        
        return "\n".join(analysis_results)
    
    except Exception as e:
        error_msg = f"Erro na busca por pessoas desaparecidas: {str(e)}"
        logging.error(error_msg, exc_info=True)
        return error_msg
