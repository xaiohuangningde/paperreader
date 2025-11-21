import streamlit as st
import pandas as pd
from io import BytesIO
import os
import sys
import traceback
from dotenv import load_dotenv
from PIL import Image
import logging

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 引入工具模块
try:
    from utils.pdf_processor import PDFProcessor
    from utils.ai_extractor import AIExtractor
    from utils.structured_extractor import StructuredExtractor
    from utils.report_generator import WordReportGenerator
    from utils.image_cropper import ImageCropper
    logger.info("✅ 成功导入所有自定义模块")
except ImportError as e:
    st.error(f"❌ 核心模块导入失败: {str(e)}")
    st.error(f"请确保 utils 文件夹存在且包含所有必需的模块文件")
    st.error(f"当前工作目录: {os.getcwd()}")
    st.error(f"系统路径: {sys.path}")
    st.stop()

load_dotenv()

st.set_page_config(layout="wide", page_title="DeepSpec Debug Mode", initial_sidebar_state="expanded")

# --- 全局状态初始化 ---
if 'papers_data' not in st.session_state:
    st.session_state.papers_data = {}
    logger.info("初始化 papers_data")
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
    logger.info("初始化 current_file")
if 'word_buffer' not in st.session_state:
    st.session_state.word_buffer = None
    logger.info("初始化 word_buffer")
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []
    logger.info("初始化 debug_logs")

def add_debug_log(message):
    """添加调试日志"""
    timestamp = pd.Timestamp.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    st.session_state.debug_logs.append(log_entry)
    logger.info(log_entry)

# --- CSS 样式微调 ---
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 5px;}
    .dataframe {font-family: 'Arial', sans-serif; font-size: 12px;}
    div[data-testid="stExpander"] details summary {font-weight: bold; color: #1f77b4;}
    .debug-log {background-color: #f1f1f1; padding: 10px; border-radius: 5px; font-family: monospace;}
</style>
""", unsafe_allow_html=True)

# ================= 侧边栏：工作流控制 =================
with st.sidebar:
    st.title("📚 DeepSpec 调试版")
    
    # 调试选项
    with st.expander("🔧 调试选项", expanded=False):
        debug_mode = st.checkbox("启用详细调试日志", value=True)
        if st.button("清空日志"):
            st.session_state.debug_logs = []
            st.rerun()
        
        # 显示当前状态
        st.write("当前状态:")
        st.json({
            "papers_data_count": len(st.session_state.papers_data),
            "current_file": st.session_state.current_file,
            "word_buffer": st.session_state.word_buffer is not None,
            "debug_logs_count": len(st.session_state.debug_logs)
        })
    
    st.divider()
    
    # 1. 批量上传
    uploaded_files = st.file_uploader("1. 批量上传 PDF", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            if f.name not in st.session_state.papers_data:
                st.session_state.papers_data[f.name] = {
                    "file_obj": f,
                    "status": "待分析",
                    "extracted_data": None,
                    "pdf_processor": PDFProcessor(),
                    "selected_image": None,
                    "error_log": []
                }
                add_debug_log(f"添加新文件: {f.name}")
    
    st.divider()
    
    # 2. AI 设置与提取
    role = st.selectbox("设定 AI 角色", ["水力压裂专家", "油藏数值模拟专家", "机器学习专家"])
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key: 
        os.environ["OPENAI_API_KEY"] = api_key
        add_debug_log("API Key 已设置")
    
    # 模拟数据选项
    use_mock_data = st.checkbox("使用模拟数据 (无需API Key)", value=True)
    
    pending_files = [name for name, info in st.session_state.papers_data.items() if info['status'] == "待分析"]
    if pending_files:
        st.info(f"队列待处理: {len(pending_files)} 篇")
        if st.button(f"🚀 批量 AI 提取", type="primary"):
            if not api_key and not use_mock_data:
                st.error("请先配置 API Key 或勾选使用模拟数据")
            else:
                progress_bar = st.progress(0)
                for idx, fname in enumerate(pending_files):
                    info = st.session_state.papers_data[fname]
                    add_debug_log(f"开始处理: {fname}")
                    
                    try:
                        # 预处理 PDF
                        add_debug_log(f"处理 PDF: {fname}")
                        success = info['pdf_processor'].process_pdf(info['file_obj'])
                        if not success:
                            raise Exception("PDF 处理失败")
                        
                        # 提取文本
                        text = ""
                        for page_num in range(1, min(4, info['pdf_processor'].get_page_count() + 1)):
                            page_text = info['pdf_processor'].extract_text_by_page(page_num)
                            if page_text:
                                text += page_text + "\n\n"
                        
                        add_debug_log(f"提取文本长度: {len(text)} 字符")
                        
                        # AI 提取
                        if use_mock_data:
                            # 使用模拟数据
                            extractor = StructuredExtractor()
                            data = extractor.get_mock_structured_data()
                            data['title'] = f"模拟数据 - {fname}"
                        else:
                            extractor = StructuredExtractor()
                            data = extractor.extract_structured_data(text, role=role)
                        
                        info['extracted_data'] = data
                        info['status'] = "已提取"
                        add_debug_log(f"成功提取数据: {fname}")
                        
                    except Exception as e:
                        error_msg = f"{fname} 提取失败: {str(e)}"
                        st.error(error_msg)
                        info['error_log'].append(error_msg)
                        add_debug_log(error_msg)
                        
                        # 添加详细的错误信息到日志
                        add_debug_log(f"详细错误: {traceback.format_exc()}")
                        
                        # 使用模拟数据作为后备
                        extractor = StructuredExtractor()
                        data = extractor.get_mock_structured_data()
                        data['title'] = f"后备数据 - {fname} (提取失败)"
                        info['extracted_data'] = data
                        info['status'] = "已提取(后备)"
                        add_debug_log(f"使用后备数据: {fname}")
                    
                    progress_bar.progress((idx + 1) / len(pending_files))
                
                st.success("提取完成！请在右侧逐一审核。")
                st.rerun()
    
    st.divider()

    # 3. 论文导航
    st.subheader("📑 论文列表")
    if st.session_state.papers_data:
        for fname, info in st.session_state.papers_data.items():
            icon = "✅" if info['status'] == "已审核" else ("🤖" if "已提取" in info['status'] else "⏳")
            status_color = "green" if info['status'] == "已审核' else ("orange" if "已提取" in info['status'] else "gray")
            with st.container():
                st.markdown(f"<span style='color:{status_color}'>{icon}</span> **{fname}** - {info['status']}", unsafe_allow_html=True)
                if st.button(f"编辑", key=f"nav_{fname}"):
                    st.session_state.current_file = fname
                if info['error_log']:
                    with st.expander(f"错误日志 ({len(info['error_log'])})"):
                        for error in info['error_log']:
                            st.error(error)
    else:
        st.info("暂无上传的文件")

# ================= 主工作区 =================

# 创建两个 Tab：一个是单篇编辑，一个是全局预览
tab_edit, tab_preview, tab_debug = st.tabs(["✏️ 单篇精修 (Editor)", "👀 报告预览 (Word Preview)", "🔍 调试日志"])

# --- Tab 1: 单篇精修 ---
with tab_edit:
    if st.session_state.current_file:
        fname = st.session_state.current_file
        info = st.session_state.papers_data[fname]
        
        st.caption(f"当前正在编辑: {fname} | 状态: {info['status']}")
        
        if "待分析" in info['status']:
            st.warning("⚠️ 此文件尚未进行 AI 提取，请先在左侧点击"批量 AI 提取"。")
        else:
            if info['extracted_data']:
                data = info['extracted_data']
                
                # 显示原始数据用于调试
                with st.expander("🔍 原始提取数据 (调试)", expanded=False):
                    st.json(data)
                
                # 双栏布局：左编辑，右图表
                col_form, col_media = st.columns([1.3, 1])
                
                with col_form:
                    st.subheader("1. 结构化数据校对")
                    with st.container(border=True):
                        new_title = st.text_input("论文标题 (Article)", data.get('title', ''))
                        new_purpose = st.text_area("研究目的 (Purpose)", data.get('purpose', ''), height=80)
                        
                        # 结论编辑
                        st.markdown("**核心结论 (Conclusions)**")
                        conclusions = data.get('conclusion', [])
                        if isinstance(conclusions, str): 
                            conclusions = [conclusions]
                        if not conclusions:
                            conclusions = [""]  # 确保至少有一个空结论
                        
                        new_conclusions = []
                        for i, c in enumerate(conclusions):
                            new_c = st.text_area(f"结论 {i+1}", c, key=f"c_{fname}_{i}", height=60)
                            new_conclusions.append(new_c)
                        
                        # 添加新结论按钮
                        if st.button(f"+ 添加结论", key=f"add_conclusion_{fname}"):
                            new_conclusions.append("")
                            st.rerun()
                        
                        new_params = st.text_area("关键参数 (Parameters)", data.get('params', ''), height=100)
                        
                        # 公式编辑
                        st.markdown("**控制方程 (Formulas)**")
                        formulas = data.get('formulas', [])
                        if isinstance(formulas, str): 
                            formulas = [formulas]
                        if not formulas:
                            formulas = [""]  # 确保至少有一个空公式
                        
                        new_formulas = []
                        for i, f in enumerate(formulas):
                            f_col1, f_col2 = st.columns([3, 1])
                            with f_col1:
                                new_f = st.text_input(f"LaTeX Code {i+1}", f, key=f"f_{fname}_{i}")
                            with f_col2:
                                try:
                                    if new_f.strip():
                                        st.latex(new_f)
                                except Exception as e:
                                    st.caption(f"渲染失败: {str(e)[:20]}...")
                            new_formulas.append(new_f)
                        
                        # 添加新公式按钮
                        if st.button(f"+ 添加公式", key=f"add_formula_{fname}"):
                            new_formulas.append("")
                            st.rerun()
                        
                        new_comments = st.text_area("专家批注 (Comments)", data.get('comments', ''))
                        new_why = st.text_input("标签 (Why)", data.get('why', ''))

                with col_media:
                    st.subheader("2. 图表证据链 (Evidence)")
                    
                    if not info['pdf_processor'].pages:
                        try:
                            success = info['pdf_processor'].process_pdf(info['file_obj'])
                            if not success:
                                st.error("PDF 处理失败")
                        except Exception as e:
                            st.error(f"PDF 处理出错: {str(e)}")
                    
                    total_pages = info['pdf_processor'].get_page_count()
                    if total_pages > 0:
                        page_num = st.number_input("选择 PDF 页码", 1, total_pages, 1, key=f"pg_{fname}")
                        
                        try:
                            page_img = ImageCropper.extract_pdf_page_as_image(info['pdf_processor'], page_num)
                            if page_img:
                                st.info("👇 在下方拖拽框选关键图表，然后点击"截取"")
                                cropped = ImageCropper.crop_image_with_streamlit(page_img, key_prefix=f"crop_{fname}")
                                
                                if st.button("📸 确认截取并使用", key=f"btn_crop_{fname}"):
                                    info['selected_image'] = cropped
                                    st.success("截图已缓存！")
                                
                                if info['selected_image']:
                                    st.image(info['selected_image'], caption="当前已绑定的图表", width=200)
                                else:
                                    st.warning("尚未绑定图表")
                            else:
                                st.error(f"无法提取第 {page_num} 页图像")
                        except Exception as e:
                            st.error(f"图像处理出错: {str(e)}")
                    else:
                        st.error("PDF 无可用页面")

                st.divider()
                if st.button("💾 保存并标记为[已审核]", type="primary", key=f"save_{fname}"):
                    try:
                        info['extracted_data'] = {
                            'title': new_title, 
                            'purpose': new_purpose,
                            'conclusion': new_conclusions, 
                            'params': new_params,
                            'formulas': new_formulas, 
                            'comments': new_comments, 
                            'why': new_why
                        }
                        info['status'] = "已审核"
                        st.session_state.word_buffer = None  # 数据变更，清除旧缓存
                        st.toast("保存成功！请继续下一篇或去预览页查看。")
                        add_debug_log(f"保存成功: {fname}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"保存失败: {str(e)}")
                        add_debug_log(f"保存失败: {fname} - {str(e)}")
            else:
                st.error("提取数据为空，无法编辑")
                add_debug_log(f"提取数据为空: {fname}")
    else:
        st.info("👈 请在左侧选择一篇论文进行编辑。")

# --- Tab 2: 报告预览 ---
with tab_preview:
    st.subheader("📄 最终报告预览 (Master Table View)")
    
    reviewed_papers = [p for p in st.session_state.papers_data.values() if p['status'] == "已审核"]
    
    if not reviewed_papers:
        st.warning("⚠️ 暂无已审核的论文。请在"单篇精修"页面完成审核并点击保存。")
    else:
        st.write(f"共 {len(reviewed_papers)} 篇论文准备生成。")
        
        # 1. 准备预览数据 (Pandas DataFrame)
        preview_list = []
        for p in reviewed_papers:
            if p['extracted_data']:
                d = p['extracted_data']
                # 格式化结论为字符串
                cons_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(d.get('conclusion', []))])
                # 格式化公式
                forms_str = "\n".join(d.get('formulas', []))
                
                preview_list.append({
                    "Article": d.get('title'),
                    "具体内容(1): 目的与结论": f"【目的】\n{d.get('purpose')}\n\n【结论】\n{cons_str}",
                    "具体内容(2): 参数/公式/图表": f"【参数】\n{d.get('params')}\n\n【公式】\n{forms_str}\n\n【图表】\n{'✅ 已包含图片' if p['selected_image'] else '❌ 无图片'}",
                    "Comments": d.get('comments'),
                    "Why": d.get('why')
                })
            else:
                add_debug_log("某篇论文的提取数据为空，无法预览")
        
        if preview_list:
            df_preview = pd.DataFrame(preview_list)
            st.dataframe(df_preview, use_container_width=True)
        else:
            st.error("没有可用于预览的数据")
        
        st.divider()
        
        # 2. 生成与下载区域
        col_gen, col_down = st.columns([1, 2])
        
        with col_gen:
            # 强制重新生成按钮
            if st.button("🔄 生成/更新 Word 文件"):
                try:
                    with st.spinner("正在排版 Word 文档 (包含高清图片与公式渲染)..."):
                        gen = WordReportGenerator()
                        for p in reviewed_papers:
                            img_stream = None
                            if p['selected_image']:
                                img_stream = BytesIO()
                                p['selected_image'].save(img_stream, format='PNG')
                                img_stream.seek(0)
                            try:
                                gen.add_paper_analysis(p['extracted_data'], img_stream)
                                add_debug_log(f"成功添加论文到Word: {p['extracted_data'].get('title', '未知')}")
                            except Exception as e:
                                add_debug_log(f"添加论文到Word失败: {str(e)}")
                        
                        st.session_state.word_buffer = gen.save_to_bytes()
                    st.success("生成完毕！")
                except Exception as e:
                    st.error(f"生成Word文档失败: {str(e)}")
                    add_debug_log(f"Word生成失败: {str(e)}\n{traceback.format_exc()}")
        
        with col_down:
            if st.session_state.word_buffer:
                st.download_button(
                    label="📥 下载最终 Word 报告 (.docx)",
                    data=st.session_state.word_buffer,
                    file_name="SPE_Literature_Review_Master.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary"
                )
            else:
                st.caption("点击左侧按钮生成后即可下载")

# --- Tab 3: 调试日志 ---
with tab_debug:
    st.subheader("🔍 调试日志")
    
    # 显示系统信息
    with st.expander("系统信息", expanded=False):
        st.write(f"Python 版本: {sys.version}")
        st.write(f"Streamlit 版本: {st.__version__}")
        st.write(f"工作目录: {os.getcwd()}")
        st.write(f"文件系统列表: {os.listdir('.')}")
        
        # 检查utils目录
        utils_dir = "utils"
        if os.path.exists(utils_dir):
            st.write(f"Utils 目录存在: {os.listdir(utils_dir)}")
        else:
            st.error(f"Utils 目录不存在: {utils_dir}")
    
    # 显示调试日志
    if st.session_state.debug_logs:
        st.write("### 调试日志")
        for log in st.session_state.debug_logs[-50:]:  # 只显示最近50条
            st.code(log, language="text")
    else:
        st.info("暂无调试日志")