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
    page_title="DeepSpec: SPE Paper Scrutinizer",
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

# --- Sidebar: 上传与设置 ---
with st.sidebar:
    st.header("1. 文献导入")
    uploaded_file = st.file_uploader("上传 PDF (SPE Paper)", type="pdf")
    
    if uploaded_file is not None and uploaded_file != st.session_state.uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        # 重置提取结果
        st.session_state.extraction_result = None
        st.session_state.comments = {}
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
    start_btn = st.button("开始深度提取", disabled=(uploaded_file is None or not api_key))
    export_btn = st.button("导出结果到Excel", disabled=(st.session_state.extraction_result is None))
    
    # Word报告导出按钮
    if st.session_state.analyzed_papers and st.button("📥 生成 Word 报告"):
        generate_word_report()

# 模拟数据 (Mock Data) - 在真实开发中，这里会调用 OpenAI API
def get_mock_extraction_result():
    return {
        "summary": [
            {"point": "导流能力在闭合压力超过 6000 psi 时急剧下降。", "source_page": 4, "confidence": "High"},
            {"point": "采用新型涂层后，支撑剂破碎率降低了 18%。", "source_page": 6, "confidence": "High"},
            {"point": "在高温条件下，压裂液的粘度保持稳定。", "source_page": 8, "confidence": "Medium"}
        ],
        "parameters": [
            {"param": "Injection Rate (排量)", "value": "60 bpm", "unit": "bpm", "confidence": "High"},
            {"param": "Proppant Conc. (砂比)", "value": "2-6 ppg", "unit": "ppg", "confidence": "High"},
            {"param": "Fluid Viscosity (粘度)", "value": "N/A", "unit": "cp", "confidence": "Missing"},
            {"param": "Fracture Width (裂缝宽度)", "value": "0.25-0.5 inch", "unit": "inch", "confidence": "Medium"},
            {"param": "Closure Pressure (闭合压力)", "value": "6500 psi", "unit": "psi", "confidence": "Low"}
        ],
        "equations": [
            {
                "name": "导流能力方程",
                "equation": r"k_f w_f = \frac{Q \mu}{2\pi h \Delta P}",
                "description": "裂缝导流能力与流量、流体粘度和压差的关系",
                "source_page": 7
            },
            {
                "name": "支撑剂嵌入方程",
                "equation": r"\delta = \frac{P}{E} \left(1-\nu^2\right)",
                "description": "支撑剂嵌入深度与压力和岩石性质的关系",
                "source_page": 9
            }
        ],
        "figures": [
            {"caption": "Fig 3: 不同闭合压力下的导流能力变化", "source_page": 4},
            {"caption": "Fig 5: 支撑剂破碎率对比", "source_page": 6},
            {"caption": "Fig 7: 温度对压裂液粘度的影响", "source_page": 8}
        ]
    }

# --- Main Interface ---
col_extracted, col_pdf = st.columns([1, 1])

if st.session_state.uploaded_file:
    # 获取PDF文件信息
    file_name = st.session_state.uploaded_file.name
    file_size = st.session_state.uploaded_file.size / (1024 * 1024)  # MB
    
    with col_extracted:
        st.subheader(f"📝 [2] 智能提取报告")
        st.caption(f"文件: {file_name} | 大小: {file_size:.2f} MB")
        
        if start_btn:
            with st.spinner("正在进行智能分析，请稍候..."):
                # 在真实环境中，这里会调用AI提取器
                st.session_state.extraction_result = get_mock_extraction_result()
                
                # 显示处理完成提示
                st.success("✅ 分析完成！请查看下方结果。")
        
        if st.session_state.extraction_result:
            result = st.session_state.extraction_result
            
            # 1. 结论部分
            st.markdown('<h3 class="section-header">📌 核心结论 (Fact-Check)</h3>', unsafe_allow_html=True)
            
            for i, item in enumerate(result["summary"]):
                confidence_class = {
                    "High": "highlight-green",
                    "Medium": "highlight-yellow",
                    "Low": "highlight-red"
                }.get(item["confidence"], "highlight-yellow")
                
                with st.container():
                    st.markdown(f'<div class="{confidence_class}">', unsafe_allow_html=True)
                    st.markdown(f"**📄 P{item['source_page']}**: {item['point']}")
                    st.markdown(f"**置信度**: {item['confidence']}")
                    
                    # 添加定位按钮
                    if st.button(f"定位到原文", key=f"summary_{i}"):
                        st.session_state.target_page = item['source_page']
                        st.session_state.highlight_text = item['point'][:20]  # 高亮部分文本
                    
                    st.markdown('</div>', unsafe_allow_html=True)
            
            # 2. 关键参数表 (带红绿灯)
            st.markdown('<h3 class="section-header">📊 关键参数 (Inputs)</h3>', unsafe_allow_html=True)
            
            # 将数据转换为 DataFrame 展示
            df = pd.DataFrame(result["parameters"])
            
            # 添加样式
            def color_confidence(val):
                if val == 'Missing':
                    return 'background-color: #f8d7da'
                elif val == 'Low':
                    return 'background-color: #fff3cd'
                elif val == 'Medium':
                    return 'background-color: #fff3cd'
                else:
                    return 'background-color: #d4edda'
            
            styled_df = df.style.applymap(color_confidence, subset=['confidence'])
            st.dataframe(styled_df, use_container_width=True)
            
            st.caption("🔴 红色代表原文未找到或需人工核实 | 🟡 黄色代表推断内容 | 🟢 绿色代表明确提及")
            
            # 3. 公式部分 (LaTeX 核心)
            st.markdown('<h3 class="section-header">📐 核心控制方程</h3>', unsafe_allow_html=True)
            
            for i, eq in enumerate(result["equations"]):
                with st.expander(f"{eq['name']} (来源: P{eq['source_page']})"):
                    st.markdown(f"**说明**: {eq['description']}")
                    st.latex(eq['equation'])
                    
                    # 添加复制按钮
                    st.code(eq['equation'], language="latex")
                    
                    # 添加定位按钮
                    if st.button(f"定位到公式来源", key=f"eq_{i}"):
                        st.session_state.target_page = eq['source_page']
                        st.session_state.highlight_text = eq['name']
            
            # 4. 图表部分
            st.markdown('<h3 class="section-header">📈 关键图表</h3>', unsafe_allow_html=True)
            
            for i, fig in enumerate(result["figures"]):
                with st.container():
                    st.markdown(f"**{fig['caption']}** (来源: P{fig['source_page']})")
                    if st.button(f"查看图表", key=f"fig_{i}"):
                        st.session_state.target_page = fig['source_page']
                        st.session_state.highlight_text = fig['caption'][:10]
            
            # 5. 用户批注
            st.markdown('<h3 class="section-header">🧠 专家批注</h3>', unsafe_allow_html=True)
            
            # 初始化批注输入
            comment_key = "general_comment"
            if comment_key not in st.session_state.comments:
                st.session_state.comments[comment_key] = ""
            
            comment = st.text_area(
                "输入你的 Comments (将同步到 Excel):",
                value=st.session_state.comments[comment_key],
                placeholder="例如：该实验未考虑温度对粘度的影响...",
                key=comment_key
            )
            st.session_state.comments[comment_key] = comment
    
    with col_pdf:
        st.subheader("🔎 [3] 原文溯源")
        
        # 显示PDF预览
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
                
                # 高亮显示文本
                highlight_text = st.session_state.get('highlight_text', '')
                if highlight_text and highlight_text in page_text:
                    # 简单高亮显示（在真实应用中可能需要更复杂的处理）
                    highlighted_text = page_text.replace(
                        highlight_text, 
                        f"**<mark style='background-color: yellow;'>{highlight_text}</mark>**"
                    )
                    st.markdown(highlighted_text, unsafe_allow_html=True)
                else:
                    st.text_area("页面内容:", value=page_text, height=500)
                
                # 显示页面图片
                # 首先尝试显示整个页面
                full_page_image = st.session_state.pdf_processor.get_page_as_image(selected_page)
                if full_page_image:
                    try:
                        # 显示base64编码的图像
                        st.image(f"data:image/png;base64,{full_page_image['base64']}", 
                                caption=f"页面 {selected_page}")
                    except Exception as e:
                        st.info(f"无法显示完整页面图像: {str(e)}")
                
                # 然后显示页面中提取的图像
                page_images = st.session_state.pdf_processor.get_page_image(selected_page)
                if page_images:
                    st.subheader("页面中的图像:")
                    for i, img_data in enumerate(page_images):
                        try:
                            # 显示base64编码的图像
                            st.image(f"data:image/png;base64,{img_data['base64']}", 
                                    caption=f"页面 {selected_page} - 图像 {i+1}")
                        except Exception as e:
                            st.info(f"无法显示图像 {i+1}: {str(e)}")
        else:
            st.info("请在左侧上传PDF文件并开始分析")
        
        if 'target_page' in st.session_state:
            st.session_state.pop('target_page')
        if 'highlight_text' in st.session_state:
            st.session_state.pop('highlight_text')
else:
    col_extracted.info("请在左侧上传 SPE 论文 PDF 以开始。")
    col_pdf.info("PDF 预览区域")

# 导出功能
if export_btn and st.session_state.extraction_result:
    with st.spinner("正在导出结果..."):
        # 在真实环境中，这里会调用格式化器
        export_filename = f"DeepSpec_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        st.success(f"✅ 结果已导出为 {export_filename}！")
        
        # 提供下载链接
        st.download_button(
            label="下载导出文件",
            data=pd.DataFrame(st.session_state.extraction_result["parameters"]).to_csv(index=False),
            file_name=f"DeepSpec_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

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
                if 'image' in paper and paper['image']:
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

# 底部信息
st.markdown("---")
st.markdown("© 2023 DeepSpec Pro: SPE Paper Scrutinizer - 为石油工程师打造的专业文献分析工具")