import argparse
import contextlib
import importlib
import os
import queue
import re
import threading
import tempfile
import unicodedata
import time
from pathlib import Path
from typing import Dict, List, Tuple
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFont, ImageOps
from proglog import ProgressBarLogger
try:
    # MoviePy 2.x
    from moviepy import ImageClip, VideoFileClip, concatenate_videoclips
except ImportError:
    # MoviePy 1.x exposes the same classes through moviepy.editor.
    moviepy_editor = importlib.import_module("moviepy.editor")
    ImageClip = moviepy_editor.ImageClip
    VideoFileClip = moviepy_editor.VideoFileClip
    concatenate_videoclips = moviepy_editor.concatenate_videoclips


def set_clip_duration(clip, duration: float):
    """Set a clip duration on both MoviePy 1.x and 2.x."""
    if hasattr(clip, "with_duration"):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


class RenderProgressLogger(ProgressBarLogger):
    """Converte o progresso do MoviePy em eventos simples para a GUI."""

    def __init__(self, progress_callback=None):
        super().__init__()
        self.progress_callback = progress_callback
        self.started_at = time.monotonic()

    def bars_callback(self, bar, attr, value, old_value=None):
        if not self.progress_callback or attr != "index":
            return

        progress_bar = self.bars.get(bar, {})
        total = progress_bar.get("total") or 0
        if not total:
            return

        percent = max(0.0, min(100.0, value / total * 100))
        elapsed = time.monotonic() - self.started_at
        self.progress_callback(percent, bar, elapsed)


# ==========================================
# CONFIGURAÇÕES GERAIS E PALETA DE CORES
# ==========================================
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080
COLOR_BG = (0, 0, 0)                  # Preto absoluto
COLOR_PRIMARY = (255, 153, 0)         # Laranja/Amarelo (#FF9900)
COLOR_TEXT = (255, 165, 0)            # Laranja padrão para textos
COLOR_WHITE = (255, 255, 255)


def get_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Carrega uma fonte do sistema com fallback para a fonte padrão do PIL."""
    try:
        return ImageFont.truetype(font_name, size)
    except IOError:
        try:
            # Fallback para sistemas Windows/Linux comuns
            return ImageFont.truetype("arial.ttf", size)
        except IOError:
            try:
                return ImageFont.truetype("DejaVuSans.ttf", size)
            except IOError:
                return ImageFont.load_default()


# ==========================================
# 1. PARSERS DE ARQUIVOS DE TEXTO (.TXT)
# ==========================================
def _normalise_key(value: str) -> str:
    """Normaliza chaves para aceitar acentos, maiusculas e variacoes de nome."""
    value = unicodedata.normalize("NFKD", value)
    return "".join(char for char in value if not unicodedata.combining(char)).lower().strip()


def parse_metadata_file(filepath: str) -> Dict[str, str]:
    """
    Lê o arquivo de metadados no formato chave-valor e bloco de descrição.
    """
    metadata = {
        "titulo": "Sem Título",
        "canal": "Desconhecido",
        "data_upload": "Data Indisponível",
        "visualizacoes": "N/A",
        "likes": "N/A",
        "status": "", #[Vídeo Arquivado]
        "descricao": "",
        "thumb_path": "thumb.jpg",
        "logo_path": "logo.png",
        "watermark_path": "watermark.png"
    }

    metadata_path = Path(filepath).expanduser().resolve()
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Arquivo de metadados não encontrado: {metadata_path}")

    with metadata_path.open("r", encoding="utf-8-sig") as f:
        content = f.read()

    # Separa metadados da descrição
    if "=== Descrição ===" in content:
        header_part, desc_part = content.split("=== Descrição ===", 1)
        metadata["descricao"] = desc_part.strip()
    else:
        header_part = content

    # Processa as linhas de metadados
    for line in header_part.splitlines():
        if ":" in line and not line.startswith("==="):
            key, val = line.split(":", 1)
            key_clean = _normalise_key(key)
            val_clean = val.strip()

            if "titulo" in key_clean:
                metadata["titulo"] = val_clean
            elif "canal" in key_clean:
                metadata["canal"] = val_clean
            elif "data" in key_clean:
                metadata["data_upload"] = val_clean
            elif "visualizacoes" in key_clean or "views" in key_clean:
                metadata["visualizacoes"] = val_clean
            elif "likes" in key_clean:
                metadata["likes"] = val_clean
            elif "status" in key_clean:
                metadata["status"] = val_clean
            elif "thumb" in key_clean or "thumbnail" in key_clean:
                metadata["thumb_path"] = str((metadata_path.parent / val_clean).resolve())
            elif "logo" in key_clean:
                metadata["logo_path"] = str((metadata_path.parent / val_clean).resolve())

    return metadata


def parse_keywords_file(filepath: str) -> List[str]:
    """Lê o arquivo de keywords (uma por linha) e retorna uma lista limpa."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


# ==========================================
# 2. FUNÇÕES AUXILIARES DE IMAGEM
# ==========================================
def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Quebra o texto em múltiplas linhas respeitando a largura máxima em pixels."""
    lines = []
    paragraphs = text.split("\n")

    for paragraph in paragraphs:
        if not paragraph.strip():
            lines.append("")
            continue

        words = paragraph.split(" ")
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

    return lines


def paste_with_alpha(base_img: Image.Image, overlay_img: Image.Image, pos: Tuple[int, int], opacity: float = 1.0):
    """Cola uma imagem RGBA sobre outra respeitando a opacidade informada."""
    if overlay_img.mode != "RGBA":
        overlay_img = overlay_img.convert("RGBA")

    if opacity < 1.0:
        r, g, b, a = overlay_img.split()
        a = a.point(lambda p: int(p * opacity))
        overlay_img = Image.merge("RGBA", (r, g, b, a))

    base_img.paste(overlay_img, pos, mask=overlay_img)


def make_circular_image(img: Image.Image, size: Tuple[int, int]) -> Image.Image:
    """Redimensiona e recorta uma imagem em formato circular com suavização (anti-aliasing)."""
    img = img.resize(size, Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)

    output = Image.new("RGBA", size, (0, 0, 0, 0))
    output.paste(img, (0, 0), mask=mask)
    return output


# ==========================================
# 3. GERAÇÃO DA TELA 1 (AVISO DE FAIR USE)
# ==========================================
def create_disclaimer_screen(watermark_path: str = None) -> Image.Image:
    """Gera a Tela 1: Cartela de aviso de arquivamento e copyright (1920x1080)."""
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG + (255,))
    draw = ImageDraw.Draw(canvas)

    # Marca d'água central
    if watermark_path and os.path.exists(watermark_path):
        wm = Image.open(watermark_path).convert("RGBA")
        wm = wm.resize((350, 350), Image.LANCZOS)
        paste_with_alpha(canvas, wm, ((CANVAS_WIDTH - 350) // 2, 80), opacity=0.9)

    # Fontes
    font_title = get_font("arial.ttf", 60)
    font_body = get_font("arial.ttf", 32)
    font_footer = get_font("arial.ttf", 20)

    # Título "Aviso:"
    title_text = "Aviso:"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    t_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_WIDTH - t_width) // 2, 450), title_text, fill=COLOR_PRIMARY, font=font_title)

    # Texto de aviso central
    body_text = (
        "Não endosso nem assumo qualquer responsabilidade pelo conteúdo, falas ou pelas ações\n"
        "tomadas pelos autores originais durante o vídeo.\n"
        "Seu único propósito é arquivar o vídeo original para fins de registro, para o bem da\n"
        "história da internet."
    )

    lines = body_text.split("\n")
    y_offset = 540
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font_body)
        l_width = bbox[2] - bbox[0]
        draw.text(((CANVAS_WIDTH - l_width) // 2, y_offset), line, fill=COLOR_PRIMARY, font=font_body)
        y_offset += 45

    # Texto de rodapé (Fair Use Section 107)
    footer_text = (
        'Copyright Disclaimer Under Section 107 of the Copyright Act 1976, allowance is made for "fair use" for purposes such as criticism, comment,\n'
        'news reporting, teaching, scholarship, and research. Fair use is a use permitted by copyright statute that might otherwise be infringing.\n'
        'Non-profit, educational or personal use tips the balance in favor of fair use.'
    )

    footer_lines = footer_text.split("\n")
    y_footer = 880
    for line in footer_lines:
        bbox = draw.textbbox((0, 0), line, font=font_footer)
        l_width = bbox[2] - bbox[0]
        draw.text(((CANVAS_WIDTH - l_width) // 2, y_footer), line, fill=COLOR_TEXT, font=font_footer)
        y_footer += 28

    # Ícone d'água miniatura no canto inferior direito
    if watermark_path and os.path.exists(watermark_path):
        wm_small = Image.open(watermark_path).convert("RGBA").resize((50, 50), Image.LANCZOS)
        paste_with_alpha(canvas, wm_small, (CANVAS_WIDTH - 70, CANVAS_HEIGHT - 70), opacity=0.8)

    return canvas.convert("RGB")


# ==========================================
# 4. GERAÇÃO DA TELA 2 (METADADOS E THUMB)
# ==========================================
def create_metadata_screen(metadata: Dict[str, str], watermark_path: str = None) -> Image.Image:
    """Gera a Tela 2: Layout com metadados do vídeo, descrição e thumbnail (1920x1080)."""
    canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG + (255,))
    draw = ImageDraw.Draw(canvas)

    # Marca d'água gigante de fundo (baixa opacidade)
    if watermark_path and os.path.exists(watermark_path):
        wm = Image.open(watermark_path).convert("RGBA")
        wm = wm.resize((900, 900), Image.LANCZOS)
        paste_with_alpha(canvas, wm, ((CANVAS_WIDTH - 900) // 2, (CANVAS_HEIGHT - 900) // 2), opacity=0.12)

    # Fontes
    font_title = get_font("arial.ttf", 46)
    font_meta = get_font("arial.ttf", 30)
    font_section = get_font("arial.ttf", 32)
    font_desc = get_font("arial.ttf", 18)

    # 1. Título do Vídeo no Topo
    titulo = metadata.get("titulo", "Sem Título")
    draw.text((100, 60), titulo, fill=COLOR_PRIMARY, font=font_title)

    # 2. Bloco de Metadados (Lado Esquerdo Topo)
    meta_lines = [
        f"Data de publicação: {metadata.get('data_upload', 'N/A')}",
        f"Canal: {metadata.get('canal', 'N/A')}",
        f"{metadata.get('visualizacoes', '0')} visualizações, {metadata.get('likes', '0')} likes",
        f"{metadata.get('status', '')}" ##[Vídeo Arquivado]
    ]

    y_meta = 150
    for line in meta_lines:
        draw.text((100, y_meta), line, fill=COLOR_PRIMARY, font=font_meta)
        y_meta += 42

    # 3. Bloco da Descrição (Lado Esquerdo Inferior)
    y_desc_head = y_meta + 30
    draw.text((100, y_desc_head), "Descrição do vídeo:", fill=COLOR_PRIMARY, font=font_section)

    desc_text = metadata.get("descricao", "")
    wrapped_desc = wrap_text(desc_text, font_desc, max_width=800, draw=draw)

    # Limita o número de linhas para não estourar a tela
    max_desc_lines = 22
    wrapped_desc = wrapped_desc[:max_desc_lines]

    y_desc = y_desc_head + 45
    for line in wrapped_desc:
        draw.text((100, y_desc), line, fill=COLOR_PRIMARY, font=font_desc)
        y_desc += 22

    # 4. Thumbnail (Lado Direito Central)
    thumb_path = metadata.get("thumb_path", "")
    if os.path.exists(thumb_path):
        thumb = Image.open(thumb_path).convert("RGBA")
        thumb = thumb.resize((650, 365), Image.LANCZOS)
        paste_with_alpha(canvas, thumb, (1000, 360))
        draw.text((1200, 310), "Thumbnail", fill=COLOR_PRIMARY, font=font_section)

    # 5. Logo do Canal (Parte Inferior Direita)
    logo_path = metadata.get("logo_path", "")
    if os.path.exists(logo_path):
        logo_img = Image.open(logo_path)
        circ_logo = make_circular_image(logo_img, (110, 110))
        paste_with_alpha(canvas, circ_logo, (1320, 830))
        draw.text((950, 865), "Logo do canal", fill=COLOR_PRIMARY, font=font_section)

    # Ícone d'água miniatura no canto inferior direito
    if watermark_path and os.path.exists(watermark_path):
        wm_small = Image.open(watermark_path).convert("RGBA").resize((50, 50), Image.LANCZOS)
        paste_with_alpha(canvas, wm_small, (CANVAS_WIDTH - 70, CANVAS_HEIGHT - 70), opacity=0.8)

    return canvas.convert("RGB")


# ==========================================
# 5. PROCESSAMENTO E CONCATENAÇÃO DE VÍDEO
# ==========================================
def render_archival_video(
    main_video_path: str,
    output_video_path: str,
    metadata_file: str,
    keywords_file: str,
    watermark_path: str = None,
    disclaimer_duration: float = 5.0,
    metadata_duration: float = 8.0,
    thumbnail_path: str = None,
    logo_path: str = None,
    encode_preset: str = "veryfast",
    progress_callback=None,
):
    """
    Gera as duas telas de abertura, concatena com o vídeo principal e exporta o resultado.
    """
    main_video = Path(main_video_path).expanduser().resolve()
    output_video = Path(output_video_path).expanduser().resolve()
    metadata_path = Path(metadata_file).expanduser().resolve()
    keywords_path = (
        Path(keywords_file).expanduser().resolve()
        if keywords_file
        else None
    )

    if not main_video.is_file():
        raise FileNotFoundError(f"Vídeo principal não encontrado: {main_video}")
    if not metadata_path.is_file():
        raise FileNotFoundError(f"Arquivo de metadados não encontrado: {metadata_path}")
    print("[1/4] Lendo metadados e keywords...")
    metadata = parse_metadata_file(metadata_file)
    if thumbnail_path:
        metadata["thumb_path"] = str(Path(thumbnail_path).expanduser().resolve())
    if logo_path:
        metadata["logo_path"] = str(Path(logo_path).expanduser().resolve())
    keywords = parse_keywords_file(str(keywords_path)) if keywords_path and keywords_path.is_file() else []
    print(f"      Palavras-chave carregadas ({len(keywords)} encontradas).")

    print("[2/4] Gerando imagens das telas com Pillow...")
    img_disclaimer = create_disclaimer_screen(watermark_path=watermark_path)
    img_metadata = create_metadata_screen(metadata=metadata, watermark_path=watermark_path)

    output_video.parent.mkdir(parents=True, exist_ok=True)

    print("[3/4] Criando clipes de vídeo com MoviePy...")
    with tempfile.TemporaryDirectory(prefix="mega_intro_") as temp_dir:
        disclaimer_image = Path(temp_dir) / "disclaimer.png"
        metadata_image = Path(temp_dir) / "metadata.png"
        img_disclaimer.save(disclaimer_image)
        img_metadata.save(metadata_image)

        clip_disclaimer = set_clip_duration(ImageClip(str(disclaimer_image)), disclaimer_duration)
        clip_metadata = set_clip_duration(ImageClip(str(metadata_image)), metadata_duration)
        main_clip = VideoFileClip(str(main_video))
        final_clip = concatenate_videoclips(
            [clip_disclaimer, clip_metadata, main_clip], method="compose"
        )

        try:
            print("[4/4] Concatenando e renderizando o vídeo final...")
            fps = getattr(main_clip, "fps", None) or 24
            final_clip.write_videofile(
                str(output_video),
                codec="libx264",
                audio_codec="aac",
                fps=fps,
                preset=encode_preset,
                bitrate="8000k",
                threads=os.cpu_count() or 1,
                logger=RenderProgressLogger(progress_callback),
            )
        finally:
            for clip in (final_clip, main_clip, clip_metadata, clip_disclaimer):
                close = getattr(clip, "close", None)
                if close:
                    close()

    print(f"[CONCLUÍDO] Vídeo final gerado com sucesso: {output_video}")


def run_gui():
    """Abre a interface gráfica para configurar e renderizar o vídeo."""
    root = tk.Tk()
    root.title("MEGA Video Archiver")
    root.geometry("760x570")
    root.minsize(700, 500)

    fields = {}
    log_queue = queue.Queue()

    def show_help():
        """Exibe as instruções de uso em uma janela rolável."""
        help_window = tk.Toplevel(root)
        help_window.title("Ajuda - MEGA Video Archiver")
        help_window.geometry("780x650")
        help_window.minsize(620, 450)
        help_window.transient(root)

        frame = ttk.Frame(help_window, padding=12)
        frame.pack(fill="both", expand=True)
        text = tk.Text(frame, wrap="word", padx=10, pady=8)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        help_content = """MEGA VIDEO ARCHIVER - GUIA DE USO

1. FLUXO BÁSICO

1) Selecione o vídeo original.
2) Selecione metadados.txt.
3) Selecione keywords.txt se o vídeo possuir palavras-chave.
4) Selecione thumbnail, logo e marca d'água, quando disponíveis.
5) Escolha o nome e local do vídeo de saída.
6) Ajuste as durações das cartelas e clique em Renderizar vídeo.

O programa cria duas cartelas no início, nesta ordem:
Aviso de arquivamento -> Metadados e thumbnail -> Vídeo original.

2. CAMPOS DA JANELA

Vídeo original:
Arquivo que será preservado. Formatos aceitos: MP4, MKV, MOV e AVI.

Metadados:
Arquivo TXT com título, canal, data, visualizações, likes e descrição.
As chaves reconhecidas incluem Título, Canal, Data de Upload,
Visualizações, Likes, Thumbnail e Logo.

Keywords (opcional):
Arquivo TXT com uma palavra-chave por linha. Ele é contabilizado, mas as
palavras não são desenhadas na cartela. Vídeos sem keywords podem ser
renderizados normalmente; basta deixar este campo vazio.

Thumbnail:
Imagem exibida na parte direita da cartela de metadados.
Logo do canal:
Imagem recortada em círculo na parte inferior da cartela de metadados.
Marca d'água:
Logo usada com transparência no centro das cartelas e em tamanho pequeno
no canto inferior direito.

Vídeo de saída:
É o arquivo MP4 que o programa vai criar com vídeo H.264 e áudio AAC.
Não selecione um vídeo existente neste campo. Escolha apenas o nome e o local
onde o resultado deverá ser salvo, por exemplo: video_arquivado_final.mp4.

3. FORMATOS E RESOLUÇÃO

Vídeo: MP4, MKV, MOV e AVI, desde que o FFmpeg consiga decodificá-los.
Imagens: PNG, JPG, JPEG e WEBP.
Saída: MP4.
As cartelas são sempre geradas em 1920 x 1080.

Resolução recomendada para imagens:

Imagens PNG com fundo transparente são recomendadas para logo e marca d'água.
JPG não possui transparência e pode aparecer com fundo retangular.
Imagens muito pequenas podem perder nitidez quando ampliadas.

4. FORMATO DOS ARQUIVOS TXT

Exemplo de metadados.txt:

Título: Nome do vídeo
Canal: Nome do canal
Data de Upload: 2026-09-22
Visualizações: 10.000
Likes: 500
Thumbnail: thumbnail.jpg
Logo: logo.png

=== Descrição ===
Texto completo da descrição do vídeo.

Os caminhos de Thumbnail e Logo podem ser relativos à pasta do metadados.txt
ou substituídos pelos seletores da janela.

5. DURAÇÕES DAS CARTELAS

Aviso (s): duração da primeira tela. O padrão é 5 segundos.
Metadados (s): duração da segunda tela. O padrão é 8 segundos.
Use números positivos. Vídeos longos ou textos extensos podem precisar de
mais tempo na cartela de metadados.

6. BOAS PRÁTICAS


7. REQUISITOS E ERROS COMUNS

Instale as bibliotecas com:
pip install -r videoCreator\\require.txt

O MoviePy precisa do FFmpeg para ler e renderizar os vídeos. No Windows,
instale o FFmpeg e deixe-o disponível no PATH se o MoviePy não encontrá-lo.
ImageMagick não é necessário.

Se um arquivo não for encontrado, confira o caminho selecionado.
Se a saída falhar, verifique espaço em disco, permissões e se o arquivo de
saída não está aberto em outro programa.
"""
        text.insert("1.0", help_content)
        text.configure(state="disabled")
        ttk.Button(help_window, text="Fechar", command=help_window.destroy).pack(pady=(0, 12))

    def add_file_field(parent, label, filetypes, key, save=False):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=4)
        ttk.Label(row, text=label, width=18).pack(side="left")
        variable = tk.StringVar()
        fields[key] = variable
        ttk.Entry(row, textvariable=variable).pack(side="left", fill="x", expand=True, padx=6)

        def choose_file():
            if save:
                selected = filedialog.asksaveasfilename(
                    title=label, defaultextension=".mp4", filetypes=filetypes
                )
            else:
                selected = filedialog.askopenfilename(title=label, filetypes=filetypes)
            if selected:
                variable.set(selected)

        ttk.Button(row, text="Selecionar...", command=choose_file).pack(side="right")

    main = ttk.Frame(root, padding=16)
    main.pack(fill="both", expand=True)
    title_row = ttk.Frame(main)
    title_row.pack(fill="x")
    ttk.Label(title_row, text="MEGA Video Archiver", font=("Arial", 18, "bold")).pack(side="left")
    ttk.Button(title_row, text="Ajuda", command=show_help).pack(side="right")
    ttk.Label(
        main,
        text="Selecione os arquivos para criar as cartelas e concatená-las ao vídeo.",
    ).pack(anchor="w", pady=(2, 14))

    input_frame = ttk.LabelFrame(main, text="Arquivos", padding=10)
    input_frame.pack(fill="x")
    video_types = [("Vídeos", "*.mp4 *.mkv *.mov *.avi"), ("Todos os arquivos", "*.*")]
    text_types = [("Arquivos de texto", "*.txt"), ("Todos os arquivos", "*.*")]
    image_types = [("Imagens", "*.png *.jpg *.jpeg *.webp"), ("Todos os arquivos", "*.*")]
    add_file_field(input_frame, "Vídeo original", video_types, "video")
    add_file_field(input_frame, "Metadados", text_types, "metadata")
    add_file_field(input_frame, "Keywords (opcional)", text_types, "keywords")
    add_file_field(input_frame, "Thumbnail", image_types, "thumbnail")
    add_file_field(input_frame, "Logo do canal", image_types, "logo")
    add_file_field(input_frame, "Marca d'água", image_types, "watermark")
    add_file_field(input_frame, "Vídeo de saída", [("MP4", "*.mp4")], "output", save=True)

    settings = ttk.Frame(main)
    settings.pack(fill="x", pady=12)
    ttk.Label(settings, text="Aviso (s):").pack(side="left")
    disclaimer_seconds = tk.StringVar(value="5")
    ttk.Entry(settings, textvariable=disclaimer_seconds, width=8).pack(side="left", padx=(5, 20))
    ttk.Label(settings, text="Metadados (s):").pack(side="left")
    metadata_seconds = tk.StringVar(value="8")
    ttk.Entry(settings, textvariable=metadata_seconds, width=8).pack(side="left", padx=5)
    ttk.Label(settings, text="Preset:").pack(side="left", padx=(20, 5))
    encode_preset = tk.StringVar(value="veryfast")
    preset_combo = ttk.Combobox(
        settings,
        textvariable=encode_preset,
        values=("ultrafast", "veryfast", "faster", "fast", "medium"),
        state="readonly",
        width=10,
    )
    preset_combo.pack(side="left")

    log_frame = ttk.LabelFrame(main, text="Progresso", padding=6)
    log_frame.pack(fill="both", expand=True)
    progress_info = ttk.Label(log_frame, text="Aguardando renderização...")
    progress_info.pack(fill="x", pady=(0, 4))
    progress_bar = ttk.Progressbar(log_frame, orient="horizontal", mode="determinate", maximum=100)
    progress_bar.pack(fill="x", pady=(0, 6))
    log_text = tk.Text(log_frame, height=8, state="disabled", wrap="word")
    log_text.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    scrollbar.pack(side="right", fill="y")
    log_text.configure(yscrollcommand=scrollbar.set)

    render_button = ttk.Button(main, text="Renderizar vídeo", command=lambda: start_render())
    render_button.pack(anchor="e", pady=(10, 0))

    def write_log(message):
        log_text.configure(state="normal")
        log_text.insert("end", message)
        log_text.see("end")
        log_text.configure(state="disabled")

    def poll_logs():
        try:
            while True:
                event = log_queue.get_nowait()
                if isinstance(event, tuple) and event[0] == "progress":
                    _, percent, stage, elapsed = event
                    progress_bar.configure(value=percent)
                    progress_info.configure(
                        text=f"{percent:5.1f}% | etapa: {stage} | tempo: {elapsed:.0f}s"
                    )
                elif isinstance(event, tuple) and event[0] == "reset":
                    progress_bar.configure(value=0)
                    progress_info.configure(text=event[1])
                else:
                    write_log(event)
        except queue.Empty:
            pass
        root.after(100, poll_logs)

    def start_render():
        required = {key: fields[key].get().strip() for key in ("video", "metadata", "output")}
        missing = [name for name, value in required.items() if not value]
        if missing:
            messagebox.showwarning("Arquivos ausentes", "Preencha: " + ", ".join(missing))
            return
        try:
            disclaimer = float(disclaimer_seconds.get().replace(",", "."))
            metadata_duration = float(metadata_seconds.get().replace(",", "."))
            if disclaimer <= 0 or metadata_duration <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Duração inválida", "Informe durações positivas em segundos.")
            return

        render_button.configure(state="disabled")
        write_log("Iniciando renderização...\n")
        log_queue.put(("reset", "Preparando vídeo..."))

        def worker():
            try:
                with contextlib.redirect_stdout(_QueueWriter(log_queue)):
                    render_archival_video(
                        main_video_path=required["video"],
                        output_video_path=required["output"],
                        metadata_file=required["metadata"],
                        keywords_file=fields["keywords"].get().strip() or None,
                        watermark_path=fields["watermark"].get().strip() or None,
                        thumbnail_path=fields["thumbnail"].get().strip() or None,
                        logo_path=fields["logo"].get().strip() or None,
                        disclaimer_duration=disclaimer,
                        metadata_duration=metadata_duration,
                        encode_preset=encode_preset.get(),
                        progress_callback=lambda percent, stage, elapsed: log_queue.put(
                            ("progress", percent, stage, elapsed)
                        ),
                    )
                log_queue.put("\nRenderização concluída.\n")
                log_queue.put(("progress", 100.0, "concluído", 0.0))
                root.after(0, lambda: messagebox.showinfo("Concluído", "Vídeo gerado com sucesso."))
            except Exception as error:
                log_queue.put(f"\nERRO: {error}\n")
                root.after(0, lambda: messagebox.showerror("Erro", str(error)))
            finally:
                root.after(0, lambda: render_button.configure(state="normal"))

        threading.Thread(target=worker, daemon=True).start()

    root.after(100, poll_logs)
    root.mainloop()


class _QueueWriter:
    """Adapta print() para o log da janela sem bloquear o thread principal."""

    def __init__(self, output_queue):
        self.output_queue = output_queue

    def write(self, text):
        if text:
            self.output_queue.put(text)

    def flush(self):
        pass


def run_cli():
    """Executa o renderizador pela linha de comandos."""
    parser = argparse.ArgumentParser(description="Cria cartelas de arquivamento e as insere em um vídeo.")
    parser.add_argument("--video", required=True, help="Caminho do vídeo original")
    parser.add_argument("--metadata", required=True, help="Caminho do metadados.txt")
    parser.add_argument("--keywords", help="Caminho opcional do keywords.txt")
    parser.add_argument("--output", required=True, help="Caminho do vídeo final")
    parser.add_argument("--watermark", help="Logo/ marca d'agua usada nas cartelas")
    parser.add_argument("--thumbnail", help="Thumbnail; substitui o caminho do metadados.txt")
    parser.add_argument("--logo", help="Logo do canal; substitui o caminho do metadados.txt")
    parser.add_argument("--disclaimer-seconds", type=float, default=5.0)
    parser.add_argument("--metadata-seconds", type=float, default=8.0)
    parser.add_argument(
        "--preset",
        choices=("ultrafast", "veryfast", "faster", "fast", "medium"),
        default="veryfast",
        help="Preset H.264: mais rápido gera arquivo maior",
    )
    args = parser.parse_args()

    render_archival_video(
        main_video_path=args.video,
        output_video_path=args.output,
        metadata_file=args.metadata,
        keywords_file=args.keywords,
        watermark_path=args.watermark,
        disclaimer_duration=args.disclaimer_seconds,
        metadata_duration=args.metadata_seconds,
        thumbnail_path=args.thumbnail,
        logo_path=args.logo,
        encode_preset=args.preset,
    )


# Sem argumentos, abre a janela. Use --cli para a execução automatizada.
if __name__ == "__main__":
    if len(os.sys.argv) > 1 and os.sys.argv[1] == "--cli":
        os.sys.argv.pop(1)
        run_cli()
    else:
        run_gui()
