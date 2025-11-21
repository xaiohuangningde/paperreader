from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ROW_HEIGHT_RULE
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
# 设置非交互式后端，防止多线程报错
matplotlib.use('Agg')

class WordReportGenerator:
    def __init__(self):
        self.document = Document()
        # 1. 页面设置：横向布局 (Landscape) 以容纳大宽表
        section = self.document.sections[0]
        section.orientation = 1  # Landscape
        section.page_width = Inches(11.69)  # A4 Width
        section.page_height = Inches(8.27)  # A4 Height
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        
        # 2. 标题
        heading = self.document.add_heading('SPE 文献深度综述矩阵', 0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # 3. 初始化主表格 (Master Table)
        self.table = self.document.add_table(rows=1, cols=5)
        self.table.style = 'Table Grid'
        self.table.autofit = False  # 关闭自动调整，强制使用固定列宽
        self.table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        # 4. 设置列宽 (总宽约 10.5 英寸)
        # 比例: Article(10%), Content1(25%), Content2(35%), Comments(20%), Why(10%)
        widths = [Inches(1.2), Inches(2.8), Inches(3.8), Inches(1.8), Inches(0.9)]
        for i, width in enumerate(widths):
            for cell in self.table.columns[i].cells:
                cell.width = width

        # 5. 设置表头
        headers = ["Article", "具体内容 (1)\n目的与核心结论", "具体内容 (2)\n参数、公式与图表", "Comments\n(专家想法)", "Why\n(Tags)"]
        hdr_cells = self.table.rows[0].cells
        for i, text in enumerate(headers):
            cell = hdr_cells[i]
            # 锁定表头宽度
            cell.width = widths[i]
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run(text)
            run.bold = True
            run.font.size = Pt(10)
            run.font.name = '微软雅黑'
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            # 灰色背景
            self._set_cell_background(cell, "E7E6E6")

    def _set_cell_background(self, cell, color):
        shading_elm = parse_xml(r'<w:shd {} w:fill="{}"/>'.format(nsdecls('w'), color))
        cell._tc.get_or_add_tcPr().append(shading_elm)

    def _render_latex_to_image(self, latex_string):
        """渲染 LaTeX 为透明背景图片"""
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 估算公式长度以调整画布
            fig_width = max(4, len(latex_string) * 0.15)
            fig = plt.figure(figsize=(fig_width, 1))
            
            # 渲染公式
            text = fig.text(0.5, 0.5, f"${latex_string}$", fontsize=14, 
                           ha='center', va='center', alpha=1.0)
            
            buffer = BytesIO()
            # 关键：透明背景，紧凑剪裁
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.1, transparent=True, dpi=200)
            buffer.seek(0)
            plt.close(fig)
            return buffer
        except Exception as e:
            print(f"LaTeX Render Error: {e}")
            return None

    def add_paper_row(self, data, image_stream=None):
        """向主表格添加一行"""
        row_cells = self.table.add_row().cells
        
        # 再次强制设置这一行的列宽（Word有时会重置）
        widths = [Inches(1.2), Inches(2.8), Inches(3.8), Inches(1.8), Inches(0.9)]
        for i, width in enumerate(widths):
            row_cells[i].width = width

        # --- Col 1: Article ---
        p = row_cells[0].paragraphs[0]
        p.add_run(data.get('title', 'N/A')).bold = True
        p.runs[0].font.size = Pt(9)

        # --- Col 2: 目的与结论 ---
        p = row_cells[1].paragraphs[0]
        # 目的
        p.add_run("【研究目的】\n").bold = True
        p.add_run(f"{data.get('purpose', 'N/A')}\n\n")
        # 结论
        p.add_run("【核心结论】\n").bold = True
        conclusions = data.get('conclusion', [])
        if isinstance(conclusions, str): conclusions = [conclusions]
        for idx, point in enumerate(conclusions, 1):
            p.add_run(f"{idx}. {point}\n")
        
        # 格式调整
        for run in p.runs:
            run.font.size = Pt(9)

        # --- Col 3: 参数、公式与图表 (核心区域) ---
        p = row_cells[2].paragraphs[0]
        
        # 1. 参数
        p.add_run("【关键参数】\n").bold = True
        p.add_run(f"{data.get('params', 'N/A')}\n")
        
        # 2. 公式
        formulas = data.get('formulas', [])
        if formulas:
            p.add_run("\n【控制方程】\n").bold = True
            if isinstance(formulas, str): formulas = [formulas]
            for form in formulas:
                # 尝试渲染图片
                img_buf = self._render_latex_to_image(form)
                if img_buf:
                    row_cells[2].add_paragraph().add_run().add_picture(img_buf, height=Inches(0.6))
                else:
                    # 降级显示文本
                    p.add_run(f"$$ {form} $$\n")

        # 3. 关键图表 (嵌入)
        if image_stream:
            p.add_run("\n【图表证据】\n").bold = True
            # 插入图片并限制宽度，防止撑破表格
            pic_p = row_cells[2].add_paragraph()
            pic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = pic_p.add_run()
            run.add_picture(image_stream, width=Inches(3.5)) # 略小于列宽

        # --- Col 4: Comments ---
        p = row_cells[3].paragraphs[0]
        p.add_run(data.get('comments', 'N/A'))
        p.runs[0].font.size = Pt(9)

        # --- Col 5: Why ---
        p = row_cells[4].paragraphs[0]
        p.add_run(data.get('why', 'N/A'))
        p.runs[0].font.size = Pt(9)

    def add_paper_analysis(self, data, image_stream=None):
        """
        添加论文分析到报告（别名方法，兼容旧代码）
        
        Args:
            data: 字典，包含 'title', 'purpose', 'conclusion', 'params', 'formulas', 'comments', 'why', 'page_source'
            image_stream: 图片的字节流 (BytesIO)，如果没有则为 None
        """
        return self.add_paper_row(data, image_stream)

    def save_to_bytes(self):
        buffer = BytesIO()
        self.document.save(buffer)
        buffer.seek(0)
        return buffer