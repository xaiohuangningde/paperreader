import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
import openai
import json
from datetime import datetime
import base64
import re
from PIL import Image

# 导入自定义工具模块
try:
    from utils.pdf_processor import PDFProcessor
    from utils.ai_extractor import AIExtractor
    from utils.formatter import ResultFormatter
    from utils.report_generator import WordReportGenerator
    from utils.image_cropper import ImageCropper
    from utils.structured_extractor import StructuredExtractor
except ImportError as e:
    st.error(f"导入自定义模块失败: {str(e)}")
    st.stop()

# 加载环境变量
load_dotenv()

# 页面设置：宽屏模式，模拟仪表盘
st.set_page_config(
    layout="wide", 
    page_title="DeepSpec Pro",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2ca02c;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .highlight-green {
        background-color: #d4edda;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #28a745;
    }
    .highlight-yellow {
        background-color: #fff3cd;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #ffc107;
    }
    .highlight-red {
        background-color: #f8d7da;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #dc3545;
    }
    .parameter-table {
        width: 100%;
        border-collapse: collapse;
    }
    .parameter-table th, .parameter-table td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    .parameter-table th {
        background-color: #f2f2f2;
    }
    .confidence-high {
        background-color: #d4edda;
    }
    .confidence-medium {
        background-color: #fff3cd;
    }
    .confidence-low {
        background-color: #f8d7da;
    }
    .equation-container {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: 'Courier New', Courier, monospace;
    }
    .source-link {
        color: #1f77b4;
        text-decoration: none;
        font-weight: bold;
    }
    .source-link:hover {
        text-decoration: underline;
    }
    .paper-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
        background-color: white;
    }
    .selected-paper {
        border: 2px solid #1f77b4;
        box-shadow: 0 0 5px rgba(31, 119, 180, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# 初始化Session State
def init_session_state():
    if 'pdf_processor' not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor()
    if 'ai_extractor' not in st.session_state:
        st.session_state.ai_extractor = AIExtractor()
    if 'structured_extractor' not in st.session_state:
        st.session_state.structured_extractor = StructuredExtractor()
    if 'formatter' not in st.session_state:
        st.session_state.formatter = ResultFormatter()
    if 'extraction_result' not in st.session_state:
        st.session_state.extraction_result = None
    if 'structured_data' not in st.session_state:
        st.session_state.structured_data = None
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'comments' not in st.session_state:
        st.session_state.comments = {}
    if 'analyzed_papers' not in st.session_state:
        st.session_state.analyzed_papers = []
    if 'cropped_images' not in st.session_state:
        st.session_state.cropped_images = []

# 初始化Session State
init_session_state()

# 主标题
st.markdown('<h1 class="main-header">DeepSpec Pro: SPE Paper Scrutinizer 🚀</h1>', unsafe_allow_html=True)
st.markdown("---")

# --- Sidebar: 上传与控制 ---
with st.sidebar:
    st.header("1. 文献导入")
    uploaded_file = st.file_uploader("上传 PDF (SPE Paper)", type="pdf")
    
    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        # 重置提取结果
        st.session_state.extraction_result = None
        st.session_state.structured_data = None
        st.session_state.comments = {}
        st.session_state.cropped_images = []
        # 处理PDF
        with st.spinner("正在处理PDF文件..."):
            st.session_state.pdf_processor.process_pdf(uploaded_file)
    
    st.header("2. 科学家设定")
    role = st.selectbox("当前角色", ["水力压裂专家", "油藏数值模拟专家", "机器学习专家", "通用研究员"])
    
    api_key = st.text_input("OpenAI API Key", type="password")
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
    
    st.header("3. 分析模式")
    extraction_mode = st.selectbox(
        "提取模式",
        ["快速提取", "标准提取", "深度提取"],
        index=1,
        help="不同模式会影响分析的深度和准确性"
    )
    
    st.header("4. 操作")
    
    # 分析按钮
    if st.button("🤖 AI 分析", disabled=(uploaded_file is None or not api_key)):
        with st.spinner("正在像首席科学家一样阅读..."):
            try:
                # 获取PDF文本（简化处理，实际应该从PDF处理器中获取）
                pages_text = ""
                for i, page in enumerate(st.session_state.pdf_processor.pages[:5]):  # 只处理前5页
                    page_text = page.extract_text()
                    if page_text:
                        pages_text += f"Page {i+1}:\n{page_text}\n\n"
                
                # 使用结构化提取器获取数据
                if pages_text:
                    st.session_state.structured_data = st.session_state.structured_extractor.extract_structured_data(
                        pages_text, role, extraction_mode
                    )
                else:
                    # 使用模拟数据
                    st.session_state.structured_data = st.session_state.structured_extractor.get_mock_structured_data()
                
                st.success("✅ 分析完成！")
            except Exception as e:
                st.error(f"分析失败: {str(e)}")
                # 使用模拟数据作为后备
                st.session_state.structured_data = st.session_state.structured_extractor.get_mock_structured_data()
                st.info("已使用模拟数据进行分析")
    
    # 导出按钮
    if st.session_state.analyzed_papers and st.button("📥 生成 Word 报告"):
        generate_word_report()

# --- 主界面 ---
if st.session_state.uploaded_file:
    file_name = st.session_state.uploaded_file.name
    file_size = st.session_state.uploaded_file.size / (1024 * 1024)  # MB
    
    st.caption(f"文件: {file_name} | 大小: {file_size:.2f} MB")
    
    if st.session_state.structured_data:
        data = st.session_state.structured_data
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📝 编辑内容 (所见即所得)")
            
            # 允许用户修改AI的结果
            title = st.text_input("论文标题", value=data.get('title', ''))
            purpose = st.text_area("研究目的", value=data.get('purpose', ''), height=100)
            
            # 编辑结论
            st.write("**核心结论:**")
            conclusions = data.get('conclusion', [])
            if isinstance(conclusions, str):
                conclusions = [conclusions]
            
            edited_conclusions = []
            for i, conclusion in enumerate(conclusions):
                with st.expander(f"结论 {i+1}", expanded=True):
                    edited_conclusion = st.text_area(
                        f"结论 {i+1}",
                        value=conclusion,
                        key=f"conclusion_{i}"
                    )
                    edited_conclusions.append(edited_conclusion)
            
            # 编辑参数
            params = st.text_area("详细参数", value=data.get('params', ''), height=100)
            
            # 编辑公式
            st.write("**核心公式:**")
            formulas = data.get('formulas', [])
            if isinstance(formulas, str):
                formulas = [formulas]
            
            edited_formulas = []
            for i, formula in enumerate(formulas):
                with st.expander(f"公式 {i+1}", expanded=False):
                    edited_formula = st.text_area(
                        f"公式 {i+1}",
                        value=formula,
                        key=f"formula_{i}"
                    )
                    edited_formulas.append(edited_formula)
            
            # 编辑评论和标签
            comments = st.text_area("Comments (想法)", value=data.get('comments', ''))
            why = st.text_area("Why (标签)", value=data.get('why', ''))
            
            # 存储编辑后的数据
            edited_data = {
                'title': title,
                'purpose': purpose,
                'conclusion': edited_conclusions,
                'params': params,
                'formulas': edited_formulas,
                'comments': comments,
                'why': why,
                'page_source': data.get('page_source', '')
            }
            
            # 添加到报告按钮
            if st.button("➕ 将此条目添加到 Word 报告"):
                # 获取选中的图片
                selected_image = None
                if 'selected_image_index' in st.session_state and st.session_state.selected_image_index >= 0:
                    if st.session_state.selected_image_index < len(st.session_state.cropped_images):
                        selected_image = st.session_state.cropped_images[st.session_state.selected_image_index]
                
                # 创建条目
                entry = {
                    "title": title,
                    "purpose": purpose,
                    "conclusion": edited_conclusions,
                    "params": params,
                    "formulas": edited_formulas,
                    "comments": comments,
                    "why": why,
                    "page_source": data.get('page_source', ''),
                    "image": selected_image
                }
                
                # 添加到已分析论文列表
                st.session_state.analyzed_papers.append(entry)
                
                # 显示成功消息
                st.toast(f"✅ 已添加！当前报告已有 {len(st.session_state.analyzed_papers)} 篇文献。")
                
                # 清空选中的图片
                if 'selected_image_index' in st.session_state:
                    st.session_state.selected_image_index = -1
        
        with col2:
            st.subheader("📸 截图证据")
            
            # 显示PDF页面图片选择
            page_count = st.session_state.pdf_processor.get_page_count()
            
            if page_count > 0:
                selected_page = st.selectbox(
                    "选择页面",
                    options=list(range(1, page_count + 1)),
                    format_func=lambda x: f"第 {x} 页"
                )
                
                # 获取页面图像
                page_image = ImageCropper.extract_pdf_page_as_image(
                    st.session_state.pdf_processor, 
                    selected_page
                )
                
                if page_image:
                    st.image(page_image, caption=f"第 {selected_page} 页", use_column_width=True)
                    
                    # 裁剪图片
                    st.write("### 图片裁剪")
                    cropped_image = ImageCropper.crop_image_with_streamlit(page_image, f"page_{selected_page}")
                    
                    if cropped_image:
                        st.image(cropped_image, caption="裁剪后的图片", use_column_width=True)
                        
                        if st.button(f"将此图片添加到报告", key=f"add_cropped_{selected_page}"):
                            st.session_state.cropped_images.append(cropped_image)
                            st.toast(f"已添加裁剪图片！当前有 {len(st.session_state.cropped_images)} 张图片。")
            
            # 显示已裁剪的图片
            if st.session_state.cropped_images:
                st.write("### 已裁剪的图片")
                for i, img in enumerate(st.session_state.cropped_images):
                    col_img, col_btn = st.columns([3, 1])
                    
                    with col_img:
                        if st.image(img, caption=f"图片 {i+1}", use_column_width=True):
                            pass
                    
                    with col_btn:
                        if st.button(f"使用", key=f"use_img_{i}"):
                            st.session_state.selected_image_index = i
                            st.toast(f"已选择图片 {i+1} 用于插入到报告中")
                        
                        if st.button(f"删除", key=f"del_img_{i}"):
                            st.session_state.cropped_images.pop(i)
                            st.experimental_rerun()
    
    # PDF预览区域
    st.markdown("---")
    st.subheader("🔎 PDF 预览")
    
    if hasattr(st.session_state.pdf_processor, 'pages'):
        page_count = len(st.session_state.pdf_processor.pages)
        
        # 页面选择器
        target_page = st.session_state.get('target_page', 1)
        if target_page < 1 or target_page > page_count:
            target_page = 1
        
        selected_page = st.number_input(
            f"选择页面 (1-{page_count})",
            min_value=1,
            max_value=page_count,
            value=target_page
        )
        
        # 显示页面内容
        if selected_page <= page_count:
            page = st.session_state.pdf_processor.pages[selected_page-1]
            
            # 获取页面文本
            try:
                page_text = page.extract_text()
                if not page_text:
                    page_text = "此页无文本内容"
            except Exception as e:
                page_text = f"提取文本时出错: {str(e)}"
            
            # 显示文本
            st.text_area("页面内容:", value=page_text, height=300)
            
            # 显示页面图像
            full_page_image = st.session_state.pdf_processor.get_page_as_image(selected_page)
            if full_page_image:
                try:
                    st.image(f"data:image/png;base64,{full_page_image['base64']}", 
                            caption=f"页面 {selected_page}")
                except Exception as e:
                    st.info(f"无法显示完整页面图像: {str(e)}")
else:
    st.info("请在左侧上传 SPE 论文 PDF 以开始。")

# --- 底部：已添加的论文列表 ---
if st.session_state.analyzed_papers:
    st.markdown("---")
    st.subheader(f"📋 已添加的论文 ({len(st.session_state.analyzed_papers)} 篇)")
    
    for i, paper in enumerate(st.session_state.analyzed_papers):
        with st.expander(f"{i+1}. {paper['title']}", expanded=False):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**目的**: {paper['purpose']}")
                st.write(f"**评论**: {paper['comments']}")
            
            with col2:
                if paper['image']:
                    st.image(paper['image'], caption="关键图表", width=150)
            
            with col3:
                if st.button(f"删除", key=f"del_paper_{i}"):
                    st.session_state.analyzed_papers.pop(i)
                    st.experimental_rerun()

# --- Word文档生成函数 ---
def generate_word_report():
    """生成Word文档"""
    if not st.session_state.analyzed_papers:
        st.error("没有可导出的论文")
        return
    
    with st.spinner("正在生成Word文档..."):
        try:
            # 创建Word报告生成器
            report_gen = WordReportGenerator()
            
            # 添加每篇论文的分析
            for paper in st.session_state.analyzed_papers:
                image_stream = None
                if paper['image']:
                    # 将PIL图像转换为字节流
                    img_buffer = BytesIO()
                    paper['image'].save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    image_stream = img_buffer
                
                report_gen.add_paper_analysis(paper, image_stream=image_stream)
            
            # 保存到字节流
            buffer = report_gen.save_to_bytes()
            
            # 提供下载按钮
            st.download_button(
                label="📥 下载 Word 报告",
                data=buffer,
                file_name=f"SPE_Literature_Review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            
            st.success("✅ Word 报告生成成功！")
            
        except Exception as e:
            st.error(f"生成Word文档时出错: {str(e)}")

# --- 底部信息 ---
st.markdown("---")
st.markdown("© 2023 DeepSpec Pro: SPE Paper Scrutinizer - 为石油工程师打造的专业文献分析工具")