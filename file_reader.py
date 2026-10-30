"""文件解析模块：把用户上传的资料（文献/图片/课件）变成 AI 能读的内容。

支持格式：
- 文献：pdf / docx（Word）
- 图片：jpg / jpeg / png / tiff / tif / bmp（TIFF/BMP 会转成 PNG 再交给视觉模型）
- 课件：pptx

对外只暴露一个函数 extract_file_content()：
- 文本类文件 → 返回提取出的纯文本
- 图片文件   → 返回 {"type": "image", "data": base64, "mime": "image/png"}
"""
import base64
import io

from docx import Document
from pptx import Presentation
from pypdf import PdfReader

# 各类文件允许的扩展名（小写）
TEXT_EXTS = {".pdf", ".docx"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
PPTX_EXTS = {".pptx"}

# 单个文本文件最多提取的字符数（防止超长文献撑爆上下文）
MAX_TEXT_CHARS = 20000


def extract_file_content(file_storage):
    """解析一个 Werkzeug FileStorage，返回统一结构。

    返回 dict：
    - {"kind": "text",  "filename": ..., "text": ...}
    - {"kind": "image", "filename": ..., "data": base64str, "mime": ...}
    - {"kind": "error", "filename": ..., "message": ...}（解析失败时）
    """
    filename = file_storage.filename or "未命名文件"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if ext in TEXT_EXTS:
            return {"kind": "text", "filename": filename,
                    "text": _extract_text(file_storage, ext)}
        if ext in IMAGE_EXTS:
            return _extract_image(file_storage, filename)
        if ext in PPTX_EXTS:
            return {"kind": "text", "filename": filename,
                    "text": _extract_pptx(file_storage)}
        return {"kind": "error", "filename": filename,
                "message": f"不支持的文件类型：{ext or '无扩展名'}（支持 pdf/docx/jpg/tiff/pptx）"}
    except Exception as exc:  # 解析失败不能让整个请求崩掉，逐文件报错
        return {"kind": "error", "filename": filename,
                "message": f"解析失败：{exc}"}


def _extract_text(file_storage, ext):
    """提取 pdf / docx 的正文文本。"""
    if ext == ".pdf":
        reader = PdfReader(file_storage)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages)
    else:  # docx
        doc = Document(file_storage)
        parts = [p.text for p in doc.paragraphs]
        # 表格里的文字也要（实验数据常在表格里）
        for table in doc.tables:
            for row in table.rows:
                parts.append(" | ".join(cell.text for cell in row.cells))
        text = "\n".join(parts)

    text = text.strip()
    if not text:
        raise ValueError("没有提取到文字（可能是扫描版 PDF，图片为主）")
    return text[:MAX_TEXT_CHARS]


def _extract_pptx(file_storage):
    """提取 pptx 每页幻灯片的文字（正文 + 备注）。"""
    prs = Presentation(file_storage)
    parts = []
    for i, slide in enumerate(prs.slides, start=1):
        lines = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = "".join(run.text for run in para.runs)
                    if line.strip():
                        lines.append(line)
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            note = slide.notes_slide.notes_text_frame.text.strip()
            if note:
                lines.append(f"[备注] {note}")
        parts.append(f"--- 第 {i} 页 ---\n" + "\n".join(lines))
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("PPT 里没有提取到文字")
    return text[:MAX_TEXT_CHARS]


def _extract_image(file_storage, filename):
    """图片统一转成 PNG 的 base64（视觉模型一般只认 jpg/png/webp，不认 tiff/bmp）。"""
    from PIL import Image

    img = Image.open(file_storage)
    # CMYK / 带透明通道等模式统一转 RGB，避免保存 PNG 时报错
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # 过大的图片缩到最长边 1600px：视觉模型输入有限，太大也浪费 token
    if max(img.size) > 1600:
        img.thumbnail((1600, 1600))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return {"kind": "image", "filename": filename, "data": b64, "mime": "image/png"}
