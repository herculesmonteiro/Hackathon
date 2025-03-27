# chatbot_gui.py - Interface do usuário
# Autor: Hercules Monteiro
# Data: 26/03/2025
# Versão: 1.0
# ============================================================================
# 1. IMPORTAÇÕES NECESSÁRIAS
# ============================================================================
import tkinter as tk
from tkinter import END, filedialog, simpledialog
import os
import shutil
import logging
import webbrowser
import chromadb
from document_processor import process_document, split_into_chunks, generate_metadata
from embedding_utils import embedding_model
from chroma_utils import get_snippet_chroma, refine_snippet_chroma, sanitize_collection_name
from llm_utils import ChatOpenAI
from langchain_openai import ChatOpenAI
from image_utils import analyze_image, search_missing_persons
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageTk


# Configuração do logger para este módulo
logger = logging.getLogger(__name__)

# Constantes globais
OPENAI_API_KEY = "colocar sua chave aqui"
DEEPSEEK_API_KEY = "colocar sua chave aqui"

# Diretórios principais do projeto.
BASE_CHROMA_PERSIST_DIR = "C:/colecoes"
PDF_DIR = "C:/uploads"
FOTOS_DIR = os.path.join(os.getcwd(), "C:/uploads/2025")

class ChatbotGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pessoas desaparecidas")
        self.current_collection = None
        self.llm_choice = tk.StringVar(value="Local")
        # Inicializar current_prompt como StringVar
        self.current_prompt = tk.StringVar(value=(
            "Você DEVE responder usando APENAS o contexto fornecido!\n"
            "Contexto:\n---\n{context}\n---\n"
            "Pergunta: {query}\n"
            "Resposta detalhada e técnica baseada EXCLUSIVAMENTE no contexto, incluindo informações relevantes dos documentos e coleções.\n"
            "Se necessário, utilize os sites externos configurados para buscar informações adicionais sobre pessoas desaparecidas."
        ))

        self.client_var = tk.StringVar(value="Selecionar Desaparecido")
        self.collection_var = tk.StringVar(value="Selecionar Coleção")
        self.setup_ui()
        self.bind_events()
        
        # Adicionando suporte para pesquisa em sites externos
        self.external_sites = [
            "https://www.desaparecidos.pr.gov.br/desaparecidos",
            # Adicione outros sites relevantes aqui
        ]


    def search_external_sites(self, query):
        """
        Pesquisa informações sobre pessoas desaparecidas em sites externos.
        Args:
            query (str): Termo de busca.
        Returns:
            list: Lista de resultados encontrados nos sites externos.
        """
        results = []
        for site in self.external_sites:
            try:
                response = requests.get(site)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for item in soup.select(".result-item"):  # Exemplo de seletor CSS
                        name = item.select_one(".name").text.strip() if item.select_one(".name") else "Nome não disponível"
                        details = item.select_one(".details").text.strip() if item.select_one(".details") else "Detalhes não disponíveis"
                        link = item.select_one("a")["href"] if item.select_one("a") else "Link não disponível"
                        results.append(f"{name}: {details} ({link})")
                else:
                    logger.warning(f"Falha ao acessar {site}: {response.status_code}")
            except Exception as e:
                logger.error(f"Erro ao pesquisar no site {site}: {str(e)}", exc_info=True)

        return results if results else ["Nenhum resultado encontrado nos sites externos."]




    def setup_ui(self):
        # Configuração da interface do usuário
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        left_frame = tk.Frame(self)
        left_frame.grid(row=0, column=0, rowspan=3, sticky="nswe", padx=10, pady=5)

        tk.Label(left_frame, text="Desaparecido:").pack(fill='x', pady=2)
        self.client_menu = tk.OptionMenu(left_frame, self.client_var, *self.get_clients())
        self.client_menu.pack(fill='x', pady=2)

        tk.Label(left_frame, text="Coleção:").pack(fill='x', pady=2)
        self.collection_menu = tk.OptionMenu(left_frame, self.collection_var, "Selecionar Coleção")
        self.collection_menu.pack(fill='x', pady=2)

        self.add_client_btn = tk.Button(left_frame, text="Adicionar Desaparecido", command=self.add_client)
        self.add_client_btn.pack(fill='x', pady=5)

        self.upload_btn = tk.Button(left_frame, text="Upload Documento", command=self.upload_document)
        self.upload_btn.pack(fill='x', pady=5)

        tk.Label(left_frame, text="Modelo LLM:").pack(fill='x', pady=2)
        self.llm_menu = tk.OptionMenu(left_frame, self.llm_choice, "Local", "OpenAI", "Deepseek")
        self.llm_menu.pack(fill='x', pady=2)

        self.edit_prompt_btn = tk.Button(left_frame, text="Editar Prompt", command=self.edit_prompt)
        self.edit_prompt_btn.pack(fill='x', pady=5)

        # Novo botão para processar imagens
        self.process_images_btn = tk.Button(left_frame, text="Processar Imagens", command=self.process_images)
        self.process_images_btn.pack(fill='x', pady=5)

        self.chat_area = tk.Text(self, height=20, width=50, state="disabled")
        self.chat_area.grid(row=1, column=1, columnspan=2, pady=10, padx=5, sticky="nsew")

        self.input_area = tk.Text(self, height=3)
        self.input_area.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=2, padx=5, sticky="ew")

        self.send_btn = tk.Button(btn_frame, text="Enviar", command=self.send_message)
        self.send_btn.pack(side='left', fill='x', expand=True)

        self.clear_btn = tk.Button(btn_frame, text="Limpar", command=self.clear_chat)
        self.clear_btn.pack(side='left', fill='x', expand=True)

    def process_images(self):
        """Processa imagens no diretório 'fotos' e exibe resultados."""
        if not os.path.exists(FOTOS_DIR):
            self.display_message("Diretório 'fotos' não encontrado.")
            return

        for foto in os.listdir(FOTOS_DIR):
            foto_path = os.path.join(FOTOS_DIR, foto)
            if os.path.isfile(foto_path) and foto.lower().endswith(('.jpg', '.jpeg', '.png')):
                self.display_message(f"Analisando: {foto}")
                self.display_image(foto_path)  # Exibe a imagem no chat

                result = analyze_image(foto_path)
                self.display_message(result)

                search_result = search_missing_persons(foto_path)
                self.display_message(search_result)


    def bind_events(self):
        # Vincula eventos aos elementos da interface
        self.client_var.trace_add('write', lambda *args: self.update_collection_menu())
        self.input_area.bind("<Return>", lambda event: self.send_message())
        self.protocol("WM_DELETE_WINDOW", self.safe_shutdown)

    def get_clients(self):
        # Obtém a lista de desparecidos do diretório de uploads
        try:
            clients = [d for d in os.listdir(PDF_DIR) if os.path.isdir(os.path.join(PDF_DIR, d))]
            return ["Selecionar Desaparecido"] + clients
        except Exception as e:
            logger.error(f"Erro ao obter desaparecido: {str(e)}", exc_info=True)
            return ["Selecionar Desaparecido"]

    def add_client(self):
        # Adiciona um novo desaparecido
        new_client = simpledialog.askstring("Novo Desaparecido", "Digite o nome do novo desaparecido:")
        if new_client:
            client_path = os.path.join(PDF_DIR, new_client)
            os.makedirs(client_path, exist_ok=True)
            self.client_menu['menu'].add_command(
                label=new_client,
                command=tk._setit(self.client_var, new_client)
            )
            self.client_var.set(new_client)

    def upload_document(self):
        # Inicia o processo de upload de documento
        try:
            file_types = [("Documentos", "*.pdf *.docx *.xlsx *.txt *.png *.jpg *.jpeg *.gif *.mp3 *.wav *.ogg")]
            file_path = filedialog.askopenfilename(filetypes=file_types)
            if file_path:
                self.process_upload(file_path)
        except Exception as e:
            self.handle_error("upload", e)

    def process_upload(self, file_path):
        # Processa o upload do documento
        try:
            client_name = self.client_var.get()
            if not client_name or client_name == "Selecionar Desaparecido":
                raise ValueError("Selecione um desaparecido antes de fazer upload.")
            client_upload_dir = os.path.join(PDF_DIR, client_name)
            os.makedirs(client_upload_dir, exist_ok=True)
            new_file_path = os.path.join(client_upload_dir, os.path.basename(file_path))
            shutil.copy(file_path, new_file_path)
            client_path = os.path.join(BASE_CHROMA_PERSIST_DIR, client_name)
            client = chromadb.PersistentClient(path=client_path)
            collection_name = sanitize_collection_name(os.path.basename(new_file_path))
            collection = client.get_or_create_collection(collection_name)
            textos = process_document(new_file_path)
            for idx, texto in enumerate(textos):
                chunks = split_into_chunks(texto)
                for chunk_idx, chunk in enumerate(chunks):
                    metadata = generate_metadata(chunk, os.path.basename(new_file_path), client_name, new_file_path)
                    embedding = embedding_model.encode(chunk).tolist()
                    collection.add(
                        ids=[f"{collection_name}chunk{idx}{chunk_idx}"],
                        documents=[chunk],
                        metadatas=[metadata],
                        embeddings=[embedding]
                    )
            self.update_collection_menu()
            self.display_message(f"Documento {os.path.basename(new_file_path)} processado com sucesso!")
        except chromadb.errors.UniqueConstraintError as e:
            self.display_message(f"Documento já existe: {str(e)}")
        except Exception as e:
            self.handle_error("processamento de upload", e)

    def send_message(self, event=None):
        try:
            query = self.input_area.get("1.0", END).strip()
            if not query:
                return

            client_name = self.client_var.get()
            collection_name = self.collection_var.get()

            if not self.validate_client_collection(client_name, collection_name):
                return

            self.display_message(f"\nVocê: {query}")

            # Pesquisa em coleções locais
            if collection_name == "Pesquisar em Todas as Coleções":
                self.search_all_collections(client_name, query)
            else:
                client_path = os.path.join(BASE_CHROMA_PERSIST_DIR, client_name)
                client = chromadb.PersistentClient(path=client_path)
                collection = client.get_collection(collection_name)
                self.process_query(collection, query)

            # Pesquisa em sites externos
            external_results = self.search_external_sites(query)  # Corrigido aqui
            if external_results:
                self.display_message("\nResultados de sites externos:")
                for result in external_results:
                    self.display_message(result)

            self.input_area.delete("1.0", END)

        except Exception as e:
            self.handle_error("envio de mensagem", e)



    def search_all_collections(self, client_name, query):
        # Pesquisa em todas as coleções do desaparecido
        client_path = os.path.join(BASE_CHROMA_PERSIST_DIR, client_name)
        client = chromadb.PersistentClient(path=client_path)
        collection_names = client.list_collections()
        combined_context = []
        all_files = set()
        for col_name in collection_names:
            try:
                current_collection = client.get_collection(col_name)
                results = current_collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=['documents', 'metadatas']
                )
                if results and results.get('documents'):
                    for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
                        if query.lower() in doc.lower():
                            combined_context.append(f"Coleção: {col_name}\n{doc[:500]}...")
                            if 'file_path' in meta:
                                all_files.add(meta['file_path'])
            except Exception as e:
                logger.error(f"Erro ao pesquisar na coleção {col_name}: {str(e)}")
        if combined_context:
            response_text = "\n\n".join(combined_context)
            self.display_message(f"Chatbot (Pesquisa em Todas):\n{response_text}")
            self.display_file_links(list(all_files))
        else:
            self.display_message("Chatbot (Pesquisa em Todas):\nNenhum resultado relevante encontrado em nenhuma coleção.")
        if self.llm_choice.get() != "Local":
            context = "\n\n".join(combined_context)[:2000]
            self.generate_llm_response(context, query, list(all_files))

    def process_query(self, collection, query):
        # Processa a consulta em uma coleção específica
        if self.llm_choice.get() != "Local":
            if self.llm_choice.get() == "Deepseek" and not DEEPSEEK_API_KEY:
                self.display_message("Erro: Chave Deepseek não configurada!")
                return
            if self.llm_choice.get() == "OpenAI" and not OPENAI_API_KEY:
                self.display_message("Erro: Chave OpenAI não configurada!")
                return
            snippet_result = get_snippet_chroma(collection, query, embedding_model)
            refined_result = refine_snippet_chroma(collection, snippet_result['text'], embedding_model)
            context = refined_result['text']
            if not context.strip():
                results = collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=['documents']
                )
                context = "\n\n".join([doc if isinstance(doc, str) else ' '.join(doc) for doc in results['documents'][0]])[:2000]
            self.generate_llm_response(context, query, refined_result['files'])
        else:
            total_docs = collection.count()
            n_results = min(5, total_docs) if total_docs > 0 else 1
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas']
            )
            response_text = "\n\n".join([
                f"\U0001f4c4 Documento {i+1} ({meta.get('titulo', 'Sem título') if isinstance(meta, dict) else 'Sem título'}):\n"
                f"{doc[:500]}{'...' if len(doc) > 500 else ''}"
            for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0]))
            ])
            self.display_message(f"Chatbot (Local):\n{response_text if response_text else 'Nenhum resultado relevante encontrado.'}")
            self.display_file_links([meta.get('file_path', '') if isinstance(meta, dict) else '' for meta in results['metadatas'][0]])

    def generate_llm_response(self, context, query, files):
        # Gera resposta usando o modelo de linguagem escolhido
        try:
            if self.llm_choice.get() == "OpenAI":
                llm = ChatOpenAI(
                    api_key=OPENAI_API_KEY,
                    model_name="gpt-3.5-turbo",
                    temperature=0.7
                )
            elif self.llm_choice.get() == "Deepseek":
                llm = ChatOpenAI(
                    api_key=DEEPSEEK_API_KEY,
                    model_name="deepseek-chat",
                    openai_api_base="https://api.deepseek.com/v1",
                    temperature=0.7
                )
            prompt = self.current_prompt.get().format(context=context, query=query)
            response = llm.invoke(prompt)
            self.display_message(
                f"Chatbot ({self.llm_choice.get()}):\n{response.content}")
            self.display_file_links(files)
        except Exception as e:
            self.handle_error("geração de resposta LLM", e)

    def display_file_links(self, files):
        unique_files = list(set([f for f in files if f]))
        if unique_files:
            self.display_message("\n🔗 Documentos relacionados:")
            for file_path in unique_files:
                if os.path.exists(file_path) or file_path.startswith("http"):
                    display_name = os.path.basename(file_path) if not file_path.startswith("http") else file_path
                    self.chat_area.config(state="normal")
                    self.chat_area.insert(
                        END, f"\n - {display_name} ", "link"
                    )
                    self.chat_area.tag_config(
                        "link", foreground="blue", underline=1
                    )
                    self.chat_area.tag_bind(
                        "link", "<Button-1>", lambda e, path=file_path: webbrowser.open(path)  # Corrigido aqui
                    )
                    self.chat_area.config(state="disabled")


    def edit_prompt(self):
        prompt_editor = tk.Toplevel(self)
        prompt_editor.title("Editar Prompt")
        editor = tk.Text(prompt_editor, width=80, height=20)
        editor.pack(padx=10, pady=10)
        editor.insert("1.0", self.current_prompt.get())
        def save_prompt():
            self.current_prompt.set(editor.get("1.0", END))
            prompt_editor.destroy()
        tk.Button(prompt_editor, text="Salvar", command=save_prompt).pack()

    def validate_client_collection(self, client, collection):
        if client == "Selecionar Desaparecido" or collection == "Selecionar Coleção":
            self.display_message(
                "Erro: Selecione Desaparecido e coleção válidos.")
            return False
        client_path = os.path.join(BASE_CHROMA_PERSIST_DIR, client)
        if not os.path.exists(client_path):
            self.display_message(
                f"Erro: Desaparecido '{client}' não encontrado.")
            return False
        try:
            chroma_client = chromadb.PersistentClient(path=client_path)
            collection_names = chroma_client.list_collections()
            if collection != "Pesquisar em Todas as Coleções" and collection not in collection_names:
                raise ValueError(f"Coleção {collection} não existe")
            return True
        except Exception as e:
            self.display_message(
                f"Erro: Coleção '{collection}' não existe.")
            logger.error(f"Validação falhou: {str(e)}")
            return False

    def update_collection_menu(self):
        client_name = self.client_var.get()
        if client_name and client_name != "Selecionar Desaparecido":
            try:
                client_path = os.path.join(
                    BASE_CHROMA_PERSIST_DIR, client_name)
                client = chromadb.PersistentClient(path=client_path)
                collection_names = client.list_collections()
                menu = self.collection_menu['menu']
                menu.delete(0, 'end')
                menu.add_command(
                    label="Pesquisar em Todas as Coleções",
                    command=tk._setit(self.collection_var,
                    "Pesquisar em Todas as Coleções")
                )
                for col in ["Selecionar Coleção"] + collection_names:
                    menu.add_command(
                        label=col,
                        command=tk._setit(self.collection_var, col)
                    )
            except Exception as e:
                self.handle_error("atualização de coleções", e)

    def display_message(self, message):
        self.chat_area.config(state="normal")
        self.chat_area.insert(END, f"\n{message}")
        self.chat_area.see(END)
        self.chat_area.config(state="disabled")

    def clear_chat(self):
        self.chat_area.config(state="normal")
        self.chat_area.delete("1.0", END)
        self.chat_area.config(state="disabled")

    def handle_error(self, context, error):
        error_msg = f"Erro em {context}: {str(error)}"
        logger.error(error_msg, exc_info=True)
        self.display_message(f"⚠️ {error_msg}")

    def safe_shutdown(self):
        try:
            self.display_message("\nSistema: Encerrando o chatbot...")
            self.update_idletasks()
            self.destroy()
        except Exception as e:
            logger.critical(f"Erro no shutdown: {str(e)}")
        finally:
            os._exit(0)

    def display_image(self, image_path):
        """
        Exibe uma imagem no chat do chatbot.
        Args:
            image_path (str): Caminho da imagem a ser exibida.
        """
        try:
            img = Image.open(image_path)
            img.thumbnail((200, 200))  # Redimensiona a imagem para caber na interface
            photo = ImageTk.PhotoImage(img)

            # Adiciona a imagem ao chat
            self.chat_area.config(state="normal")
            self.chat_area.image_create(END, image=photo)
            self.chat_area.insert(END, "\n")  # Adiciona uma nova linha após a imagem
            self.chat_area.config(state="disabled")

            # Mantém referência da imagem para evitar garbage collection
            if not hasattr(self, '_image_refs'):
                self._image_refs = []
            self._image_refs.append(photo)

        except Exception as e:
            self.display_message(f"Erro ao exibir imagem: {e}")



    def validate_arguments(self, method_name, *args):
        """
        Valida os argumentos passados para um método específico.

        Args:
            method_name (str): Nome do método.
            *args: Argumentos passados ao método.

        Raises:
            ValueError: Se os argumentos forem inválidos.
        """
        if method_name == "search_external_sites" and len(args) != 1:
            raise ValueError(f"O método '{method_name}' requer exatamente 1 argumento.")



if __name__ == "__main__":
    try:
        if not os.path.exists(BASE_CHROMA_PERSIST_DIR):
            os.makedirs(BASE_CHROMA_PERSIST_DIR, exist_ok=True)
        app = ChatbotGUI()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Falha na inicialização: {str(e)}", exc_info=True)
        tk.messagebox.showerror(
            "Erro Fatal", f"Aplicação encerrada devido a um erro crítico:\n{str(e)}")
        raise SystemExit("Erro fatal. Verifique log.txt para mais detalhes.")

