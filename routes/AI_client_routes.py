from flask import Flask , Blueprint , request , render_template

from ai_client import client
from file_reader import extract_file_content
from models import AI_Models
import time
import datetime

"""规定模型分工机制：
    DSV4负责解析文本
    MMM-3负责解析图片"""

AI_client_bp = Blueprint('AI_client_bp' , __name__ , url_prefix='/read')
@AI_client_bp.route("/", methods=["POST"])
def read_files():
    """接收用户上传的资料（文献/图片/课件），交给 AI 阅读识别。

    双模型分工：
    - 文本类（pdf/docx/pptx）→ DeepSeek-V4-Pro（顶尖文本模型，中文友好）
    - 图片类（jpg/tiff 等）  → MiniMax-M3（视觉多模态模型）
    """
    files = request.files.getlist("materials")
    if not files or all(f.filename == "" for f in files):
        return render_template("index.html", ai_text="请先选择至少一个文件。")

    # 逐个解析：文本类和图片类分开收集
    text_parts = []
    images = []
    errors = []
    for f in files:
        parsed = extract_file_content(f)
        if parsed["kind"] == "text":
            text_parts.append(f"【文件：{parsed['filename']}】\n{parsed['text']}")
        elif parsed["kind"] == "image":
            images.append(parsed)
        else:
            errors.append(f"{parsed['filename']}：{parsed['message']}")

    if not text_parts and not images:
        # 全部解析失败，直接把原因告诉用户，不调 AI
        return render_template("index.html", ai_text="文件解析失败：\n" + "\n".join(errors))

    sections = []  # 每类资料的处理结果，最后拼在一起展示

    # ── 1. 文本资料 → DeepSeek-V4-Pro ──────────────────────────────
    if text_parts:
        try:
            response = client.chat.completions.create(
                model="DeepSeek-V4-Pro",
                messages=[
                    {"role": "system", "content": "你是科研资料阅读助手。用户会给你文献或课件，请阅读并识别其中的内容，输出结构化总结：主题、关键信息、与实验报告相关的可用要点。"},
                    {"role": "user", "content": "请阅读以下资料，总结要点：\n\n" + "\n\n".join(text_parts)},
                ],
            )
            sections.append("📄 文献/课件总结（DeepSeek-V4-Pro）：\n" + response.choices[0].message.content)
        except Exception as exc:
            sections.append(f"📄 文献/课件处理失败：{exc}")

    # ── 2. 图片资料 → MiniMax-M3（视觉多模态） ─────────────────────
    for img in images:
        try:
            response = client.chat.completions.create(
                model="MiniMax-M3",
                messages=[
                    {"role": "system", "content": "你是图像识别助手。请识别图片内容，输出：图片类型（照片/图表/截图等）、主要内容、与实验报告相关的可用信息（如仪器读数、数据、曲线趋势）。"},
                    {"role": "user", "content": [
                        {"type": "text", "text": f"请识别这张图片（文件名：{img['filename']}）的内容。"},
                        {"type": "image_url", "image_url": {"url": f"data:{img['mime']};base64,{img['data']}"}},
                    ]},
                ],
            )
            sections.append(f"🖼 图片识别（MiniMax-M3）— {img['filename']}：\n" + response.choices[0].message.content)
        except Exception as exc:
            sections.append(f"🖼 图片 {img['filename']} 识别失败：{exc}")

    # 解析失败的文件清单附在最后
    if errors:
        sections.append("⚠️ 以下文件解析失败：\n" + "\n".join(errors))

    return render_template("index.html", ai_text="\n\n".join(sections))

# @AI_client_bp('/save')
# def save():
#     """
#     把生成段落的负责AI的名字记录下来
#     """
#     ai_models = AI_Models()
#     ai_models.assigned_at(datetime.now())