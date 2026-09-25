# Baixa o icone do canal mais eficientemente, sem extrair info extra
# Titulos originais

#!/usr/bin/env python3
import os
import re
import sys
import datetime
import shutil
import traceback
import builtins
from urllib.parse import parse_qs, urlparse
from typing import Optional, Dict, List, Any, Tuple


try:
    import yt_dlp
    import questionary
    import requests
except builtins.ImportError as e:
    #print(f"Erro: Biblioteca necessária não encontrada: {e}")
    #print("Por favor, instale as dependências usando:")
    #print("pip install -r requirements.txt")
    sys.exit(1)

import time

class MegaReuploader:

    def intro():
        """
        Anima a arte ASCII se desenhando linha por linha.
        """
        MegaReupload = [
            "                                                                        ==",
            "                                                                       ====",
            "                                                                      ======",
            "                                                                     =========",
            "                                             =================      ===========",
            "                                       =========================================",
            "                                  ===============================================",
            "                              ====================================================",
            "                            =======================================================",
            "                         ===========================================================",
            "                       ==============================================================",
            "                     ==================================================================",
            "                   ================================     ================================",
            "                  ========================                   ============================",
            "                =======================                     ==============================",
            "               =====================                       ===============================",
            "              ===================                         ===================",
            "             ==================                           =======",
            "            ==================    ============       ============",
            "           =================      ==============      ===========-=",
            "          =================         ======= ==          ==========",
            "         =================          ==========         =========",
            "            =============           ======== ==       ==========",
            "                ========            ===========      ===========",
            "                     ===            === ========     ===========",
            "                                    === ========    =============",
            "                                    === =========   =============",
            "                                    === ========== ===== =======",
            "                                    === = ============== =======",
            "                                    === =  ============  =======",
            "                                    === =   ===========  =======             ==",
            "                                    === =   ==========   =======            =======",
            "                                    =====    ========    =======           =============",
            "                                   -======   =======     =======          =================",
            "                                 ==========   ======   ===========       =================",
            "                                ============   ====   ==========-==     =================",
            "                                =============  ====    =============  ==================",
            "                                   =======                           ==================",
            "                       ===================                         ===================",
            "          ===============================                       =====================",
            "          ==============================                     =======================",
            "           ============================                   ========================",
            "            =============================          ===============================",
            "             ==================================================================",
            "               ==============================================================",
            "                ===========================================================",
            "                 =======================================================",
            "                  ====================================================",
            "                   ===============================================",
            "                    =========================================",
            "                     ===========      =================",
            "                      =========",
            "                        ======",
            "                         ====                                   23/09/2026     ",
            "                          ==                              MegaReuploader v4.0.0",
            ""
        ]

        # Limpa a tela antes de começar (funciona em sistemas Unix/Linux/macOS e Windows)
        os.system('cls' if os.name == 'nt' else 'clear')

        for line in MegaReupload:
            print(line)
            time.sleep(0.01) # Pequeno atraso em segundos (ajuste para mais rápido/lento)

    intro()
    time.sleep(1)
    print("ATENÇÃO, A FUNCIONALIDADE DE COOKIES NÃO FUNCIONA COM O GOOGLE CHROME.")
    print("ISSO PODE CAUSAR FALHAS AO TENTAR BAIXAR VÍDEOS QUE REQUEREM LOGIN, OU CASO YOUTUBE CONSIDERE O PROGRAMA COMO BOT APÓS MUITOS USOS SEGUIDOS.")
    print("POR FAVOR, UTILIZE OUTRO NAVEGADOR (Firefox [de preferência], Edge, Brave, Opera) LOGADO NA SUA CONTA YOUTUBE PARA FAZER AS ARQUIVAÇÕES.")
    print("Agradecemos pela compreensão. - MegaReuploads")
    print("")
    time.sleep(1)

    def __init__(self):
        self.check_ffmpeg()
        self.ydl_opts_base = {
            'quiet': False,
            'no_warnings': True,
            # A extração detalhada é necessária para formats, tags e datas.
            # As rotinas de listagem ativam extract_flat apenas quando apropriado.
            'extract_flat': False,
            'ignoreerrors': True,
            'extractor_retries': 3,
            'fragment_retries': 3,
            #'sleep_interval': 1,
            'sleep_interval': 0,
            #'max_sleep_interval': 2,
            'max_sleep_interval': 0,
            #'sleep_interval_requests': 1,
            'sleep_interval_requests': 0,

            'nopostoverwrites': True, # preserva titulos e descrições originais
            'remote_components': ['ejs:github'],
            #'http_headers': {'Accept-Language': 'pt-BR,pt;q=0.9'}, # Força português Brasil
            
            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            # HABILITAR COOKIES DO NAVEGADOR.
            # PARA HABILITAR OS COOKIES DO NAVEGADOR, PERMITIR QUE O PROGRAMA CONSIGA ARQUIVAR VÍDEOS COM RESTRIÇÕES E
            # IMPEDIR COM QUE O YOUTUBE QUEBRE O PROGRAMA, APAGUE O # DA LINHA DO NAVEGADOR DE SUA PREFERÊNCIA.
            # Escolha >>>APENAS UMA<<< linha correspondente ao seu navegador
            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
            #'cookiesfrombrowser': ('chrome',), [!] GOOGLE CHROME (até o momento 01/11/2025) NÃO FUNCIONA COM A FUNÇÃO DE COOKIES. POR-FAVOR, UTILIZE OUTRO NAVEGADOR PARA FAZER AS ARQUIVAÇÕES.
            #'cookiesfrombrowser': ('firefox',), #Recomendado
            #'cookiesfrombrowser': ('edge',),
            #'cookiesfrombrowser': ('brave',),
            #'cookiesfrombrowser': ('opera',),
            # -=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
        }

    def _show_settings_menu(self):
        """Abre o menu de configurações."""
        print("\n" + "="*60)
        print("⚙️  Configurações")
        print("="*60)

        while True:
            choice = questionary.select(
                "O que deseja configurar?",
                choices=[
                    "Cookies do Navegador",
                    "Tempos de Espera (Sleep)",
                    "Voltar ao Menu Principal"
                ]
            ).ask()

            if choice == "Cookies do Navegador":
                self._configure_cookies()
            elif choice == "Tempos de Espera (Sleep)":
                self._configure_sleep()
            elif choice == "Voltar ao Menu Principal":
                print("Configurações salvas.")
                break

    def _configure_cookies(self):
        """Configura o uso de cookies."""
        print("\n--- Configurar Cookies ---")
        print("ATENÇÃO: Cookies do Chrome NÃO funcionam corretamente com yt-dlp.")
        print("Use Firefox (recomendado), Edge, Brave ou Opera.")

        enable = questionary.confirm(
            "Deseja ATIVAR o uso de cookies do navegador?",
            default=True
        ).ask()

        if enable:
            browser = questionary.select(
                "Qual navegador?",
                choices=[
                    questionary.Choice("Firefox (Recomendado)", "firefox"),
                    questionary.Choice("Edge", "edge"),
                    questionary.Choice("Brave", "brave"),
                    questionary.Choice("Opera", "opera"),
                    questionary.Choice("Chrome (NÃO RECOMENDADO)", "chrome"),
                ]
            ).ask()
            if browser:
                # Define a opção de cookies como uma tupla
                self.ydl_opts_base['cookiesfrombrowser'] = (browser,)
                print(f"✅ Cookies do {browser} ativados.")
        else:
            # Remove a chave do dicionário para desativar
            self.ydl_opts_base.pop('cookiesfrombrowser', None)
            print("❌ Cookies do navegador desativados.")

    def _configure_sleep(self):
        """Configura os intervalos de sleep."""
        print("\n--- Configurar Tempos de Espera (Sleep) ---")
        print("Valores maiores podem evitar bans de IP, mas tornam o download mais lento.")
        print("0 = desativado (mais rápido, mais arriscado).")

        # Função auxiliar para pegar entrada numérica
        def get_int_input(prompt: str, default_val: int) -> int:
            while True:
                val_str = questionary.text(
                    prompt,
                    default=str(default_val)
                ).ask()
                try:
                    val_int = int(val_str)
                    if val_int < 0:
                        print("Por favor, insira um número não negativo.")
                        continue
                    return val_int
                except ValueError:
                    print("Entrada inválida. Por favor, insira um número inteiro.")

        # sleep_interval
        current_sleep = self.ydl_opts_base.get('sleep_interval', 0)
        new_sleep = get_int_input("sleep_interval (segundos):", current_sleep)
        self.ydl_opts_base['sleep_interval'] = new_sleep

        # max_sleep_interval
        current_max_sleep = self.ydl_opts_base.get('max_sleep_interval', 0)
        new_max_sleep = get_int_input("max_sleep_interval (segundos):", current_max_sleep)
        if new_max_sleep < new_sleep:
             new_max_sleep = new_sleep
             print(f"Ajustando max_sleep_interval para {new_max_sleep} (não pode ser menor que sleep_interval)")
        self.ydl_opts_base['max_sleep_interval'] = new_max_sleep

        # sleep_interval_requests
        current_req_sleep = self.ydl_opts_base.get('sleep_interval_requests', 0)
        new_req_sleep = get_int_input("sleep_interval_requests (segundos):", current_req_sleep)
        self.ydl_opts_base['sleep_interval_requests'] = new_req_sleep

        print("✅ Tempos de espera atualizados.")
        print(f"  sleep_interval: {self.ydl_opts_base['sleep_interval']}")
        print(f"  max_sleep_interval: {self.ydl_opts_base['max_sleep_interval']}")
        print(f"  sleep_interval_requests: {self.ydl_opts_base['sleep_interval_requests']}")

    def check_ffmpeg(self) -> bool:
        """Verifica se o ffmpeg está disponível no sistema."""
        if shutil.which('ffmpeg') is not None:
            return True

        print('\n' + '='*60)
        print('⚠️  ATENÇÃO: ffmpeg NÃO FOI ENCONTRADO')
        print('='*60)
        print('O ffmpeg é necessário para baixar vídeos em alta qualidade (1080p+).')
        print('Sem ele, alguns vídeos podem ser limitados a 720p.')
        
        return questionary.confirm(
            'Deseja continuar mesmo sem o ffmpeg?',
            default=False
        ).ask()

    def safe_filename(self, name: str, max_length: int = 200) -> str:
        """Cria um nome de arquivo seguro para o sistema."""
        if not name:
            return 'arquivo_sem_nome'
        
        # Remove caracteres inválidos
        name = re.sub(r'[\\/<>:"|?*]', '_', name)
        # Remove caracteres de controle
        name = re.sub(r'[\x00-\x1f\x7f]', '', name)
        # Colapsa espaços múltiplos
        name = ' '.join(name.split())
        
        if len(name) > max_length:
            # Preserva extensão se houver
            base, ext = os.path.splitext(name)
            name = base[:max_length-len(ext)] + ext
            
        # Remove pontos/espaços do final (problema no Windows)
        return name.rstrip('. ')

    def _extract_info(self, url: str, flat: bool = False) -> Optional[Dict[str, Any]]:
        """Extrai informações e permite reautenticação após bloqueio do YouTube."""
        options = {**self.ydl_opts_base, 'extract_flat': flat, 'ignoreerrors': False}
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:
            if not self._retry_after_auth_error(exc):
                raise
            options = {**self.ydl_opts_base, 'extract_flat': flat, 'ignoreerrors': False}
            with yt_dlp.YoutubeDL(options) as ydl:
                return ydl.extract_info(url, download=False)

    @staticmethod
    def _is_authentication_error(error: Exception) -> bool:
        """Identifica mensagens de login, CAPTCHA ou detecção de robô."""
        message = str(error).lower()
        markers = (
            'sign in to confirm',
            'confirm you\'re not a bot',
            'confirm you are not a bot',
            'not a bot',
            'captcha',
            'authentication',
            'login required',
            'sign in to view',
            'cookies',
        )
        return any(marker in message for marker in markers)

    def _retry_after_auth_error(self, error: Exception) -> bool:
        """Pergunta o navegador e indica se a operação deve ser repetida."""
        if not self._is_authentication_error(error):
            return False

        print("\n⚠️ O YouTube solicitou autenticação ou detectou o programa como robô.")
        print("Selecione um navegador em que sua conta do YouTube esteja conectada.")
        browser = questionary.select(
            "Escolha o navegador para usar cookies:",
            choices=[
                questionary.Choice("Firefox (Recomendado)", "firefox"),
                questionary.Choice("Edge", "edge"),
                questionary.Choice("Brave", "brave"),
                questionary.Choice("Opera", "opera"),
                questionary.Choice("Chrome (pode não funcionar)", "chrome"),
                questionary.Choice("Cancelar", None),
            ],
        ).ask()
        if not browser:
            print("❌ Reautenticação cancelada.")
            return False

        self.ydl_opts_base['cookiesfrombrowser'] = (browser,)
        print(f"✅ Cookies do {browser} ativados. Repetindo a operação...")
        return True

    @staticmethod
    def _detect_archive_mode(url: str) -> Optional[str]:
        """Identifica canal, playlist ou vídeo a partir da estrutura da URL."""
        try:
            parsed = urlparse(url.strip())
            host = parsed.netloc.lower().split(':', 1)[0]
            path_parts = [part for part in parsed.path.split('/') if part]
            query = parse_qs(parsed.query)

            if host not in {'youtube.com', 'www.youtube.com', 'm.youtube.com',
                            'music.youtube.com', 'youtu.be'}:
                return None
            if host == 'youtu.be':
                return 'video' if path_parts else None
            if 'v' in query and query['v'] and query['v'][0]:
                return 'video'
            if 'list' in query and query['list'] and query['list'][0]:
                return 'playlist'
            if path_parts and path_parts[0].lower() in {
                'channel', 'c', 'user', 'shorts', 'streams', 'live'
            }:
                return 'channel'
            if path_parts and path_parts[0].startswith('@'):
                return 'channel'
            if path_parts and path_parts[0].lower() == 'playlist':
                return 'playlist'
            if path_parts and path_parts[0].lower() == 'watch':
                return 'video'
        except (TypeError, ValueError):
            return None
        return None

    def _format_selector(self, requested: str) -> str:
        """Converte a qualidade escolhida em um seletor yt-dlp resiliente."""
        selectors = {
            'best': 'bestvideo*+bestaudio/best',
            'balanced': 'bestvideo*[height<=720]+bestaudio/best[height<=720]/best',
            'worst': 'worstvideo*+worstaudio/worst',
        }
        if requested in selectors:
            return selectors[requested]
        # IDs de vídeo precisam de áudio separado quando o formato é DASH.
        if '+' in requested or '/' in requested:
            return requested
        return f'{requested}+bestaudio/best'

    def _download_video(self, url: str, folder: str, title: str,
                        format_id: str, extras: List[str]) -> None:
        """Baixa um vídeo e repete após configurar cookies se necessário."""
        options = self._prepare_download_options(format_id, folder, extras, title)
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])
        except Exception as exc:
            if not self._retry_after_auth_error(exc):
                raise
            options = self._prepare_download_options(format_id, folder, extras, title)
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

    def download_single_video(self, url: str) -> bool:
        """Processa o download de um único vídeo."""
        print("\nObtendo informações do vídeo...")
        
        # Primeiro extrair metadados
        try:
            info = self._extract_info(url)
            if not info:
                print("❌ Não foi possível obter informações do vídeo.")
                return False
                
            # Mostrar informações básicas
            print(f"\nTítulo: {info.get('title')}")
            print(f"Canal: {info.get('uploader')}")
                
            # Obter qualidades disponíveis
            formats = self._get_available_formats(info)
            if not formats:
                print("❌ Não foi possível obter as qualidades disponíveis.")
                return False
                
            # Usuário seleciona qualidade
            format_id = self._select_quality(formats)
            if not format_id:
                return False
                
            # Selecionar extras
            extras = self._select_extras(False)
            if extras is None:  # Usuário cancelou
                return False
                
            # Criar pasta para o vídeo
            storage_mode = self._select_storage_mode(extras)
            folder_name = self._video_folder(info, storage_mode)
            if storage_mode != 'root':
                os.makedirs(folder_name, exist_ok=True)
            if not folder_name:
                return False
                
            # Executar download
            print(f"\nBaixando vídeo para: {folder_name}")
            self._download_video(
                url, folder_name, info.get('title', 'video'), format_id, extras
            )
                
            # Processar extras selecionados
            if extras:
                self._process_extras(info, folder_name, extras)
                
            print(f"\n✅ Download concluído: {folder_name}")
            return True
                
        except Exception as e:
            print(f"❌ Erro durante o download: {e}")
            traceback.print_exc()
            return False

    def _get_available_formats(self, info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai e organiza os formatos disponíveis do vídeo."""
        formats = []
        seen_qualities = set()
        
        for f in info.get('formats', []):
            # Pula formatos sem vídeo
            if f.get('vcodec') == 'none':
                continue
                
            height = f.get('height', 0)
            if height and height not in seen_qualities:
                formats.append({
                    'format_id': f['format_id'],
                    'ext': f.get('ext', 'mp4'),
                    'height': height,
                    'filesize': f.get('filesize', 0),
                    'vcodec': f.get('vcodec', 'unknown')
                })
                seen_qualities.add(height)
        
        return sorted(formats, key=lambda x: x['height'], reverse=True)

    def _select_quality(self, formats: List[Dict[str, Any]]) -> Optional[str]:
        """Interface para usuário selecionar qualidade do vídeo."""
        choices = [
            questionary.Choice(
                title=f"{f['height']}p ({f['ext']}, {self._format_size(f['filesize'])})",
                value=f['format_id']
            ) for f in formats
        ]
        
        # Adiciona opção automática no topo
        choices.insert(0, questionary.Choice(
            title="🔄 Automático (Melhor qualidade disponível)",
            value="best"
        ))
        
        return questionary.select(
            "Escolha a qualidade do vídeo:",
            choices=choices
        ).ask()

    def _format_size(self, size: int) -> str:
        """Formata tamanho em bytes para formato legível."""
        if not size:
            return "Tamanho desconhecido"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"

    def _select_extras(self, modoCanal) -> Optional[List[str]]:
        """Interface para usuário selecionar extras para download."""

        if modoCanal == False:
            return questionary.checkbox(
                "Selecione os itens adicionais para download:",
                choices=[
                    questionary.Choice("📸 Thumbnail do vídeo", "thumbnail", checked=False),
                    questionary.Choice("📝 Metadados do vídeo", "metadata", checked=False),
                    questionary.Choice("🔍 Keywords (tags)", "keywords", checked=False),
                    questionary.Choice("👤 Ícone do canal", "channel_icon", checked=False)
                ]
            ).ask()
        
        else:
                return questionary.checkbox(
                "Selecione os itens adicionais para download:",
                choices=[
                    questionary.Choice("📸 Thumbnail do vídeo", "thumbnail", checked=False),
                    questionary.Choice("📝 Metadados do vídeo", "metadata", checked=False),
                    questionary.Choice("🔍 Keywords (tags)", "keywords", checked=False),
                ]
            ).ask()

    def _create_video_folder(self, info: Dict[str, Any]) -> Optional[str]:
        """Cria e retorna o nome da pasta para o vídeo."""
        try:
            title = info.get('title', 'video')
            channel = info.get('uploader', 'channel')
            upload_date = info.get('upload_date', '')
            
            if upload_date and len(upload_date) == 8:
                date_str = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
            else:
                date_str = "data_desconhecida"
            
            folder_name = f"[{self.safe_filename(channel)}][{self.safe_filename(title)}][{date_str}]"
            os.makedirs(folder_name, exist_ok=True)
            return folder_name
        except Exception as e:
            print(f"❌ Erro ao criar pasta: {e}")
            return None

    def _prepare_download_options(self, format_id: str, folder: str, 
                                extras: List[str], title: str) -> Dict[str, Any]:
        """Prepara as opções de download do yt-dlp."""
        opts = {
            **self.ydl_opts_base,
            'format': self._format_selector(format_id),
            'outtmpl': os.path.join(folder, f'{self.safe_filename(title)}.%(ext)s'),
            'writethumbnail': 'thumbnail' in extras,
        }
        
        # Se tiver ffmpeg, permite mesclar áudio e vídeo
        if shutil.which('ffmpeg'):
            opts['merge_output_format'] = 'mp4'
            
        return opts

    def _process_extras(self, info: Dict[str, Any], folder: str, extras: List[str]):
        """Processa os extras selecionados (thumbnail, metadados, etc)."""
        if 'metadata' in extras:
            self._save_metadata(info, folder)
            
        if 'keywords' in extras and info.get('tags'):
            self._save_keywords(info['tags'], folder)
            
        if 'channel_icon' in extras:
            self._download_channel_icon(info, folder)

    def _save_metadata(self, info: Dict[str, Any], folder: str):
        """Salva os metadados do vídeo em arquivo texto."""
        try:
            meta_path = os.path.join(folder, 'metadados.txt')
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write('=== Metadados do Vídeo ===\n\n')
                f.write(f"Título: {self._format_optional(info.get('title'))}\n")
                f.write(f"Canal: {self._format_optional(info.get('uploader'))}\n")
                f.write(f"ID: {self._format_optional(info.get('id'))}\n")
                f.write(f"URL: {self._format_optional(info.get('webpage_url'))}\n")
                f.write(f"Data de Upload: {self._format_date(info.get('upload_date', ''))}\n")
                f.write(f"Duração: {self._format_duration(info.get('duration', 0))}\n")
                f.write(f"Visualizações: {self._format_count(info.get('view_count'))}\n")
                f.write(f"Likes: {self._format_count(info.get('like_count'))}\n")
                
                f.write('\n=== Descrição ===\n')
                f.write(self._format_optional(info.get('description'), 'Sem descrição.'))
                
            print(f"✅ Metadados salvos em: {meta_path}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar metadados: {e}")

    def _save_keywords(self, tags: List[str], folder: str):
        """Salva as keywords/tags em arquivo texto."""
        try:
            tags_path = os.path.join(folder, 'keywords.txt')
            with open(tags_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(tags))
            print(f"✅ Keywords salvas em: {tags_path}")
        except Exception as e:
            print(f"❌ Erro ao salvar keywords: {e}")

    def _download_channel_icon(self, info: Dict[str, Any], folder: str):
        """Baixa o ícone usando os metadados do vídeo ou uma única página do canal."""
        try:
            icon_url = self._find_channel_icon_url(info)

            if not icon_url:
                channel_url = info.get('channel_url') or info.get('uploader_url')
                if channel_url:
                    channel_page = channel_url.rstrip('/') + '/about'
                    print("🔎 Ícone não encontrado no vídeo; consultando apenas a página principal do canal...")
                    channel_info = self._extract_info(channel_page, flat=True)
                    if channel_info:
                        icon_url = self._find_channel_icon_url(channel_info)

            if not icon_url:
                print("⚠️ Ícone do canal não encontrado sem varrer os vídeos do canal.")
                return

            # Download do ícone
            icon_path = os.path.join(folder, 'channel_icon.jpg')
            response = requests.get(icon_url, timeout=10)
            if response.status_code == 200:
                with open(icon_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Ícone do canal salvo em: {icon_path}")
            else:
                print(f"❌ Erro ao baixar ícone (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ Erro ao baixar ícone do canal: {e}")

    @staticmethod
    def _find_channel_icon_url(info: Dict[str, Any]) -> Optional[str]:
        """Encontra o maior thumbnail quadrado de perfil nos metadados recebidos."""
        icon_url = info.get('channel_thumbnail')
        thumbnails = info.get('thumbnails', []) or []
        candidates = [
            thumbnail for thumbnail in thumbnails
            if thumbnail.get('url')
            and thumbnail.get('width', 0) > 0
            and ('/banner/' not in thumbnail.get('url', ''))
            and (
                '/ytc/' in thumbnail.get('url', '')
                or '/profile/' in thumbnail.get('url', '')
                or abs(
                    thumbnail.get('width', 0) - thumbnail.get('height', 0)
                ) <= 5
            )
        ]
        if candidates:
            icon_url = max(candidates, key=lambda item: item.get('width', 0)).get('url')
        return icon_url

    def _format_date(self, date_str: Any) -> str:
        """Formata string de data YYYYMMDD para formato legível."""
        if isinstance(date_str, str) and len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        return date_str or 'Data desconhecida'

    def _format_duration(self, seconds: int) -> str:
        """Formata duração em segundos para formato legível."""
        if not isinstance(seconds, (int, float)) or seconds <= 0:
            return 'Duração desconhecida'
        return str(datetime.timedelta(seconds=seconds))

    @staticmethod
    def _format_optional(value: Any, default: str = 'N/A') -> str:
        """Converte valores opcionais em texto sem formatar None."""
        return default if value is None or value == '' else str(value)

    @staticmethod
    def _format_count(value: Any) -> str:
        """Formata contadores numéricos, incluindo valores ausentes."""
        if value is None or value == '':
            return 'N/A'
        try:
            return f'{int(value):,}'.replace(',', '.')
        except (TypeError, ValueError):
            return str(value)

    def _select_storage_mode(self, extras: List[str]) -> str:
        """Usa subpastas por padrão e pergunta organização sem opcionais."""
        if extras:
            return 'nested'

        choice = questionary.select(
            'Como deseja organizar os arquivos?',
            choices=[
                questionary.Choice('Pastas e subpastas (padrão)', 'nested'),
                questionary.Choice('Pasta principal', 'main'),
                questionary.Choice('Raiz', 'root'),
            ],
        ).ask()
        return choice or 'nested'

    def _video_folder(self, info: Dict[str, Any], storage_mode: str,
                      parent: str = '.') -> str:
        """Calcula a pasta do vídeo de acordo com a organização escolhida."""
        if storage_mode == 'root':
            return '.'

        title = self._format_optional(info.get('title'), 'video')
        channel = self._format_optional(info.get('uploader'), 'channel')
        date_str = self._format_date(info.get('upload_date', ''))
        folder_name = f'[{self.safe_filename(channel)}][{self.safe_filename(title)}][{date_str}]'
        if storage_mode == 'main':
            return folder_name if parent == '.' else parent
        return os.path.join(parent, folder_name)
        
    def download_playlist(self, url: str) -> bool:
        """Processa o download de uma playlist completa."""
        print("\nObtendo informações da playlist...")
        
        try:
            # Configurar opções para extração de informações da playlist
            playlist_info = self._extract_info(url, flat=True)
            if not playlist_info:
                print("❌ Não foi possível obter informações da playlist.")
                return False
                
                # Mostrar informações da playlist
                title = playlist_info.get('title', 'Playlist sem título')
                channel = playlist_info.get('uploader', 'Canal desconhecido')
                video_count = len(playlist_info.get('entries', []))
                
                print(f"\nPlaylist: {title}")
                print(f"Canal: {channel}")
                print(f"Total de vídeos: {video_count}")
                
                if not video_count:
                    print("❌ Nenhum vídeo encontrado na playlist.")
                    return False
                
                # Confirmar download
                if not questionary.confirm(
                    f"Deseja baixar todos os {video_count} vídeos?",
                    default=True
                ).ask():
                    return False
                
                # Selecionar qualidade padrão para todos os vídeos
                print("\nSelecione a qualidade padrão para todos os vídeos:")
                format_id = questionary.select(
                    "Escolha a qualidade:",
                    choices=[
                        questionary.Choice("Qualidade máxima", value="best"),
                        questionary.Choice("Qualidade média (até 720p)", value="balanced"),
                        questionary.Choice("Qualidade mínima", value="worst")
                    ]
                ).ask()
                
                if not format_id:
                    return False
                
                # Selecionar extras padrão
                extras = self._select_extras(False)
                if extras is None:
                    return False
                
                # Criar pasta principal da playlist
                base_folder = f"[{self.safe_filename(channel)}][Playlist - {self.safe_filename(title)}][{datetime.datetime.now().strftime('%Y-%m-%d')}]"
                os.makedirs(base_folder, exist_ok=True)
                
                # Salvar metadados da playlist
                self._save_playlist_metadata(playlist_info, base_folder)
                
                # Processar cada vídeo
                success_count = 0
                for i, entry in enumerate(playlist_info['entries'], 1):
                    if not entry:
                        continue
                        
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    print(f"\n[{i}/{video_count}] Processando: {entry.get('title', 'Vídeo sem título')}")
                    
                    # Obter informações detalhadas do vídeo para nome do canal e data corretos
                    video_info = self._extract_info(video_url)
                    if not video_info:
                        print("❌ Não foi possível obter os metadados deste vídeo.")
                        continue
                    video_channel = video_info.get('uploader', 'Canal desconhecido')
                    upload_date = video_info.get('upload_date', '')
                    
                    # Criar pasta para o vídeo dentro da pasta da playlist

                    video_folder = base_folder
                    if extras:
                        video_folder = os.path.join(
                            base_folder,
                            f"[{self.safe_filename(video_channel)}][{self.safe_filename(video_info.get('title', 'video'))}][{self._format_date(upload_date)}]"
                        )
                        os.makedirs(video_folder, exist_ok=True)
                    
                    # Configurar opções de download

                    # Baixar vídeo
                    try:
                        self._download_video(
                            video_url, video_folder, video_info.get('title', 'video'),
                            format_id, extras
                        )
                            
                        # Processar extras
                        if extras:
                            self._process_extras(video_info, video_folder, extras)
                                
                        success_count += 1

                        if extras:
                            print(f"✅ Download concluído: {video_folder}")
                        else:
                            print(f"✅ Download concluído: {base_folder}")

                        
                    except Exception as e:
                        print(f"❌ Erro ao baixar vídeo: {e}")
                        continue
                
                print(f"\n🎉 Download da playlist concluído!")
                print(f"✅ {success_count}/{video_count} vídeos baixados com sucesso")
                return True
                
        except Exception as e:
            print(f"❌ Erro durante o download da playlist: {e}")
            traceback.print_exc()
            return False
            
    def download_playlist(self, url: str) -> bool:
        """Baixa uma playlist usando uma única qualidade e organização escolhidas."""
        print("\nObtendo informações da playlist...")
        try:
            playlist_info = self._extract_info(url, flat=True)
            if not playlist_info:
                print("❌ Não foi possível obter informações da playlist.")
                return False

            title = self._format_optional(playlist_info.get('title'), 'Playlist sem título')
            channel = self._format_optional(playlist_info.get('uploader'), 'Canal desconhecido')
            entries = [entry for entry in (playlist_info.get('entries') or []) if entry]
            if not entries:
                print("❌ Nenhum vídeo encontrado na playlist.")
                return False

            print(f"\nPlaylist: {title}")
            print(f"Canal: {channel}")
            print(f"Total de vídeos: {len(entries)}")
            if not questionary.confirm(
                f"Deseja baixar todos os {len(entries)} vídeos?", default=True
            ).ask():
                return False

            format_id = questionary.select(
                "Escolha a qualidade:",
                choices=[
                    questionary.Choice("Qualidade máxima", "best"),
                    questionary.Choice("Qualidade média (até 720p)", "balanced"),
                    questionary.Choice("Qualidade mínima", "worst"),
                ],
            ).ask()
            if not format_id:
                return False

            extras = self._select_extras(False)
            if extras is None:
                return False
            storage_mode = self._select_storage_mode(extras)
            base_folder = '.'
            if storage_mode != 'root':
                base_folder = f"[{self.safe_filename(channel)}][Playlist - {self.safe_filename(title)}][{datetime.datetime.now().strftime('%Y-%m-%d')}]"
                os.makedirs(base_folder, exist_ok=True)

            success_count = 0
            for index, entry in enumerate(entries, 1):
                video_url = f"https://www.youtube.com/watch?v={entry.get('id')}"
                print(f"\n[{index}/{len(entries)}] Processando: {entry.get('title', 'Vídeo sem título')}")
                video_info = self._extract_info(video_url)
                if not video_info:
                    print("❌ Não foi possível obter os metadados deste vídeo.")
                    continue

                video_folder = self._video_folder(video_info, storage_mode, base_folder)
                if storage_mode == 'nested':
                    os.makedirs(video_folder, exist_ok=True)
                try:
                    self._download_video(
                        video_url, video_folder,
                        self._format_optional(video_info.get('title'), 'video'),
                        format_id, extras,
                    )
                    if extras:
                        self._process_extras(video_info, video_folder, extras)
                    success_count += 1
                except Exception as exc:
                    print(f"❌ Erro ao baixar vídeo: {exc}")

            if storage_mode != 'root':
                self._save_playlist_metadata(playlist_info, base_folder)
            print(f"\n🎉 Download da playlist concluído! {success_count}/{len(entries)} vídeos baixados.")
            return success_count > 0
        except Exception as exc:
            print(f"❌ Erro durante o download da playlist: {exc}")
            traceback.print_exc()
            return False

    def _save_playlist_metadata(self, info: Dict[str, Any], folder: str):
        """Salva os metadados da playlist em arquivo texto."""
        try:
            meta_path = os.path.join(folder, 'metadados_playlist.txt')
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write('=== Metadados da Playlist ===\n\n')
                f.write(f"Título: {info.get('title', 'N/A')}\n")
                f.write(f"Canal: {info.get('uploader', 'N/A')}\n")
                f.write(f"ID: {info.get('id', 'N/A')}\n")
                f.write(f"URL: {info.get('webpage_url', 'N/A')}\n")
                f.write(f"Total de vídeos: {len(info.get('entries', []))}\n")
                
                # Lista de vídeos
                f.write('\n=== Lista de Vídeos ===\n\n')
                for i, entry in enumerate(info.get('entries', []), 1):
                    if entry:
                        f.write(f"{i:03d}. {entry.get('title', 'Vídeo sem título')}\n")
                        f.write(f"     ID: {entry.get('id', 'N/A')}\n")
                        f.write(f"     URL: https://www.youtube.com/watch?v={entry.get('id', '')}\n\n")
                
            print(f"✅ Metadados da playlist salvos em: {meta_path}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar metadados da playlist: {e}")

    @staticmethod
    def _filter_channel_tab_entries(
        tab_info: Dict[str, Any], tab_name: str, entries: List[Dict[str, Any]],
        seen_ids: set[str],
    ) -> List[Dict[str, Any]]:
        """Filtra respostas de abas que o YouTube redirecionou para outra aba."""
        if tab_name == 'Lives':
            page_url = tab_info.get('webpage_url') or tab_info.get('original_url') or ''
            if page_url and '/streams' not in page_url.lower():
                return []

        filtered_entries = []
        for entry in entries:
            video_id = entry.get('id')
            if video_id and video_id not in seen_ids:
                seen_ids.add(video_id)
                filtered_entries.append(entry)
        return filtered_entries

    def download_channel(self, url: str) -> bool:
            """Processa o download de um canal completo."""
            print("\nObtendo informações do canal...")
            
            try:
                # --- Bloco 1: Obter Metadados do Canal ---
                # dump_single_json é bom para metadados do *canal*
                channel_info = self._extract_info(url, flat=True)
                if not channel_info:
                    print("❌ Não foi possível obter informações do canal.")
                    return False

                # Mostrar informações do canal
                channel_name = channel_info.get('uploader', 'Canal desconhecido')
                print(f"\nCanal: {channel_name}")

                # Criar pasta principal do canal
                base_folder = f"[{self.safe_filename(channel_name)}][{datetime.datetime.now().strftime('%Y-%m-%d')}]"
                os.makedirs(base_folder, exist_ok=True)
                
                # Criar subpastas
                videos_folder = os.path.join(base_folder, "Vídeos")
                lives_folder = os.path.join(base_folder, "Lives")
                shorts_folder = os.path.join(base_folder, "Shorts")
                
                os.makedirs(videos_folder, exist_ok=True)
                os.makedirs(lives_folder, exist_ok=True)
                os.makedirs(shorts_folder, exist_ok=True)
                
                # Salvar metadados, ícone e banner do canal
                self._save_channel_metadata(channel_info, base_folder)
                self._download_channel_icon_to_base(channel_info, base_folder)
                self._download_channel_banner_to_base(channel_info, base_folder)

                # --- Bloco 2: Obter Listas de Vídeos das Abas ---
                print("\nObtendo lista de vídeos do canal (por abas)...")
                
                # Opções para extrair listas de vídeos (SEM dump_single_json)
                list_opts = {
                    **self.ydl_opts_base,
                    'extract_flat': True,
                }

                tabs_to_process = [
                    ('Vídeos', f"{url}/videos", videos_folder),
                    ('Lives', f"{url}/streams", lives_folder),
                    ('Shorts', f"{url}/shorts", shorts_folder),
                ]

                all_videos_by_tab = []
                total_videos = 0
                seen_video_ids = set()

                with yt_dlp.YoutubeDL(list_opts) as ydl:
                    for tab_name, tab_url, target_folder in tabs_to_process:
                        print(f"Buscando {tab_name}...")
                        try:
                            tab_info = ydl.extract_info(tab_url, download=False)
                            entries = tab_info.get('entries', []) or []
                            entries = self._filter_channel_tab_entries(
                                tab_info, tab_name, entries, seen_video_ids
                            )
                            if entries:
                                print(f"Encontrados {len(entries)} {tab_name}.")
                                all_videos_by_tab.append((tab_name, target_folder, entries))
                                total_videos += len(entries)
                            else:
                                print(f"Nenhum {tab_name} encontrado.")
                        except Exception as e:
                            print(f"⚠️ Erro ao obter {tab_name} de {tab_url}: {e}")
                            # Algumas abas podem não existir (ex: canal sem lives)
                            # traceback.print_exc() # Descomente para depuração
                            print("Continuando para a próxima aba...")

                if not total_videos:
                    print("❌ Nenhum vídeo encontrado em nenhuma aba do canal.")
                    return False
                
                print(f"\nTotal de vídeos encontrados (em todas as abas): {total_videos}")
                channel_info['video_count'] = total_videos
                self._save_channel_metadata(channel_info, base_folder)

                # --- Bloco 3: Confirmação e Seleção de Qualidade ---
                if not questionary.confirm(
                    f"Deseja baixar todos os {total_videos} vídeos?",
                    default=True
                ).ask():
                    return False

                # Selecionar qualidade padrão
                print("\nSelecione a qualidade padrão para todos os vídeos:")
                format_id = questionary.select(
                    "Escolha a qualidade:",
                    choices=[
                        questionary.Choice("Qualidade máxima", value="best"),
                        questionary.Choice("Qualidade média (até 720p)", value="balanced"),
                        questionary.Choice("Qualidade mínima", value="worst"),
                    ]
                ).ask()
                
                if not format_id:
                    return False
                
                # Selecionar extras padrão
                extras = self._select_extras(True)
                if extras is None:
                    return False

                storage_mode = self._select_storage_mode(extras)
                if storage_mode == 'root':
                    base_folder = '.'
                    videos_folder = lives_folder = shorts_folder = '.'
                elif storage_mode == 'main':
                    videos_folder = lives_folder = shorts_folder = base_folder

                # --- Bloco 4: Processamento e Download ---
                success_count = {'Vídeos': 0, 'Lives': 0, 'Shorts': 0}
                keywords = set()
                current_video_num = 0

                for tab_name, target_folder, entries in all_videos_by_tab:
                    for entry in entries:
                        current_video_num += 1
                        if not entry:
                            continue
                            
                        video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                        print(f"\n[{current_video_num}/{total_videos}] Processando {tab_name}: {entry.get('title', 'Vídeo sem título')}")
                        
                        try:
                            # Obter informações detalhadas do vídeo (para data, tags, etc)
                            # Não precisa de flat extract aqui
                            video_info = self._extract_info(video_url)
                            
                            if not video_info:
                                print(f"❌ Erro ao obter info detalhada de: {video_url}")
                                continue

                            # Criar pasta para o vídeo
                            video_date = video_info.get('upload_date', '')
                            if video_date and len(video_date) == 8:
                                date_str = f"{video_date[:4]}-{video_date[4:6]}-{video_date[6:8]}"
                            else:
                                date_str = "data_desconhecida"
                            
                            if storage_mode == 'nested':
                                video_folder = os.path.join(
                                    target_folder,
                                    f"[{self.safe_filename(channel_name)}][{self.safe_filename(video_info.get('title', 'video'))}][{date_str}]"
                                )
                                os.makedirs(video_folder, exist_ok=True)
                            else:
                                video_folder = target_folder
                            
                            # Baixar vídeo
                            self._download_video(
                                video_url, video_folder,
                                video_info.get('title', 'video'), format_id, extras
                            )
                            
                            # Processar extras
                            if extras:
                                self._process_extras(video_info, video_folder, extras)
                                
                                # Coletar keywords para arquivo geral
                                if video_info.get('tags'):
                                    keywords.update(video_info['tags'])
                            
                            success_count[tab_name] += 1
                            print(f"✅ Download concluído: {video_folder}")
                            
                        except Exception as e:
                            print(f"❌ Erro ao baixar vídeo ({entry.get('title')}): {e}")
                            traceback.print_exc() # Mostra mais detalhes do erro
                            continue
                
                # --- Bloco 5: Finalização ---
                if keywords:
                    try:
                        with open(os.path.join(base_folder, 'keywords_canal.txt'), 'w', encoding='utf-8') as f:
                            f.write('\n'.join(sorted(keywords)))
                    except Exception as e:
                        print(f"⚠️ Erro ao salvar keywords do canal: {e}")
                
                print(f"\n🎉 Download do canal concluído!")
                print(f"✅ Vídeos baixados com sucesso:")
                print(f"   - Vídeos: {success_count['Vídeos']}")
                print(f"   - Lives: {success_count['Lives']}")
                print(f"   - Shorts: {success_count['Shorts']}")
                print(f"   Total: {sum(success_count.values())}/{total_videos}")
                return True
                
            except Exception as e:
                print(f"❌ Erro durante o download do canal: {e}")
                traceback.print_exc()
                return False
                    
    def _save_channel_metadata(self, info: Dict[str, Any], folder: str):
        """Salva os metadados do canal em arquivo texto."""
        try:
            meta_path = os.path.join(folder, 'metadados_canal.txt')
            keywords = info.get('tags', [])
            keywords_str = ', '.join(keywords) if keywords else 'N/A'

            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write('=== Metadados do Canal ===\n\n')
                f.write(f"Nome: {self._format_optional(info.get('uploader'))}\n")
                f.write(f"ID: {self._format_optional(info.get('uploader_id'))}\n")
                f.write(f"URL: {self._format_optional(info.get('uploader_url'))}\n")
                f.write(f"ID2: {self._format_optional(info.get('channel_id'))}\n")
                f.write(f"URL2: {self._format_optional(info.get('channel_url'))}\n")
                f.write(f"Palavras-chave: {keywords_str}\n")
                
                # Formatar números grandes com pontos como separador de milhar
                subscriber_count = info.get('channel_follower_count') #('subscriber_count')
                formatted_subs = self._format_count(subscriber_count)
                    
                video_count = info.get('video_count', info.get('playlist_count'))
                formatted_videos = self._format_count(video_count)
                
                f.write(f"Inscritos: {formatted_subs}\n")
                f.write(f"Total de vídeos: {formatted_videos}\n")
                
                f.write('\n=== Descrição do Canal ===\n')
                f.write(self._format_optional(info.get('description'), 'Sem descrição.'))
                
            print(f"✅ Metadados do canal salvos em: {meta_path}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar metadados do canal: {e}")
            
    def _download_channel_icon_to_base(self, info: Dict[str, Any], folder: str):
            """Baixa o ícone do canal para a pasta base (com lógica de detecção)."""
            try:
                icon_url = info.get('channel_thumbnail')  # 1. Tenta o campo de fallback
                thumbnails = info.get('thumbnails', [])

                if thumbnails:
                    # 2. Tenta a lógica de detecção de ícones
                    candidate_icons = [
                        t for t in thumbnails 
                        if t.get('url') and t.get('width', 0) > 0 and (
                            ('/ytc/' in t['url']) or 
                            ('/profile/' in t['url']) or 
                            # Verifica se é quadrado (tolerância de 5px)
                            (abs(t.get('width', 0) - t.get('height', 0)) <= 5) 
                        ) and (
                            # Exclui banners
                            ('/banner/' not in t['url']) 
                        )
                    ]
                    
                    if candidate_icons:
                        # Pega o ícone de maior resolução entre os candidatos
                        icon_url = max(candidate_icons, key=lambda x: x.get('width', 0)).get('url')

                if not icon_url:
                    print("⚠️ Ícone do canal não encontrado.")
                    return
                
                # Download do ícone
                icon_path = os.path.join(folder, 'channel_icon.jpg')
                response = requests.get(icon_url, timeout=10)
                if response.status_code == 200:
                    with open(icon_path, 'wb') as f:
                        f.write(response.content)
                    print(f"✅ Ícone do canal salvo em: {icon_path}")
                else:
                    print(f"❌ Erro ao baixar ícone (HTTP {response.status_code})")
                    
            except Exception as e:
                print(f"❌ Erro ao baixar ícone do canal: {e}")

    def _download_channel_banner_to_base(self, info: Dict[str, Any], folder: str):
        """Baixa o banner do canal para a pasta base (com lógica de detecção)."""
        try:
            # 1. Tenta o campo dedicado (lógica antiga)
            banner_url = info.get('channel_banner')
            
            if not banner_url:
                # 2. Tenta a lista 'banners' (lógica atual)
                banners = info.get('banners', [])
                if banners:
                    banner = max(banners, key=lambda b: b.get('width', 0))
                    banner_url = banner.get('url')

            if not banner_url:
                # 3. Fallback: Procura na lista 'thumbnails' (lógica antiga)
                thumbnails = info.get('thumbnails', [])
                if thumbnails:
                    non_square_banners = [
                        t for t in thumbnails 
                        if t.get('url') and 
                        t.get('width', 0) > 0 and
                        # Verifica se NÃO é quadrado (tolerância de 10px)
                        abs(t.get('width', 0) - t.get('height', 0)) > 10 and 
                        ('/ytc/' not in t['url']) and # Não é ícone
                        ('/profile/' not in t['url']) # Não é ícone
                    ]
                    
                    if non_square_banners:
                         # Pega o banner de maior resolução
                         banner_url = max(non_square_banners, key=lambda x: x.get('width', 0)).get('url')

            if not banner_url:
                print("⚠️ Banner do canal não encontrado.")
                return
            
            # A extensão pode variar, mas vamos salvar como jpg
            banner_path = os.path.join(folder, 'channel_banner.jpg')
            response = requests.get(banner_url, timeout=10)
            
            if response.status_code == 200:
                with open(banner_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Banner do canal salvo em: {banner_path}")
            else:
                print(f"❌ Erro ao baixar banner (HTTP {response.status_code})")
                
        except Exception as e:
            print(f"❌ Erro ao baixar banner do canal: {e}")
def main():
    """Função principal do programa."""
    archiver = MegaReuploader()
    
    # Menu global: o modo é escolhido automaticamente pela URL informada.
    while True: # Loop para permitir múltiplas operações
        choice = questionary.select(
            "Escolha uma opção:",
            choices=[
                "Inserir URL",
                "Configurações",
                "Sair"
            ]
        ).ask()
        
        if choice == "Sair":
            print("Saindo...")
            break
        
        if choice == "Configurações":
            archiver._show_settings_menu()
            continue

        if choice != "Inserir URL":
            continue

        # Solicitar URL e detectar o tipo de arquivamento.
        url = questionary.text("Digite a URL do YouTube:").ask()
        if not url:
            print("❌ URL não fornecida. Voltando ao menu")
            continue
        
        mode = archiver._detect_archive_mode(url)
        handlers = {
            'video': ('vídeo único', archiver.download_single_video),
            'playlist': ('playlist', archiver.download_playlist),
            'channel': ('canal', archiver.download_channel),
        }
        handler_info = handlers.get(mode)
        if not handler_info:
            print("❌ URL não reconhecida. Use um link de vídeo, playlist ou canal do YouTube.")
            continue

        mode_name, handler = handler_info
        print(f"\nModo detectado automaticamente: {mode_name}")
        handler(url)

        print("\n" + "="*60)
        print("\nOperação concluída. Voltando ao menu principal.\n")
        print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrompido pelo usuário.")
    except Exception as e:
        print(f"\nErro inesperado: {e}")
        traceback.print_exc()
