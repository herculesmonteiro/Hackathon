# # audio_utils.py - Transcrição de arquivos de áudio 
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import os
import logging
import librosa
import numpy as np
import speech_recognition as sr
import whisper
import azure.cognitiveservices.speech as speechsdk

# Configuração do logger para este módulo
logger = logging.getLogger(__name__)
# Carrega o modelo Whisper para transcrição de áudio
whisper_model = whisper.load_model("base", device="cpu")
def transcribe_audio_whisper(file_path: str) -> str:
    """
    Transcreve um arquivo de áudio usando o modelo Whisper.
    Args:
        file_path (str): Caminho para o arquivo de áudio.
    Returns:
        str: Texto transcrito do áudio.
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        # Adiciona o diretório do FFmpeg ao PATH do sistema
        ffmpeg_path = r"C:\GenAI\GenAI_v11\ffmpeg\bin"
        if ffmpeg_path not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + ffmpeg_path
        # Verifica se o FFmpeg está acessível
        if not any(os.path.isfile(os.path.join(path, "ffmpeg.exe")) for path in os.environ["PATH"].split(os.pathsep)):
            raise FileNotFoundError("FFmpeg não encontrado no PATH do sistema.")
        # Realiza a transcrição usando o modelo Whisper
        result = whisper_model.transcribe(file_path, fp16=False)
        return result["text"]
    except Exception as e:
        # Registra o erro e retorna uma string vazia
        logger.error(f"Erro na transcrição do áudio com Whisper: {e}", exc_info=True)
        return ""
def process_audio(file_path: str) -> list:
    """
    Processa um arquivo de áudio, transcrevendo-o e extraindo metadados.
    Args:
        file_path (str): Caminho para o arquivo de áudio.
    Returns:
        list: Lista contendo a transcrição e metadados do áudio.
    """
    try:
        # Tenta transcrever o áudio usando Whisper
        text = transcribe_audio_whisper(file_path)
        # Se a transcrição com Whisper falhar, tenta usar o Google Speech Recognition
        if not text:
            recognizer = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="pt-BR")
        # Carrega o áudio usando librosa para extrair metadados
        y, sr_rate = librosa.load(file_path)
        duration = librosa.get_duration(y=y, sr=sr_rate)
        # Prepara os metadados do áudio
        metadata = f"Duração: {duration:.2f} segundos, Taxa de amostragem: {sr_rate} Hz"
        # Retorna a transcrição e os metadados em uma lista
        return [f"Transcrição do áudio: {text}\n{metadata}"]
    except Exception as e:
        # Registra o erro e retorna uma lista vazia
        logger.error(f"Erro no processamento do áudio {file_path}: {e}", exc_info=True)
        return []
class RingBuffer:
    """
    Implementa um buffer circular para armazenamento temporário de dados de áudio.
    """
    def __init__(self, size):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.float32)
        self.index = 0
    def extend(self, data):
        """
        Adiciona novos dados ao buffer.
        Args:
            data (array-like): Dados a serem adicionados ao buffer.
        """
        data_len = len(data)
        if data_len >= self.size:
            self.buffer = data[-self.size:]
            self.index = 0
        else:
            space_left = self.size - self.index
            if data_len > space_left:
                self.buffer[self.index:] = data[:space_left]
                self.buffer[:data_len-space_left] = data[space_left:]
                self.index = data_len - space_left
            else:
                self.buffer[self.index:self.index+data_len] = data
                self.index = (self.index + data_len) % self.size
    def get(self):
        """
        Retorna o conteúdo atual do buffer.
        Returns:
            numpy.ndarray: Conteúdo atual do buffer.
        """
        return np.concatenate((self.buffer[self.index:], self.buffer[:self.index]))# audio_utils.py - Transcrição de arquivos de áudio para o Super-Agentes Inteligentes
# Autor: Hercules Monteiro
# Data: 16/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import os
import logging
import librosa
import numpy as np
import speech_recognition as sr
import whisper
logger = logging.getLogger(__name__)
whisper_model = whisper.load_model("base", device="cpu")
def process_audio(file_path: str) -> list:
    """
    Processa um arquivo de áudio, transcrevendo-o e extraindo metadados.
    Args:
        file_path (str): Caminho para o arquivo de áudio.
    Returns:
        list: Lista contendo a transcrição e metadados do áudio.
    """
    try:
        # Tenta transcrever o áudio usando Whisper
        text = transcribe_audio_whisper(file_path)
        # Se a transcrição com Whisper falhar, tenta usar o Google Speech Recognition
        if not text:
            recognizer = sr.Recognizer()
            with sr.AudioFile(file_path) as source:
                audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="pt-BR")
        # Carrega o áudio usando librosa para extrair metadados
        y, sr_rate = librosa.load(file_path)
        duration = librosa.get_duration(y=y, sr=sr_rate)
        # Prepara os metadados do áudio
        metadata = f"Duração: {duration:.2f} segundos, Taxa de amostragem: {sr_rate} Hz"
        # Retorna a transcrição e os metadados em uma lista
        return [f"Transcrição do áudio: {text}\n{metadata}"]
    except Exception as e:
        # Registra o erro e retorna uma lista vazia
        logger.error(f"Erro no processamento do áudio {file_path}: {e}", exc_info=True)
        return []
def transcribe_audio_whisper(file_path: str) -> str:
    """
    Transcreve um arquivo de áudio usando o modelo Whisper.
    Args:
        file_path (str): Caminho para o arquivo de áudio.
    Returns:
        str: Texto transcrito do áudio.
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        # Adiciona o diretório do FFmpeg ao PATH do sistema
        ffmpeg_path = r"C:\HM\GenAI_v11\ffmpeg\bin"
        if ffmpeg_path not in os.environ["PATH"]:
            os.environ["PATH"] += os.pathsep + ffmpeg_path
        # Verifica se o FFmpeg está acessível
        if not any(os.path.isfile(os.path.join(path, "ffmpeg.exe")) for path in os.environ["PATH"].split(os.pathsep)):
            raise FileNotFoundError("FFmpeg não encontrado no PATH do sistema.")
        # Realiza a transcrição usando o modelo Whisper
        result = whisper_model.transcribe(file_path, fp16=False)
        return result["text"]
    except Exception as e:
        # Registra o erro e retorna uma string vazia
        logger.error(f"Erro na transcrição do áudio com Whisper: {e}", exc_info=True)
        return ""
class RingBuffer:
    """
    Implementa um buffer circular para armazenamento temporário de dados de áudio.
    """
    def __init__(self, size):
        self.size = size
        self.buffer = np.zeros(size, dtype=np.float32)
        self.index = 0
    def extend(self, data):
        """
        Adiciona novos dados ao buffer.
        Args:
            data (array-like): Dados a serem adicionados ao buffer.
        """
        data_len = len(data)
        if data_len >= self.size:
            self.buffer = data[-self.size:]
            self.index = 0
        else:
            space_left = self.size - self.index
            if data_len > space_left:
                self.buffer[self.index:] = data[:space_left]
                self.buffer[:data_len-space_left] = data[space_left:]
                self.index = data_len - space_left
            else:
                self.buffer[self.index:self.index+data_len] = data
                self.index = (self.index + data_len) % self.size
    def get(self):
        """
        Retorna o conteúdo atual do buffer.
        Returns:
            numpy.ndarray: Conteúdo atual do buffer.
        """
        return np.concatenate((self.buffer[self.index:], self.buffer[:self.index]))
