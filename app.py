import streamlit as st
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
from PIL import Image

# 引入工具模块
try:
    from utils.pdf_processor import PDFProcessor
    from utils.ai_extractor import AIExtractor
    from utils.structured_extractor import StructuredExtractor
    from utils.report_generator import WordReportGenerator
    from utils.image_cropper import ImageCropper
except ImportError:
    st.error("❌ 核心模块导入失败，请确保 utils 文件夹及依赖库完整。")
    st.stop()

load_dotenv()

st.set_page_config(layout="wide", page_title="DeepSpec V3.1", initial_sidebar_state="expanded")

# --- 全局状态初始化 ---
if 'papers_data' not in st.session_state:
    st.session_state.papers_data = {}
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
if 'word_buffer' not in st.session_state:
    st.session_state.word_buffer = None  # 用于缓存生成的 Word 文件

# --- CSS 样式微调 ---
st.markdown("""
<style>
    .stButton>button {width: 100%; border-radius: 5px;}
    /* 调整表格字体，使其更像 Word 预览 */
    .dataframe {font-family: 'Arial', sans-serif; font-size: 12px;}
    div[data-testid="stExpander"] details summary {font-weight: bold; color: #1f77b4;}
</style>
""", unsafe_allow_html=True)

# ================= 侧边栏：工作流控制 =================
with st.sidebar:
    st.title("📚 DeepSpec 工作台")
    
    # 1. 批量上传
    uploaded_files = st.file_uploader("1. 批量上传 PDF", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        for f in uploaded_files:
            if f.name not in st.session_state.papers_data:
                st.session_state.papers_data[f.name] = {
                    "file_obj": f,
                    "status": "待分析",  # 待分析 -> 已提取 -> 已审核
                    "extracted_data": None,
                    "pdf_processor": PDFProcessor(),
                    "selected_image": None
                }
    
    st.divider()
    
    # 2. AI 设置与提取
    role = st.selectbox("设定 AI 角色", ["水力压裂专家", "油藏数值模拟专家", "机器学习专家"])
    api_key = st.text_input("OpenAI API Key", type="password")
    if api_key: os.environ["OPENAI_API_KEY"] = api_key
    
    pending_files = [name for name, info in st.session_state.papers_data.items() if info['status'] == "待分析"]
    if pending_files:
        st.info(f"队列待处理: {len(pending_files)} 篇")
        if st.button(f"🚀 批量 AI 提取", type="primary"):
            if not api_key:
                st.error("请先配置 API Key")
            else:
                progress_bar = st.progress(0)
                for idx, fname in enumerate(pending_files):
                    info = st.session_state.papers_data[fname]
                    # 预处理 PDF
                    info['pdf_processor'].process_pdf(info['file_obj'])
                    text = info['pdf_processor'].extract_text_by_page(1) + \
                           info['pdf_processor'].extract_text_by_page(2) + \
                           info['pdf_processor'].extract_text_by_page(3)
                    # AI 提取
                    try:
                        extractor = StructuredExtractor()
                        data = extractor.extract_structured_data(text, role=role)
                        info['extracted_data'] = data
                        info['status'] = "已提取"
                    except Exception as e:
                        st.error(f"{fname} 提取失败: {e}")
                    progress_bar.progress((idx + 1) / len(pending_files))
                st.success("提取完成！请在右侧逐一审核。")
                st.rerun()  # 【修复点】从 st.experimental_rerun() 改为 st.rerun()
    
    st.divider()

    # 3. 论文导航
    st.subheader("📑 论文列表")
    sorted_files = sorted(st.session_state.papers_data.items(), key=lambda x: x[1]['status'] == "已审核", reverse=True)
    for fname, info in sorted_files:
        icon = "✅" if info['status'] == "已审核" else ("🤖" if info['status'] == "已提取" else "⏳")
        if st.button(f"{icon} {fname}", key=f"nav_{fname}"):
            st.session_state.current_file = fname

# ================= 主工作区 =================

# 创建两个 Tab：一个是单篇编辑，一个是全局预览
tab_edit, tab_preview = st.tabs(["✏️ 单篇精修 (Editor)", "👀 报告预览 (Word Preview)"])

# --- Tab 1: 单篇精修 ---
with tab_edit:
    if st.session_state.current_file:
        fname = st.session_state.current_file
        info = st.session_state.papers_data[fname]
        
        st.caption(f"当前正在编辑: {fname} | 状态: {info['status']}")
        
        if info['status'] == "待分析":
            st.warning("⚠️ 此文件尚未进行 AI 提取，请先在左侧点击“批量 AI 提取”。")
        else:
            data = info['extracted_data']
            
            # 双栏布局：左编辑，右图表
            col_form, col_media = st.columns([1.3, 1])
            
            with col_form:
                st.subheader("1. 结构化数据校对")
                # 【恢复点】因为您已升级到新版 Streamlit，border=True 可以使用了
                with st.container(border=True):
                    new_title = st.text_input("论文标题 (Article)", data.get('title', ''))
                    new_purpose = st.text_area("研究目的 (Purpose)", data.get('purpose', ''), height=80)
                    
                    # 结论编辑
                    st.markdown("**核心结论 (Conclusions)**")
                    conclusions = data.get('conclusion', [])
                    if isinstance(conclusions, str): conclusions = [conclusions]
                    new_conclusions = []
                    for i, c in enumerate(conclusions):
                        new_c = st.text_area(f"结论 {i+1}", c, key=f"c_{fname}_{i}", height=60)
                        new_conclusions.append(new_c)
                    
                    new_params = st.text_area("关键参数 (Parameters)", data.get('params', ''), height=100)
                    
                    # 公式编辑
                    st.markdown("**控制方程 (Formulas)**")
                    formulas = data.get('formulas', [])
                    if isinstance(formulas, str): formulas = [formulas]
                    new_formulas = []
                    for i, f in enumerate(formulas):
                        f_col1, f_col2 = st.columns([3, 1])
                        with f_col1:
                            new_f = st.text_input(f"LaTeX Code {i+1}", f, key=f"f_{fname}_{i}")
                        with f_col2:
                            try: st.latex(new_f)
                            except: st.caption("渲染失败")
                        new_formulas.append(new_f)

                    new_comments = st.text_area("专家批注 (Comments)", data.get('comments', ''))
                    new_why = st.text_input("标签 (Why)", data.get('why', ''))

            with col_media:
                st.subheader("2. 图表证据链 (Evidence)")
                if not info['pdf_processor'].pages:
                    info['pdf_processor'].process_pdf(info['file_obj'])
                
                total_pages = info['pdf_processor'].get_page_count()
                page_num = st.number_input("选择 PDF 页码", 1, total_pages, 1, key=f"pg_{fname}")
                
                page_img = ImageCropper.extract_pdf_page_as_image(info['pdf_processor'], page_num)
                if page_img:
                    st.info("👇 在下方拖拽框选关键图表，然后点击“截取”")
                    cropped = ImageCropper.crop_image_with_streamlit(page_img, key_prefix=f"crop_{fname}")
                    
                    if st.button("📸 确认截取并使用", key=f"btn_crop_{fname}"):
                        info['selected_image'] = cropped
                        st.success("截图已缓存！")
                    
                    if info['selected_image']:
                        st.image(info['selected_image'], caption="当前已绑定的图表", width=200)
                    else:
                        st.warning("尚未绑定图表")

            st.divider()
            if st.button("💾 保存并标记为[已审核]", type="primary", key=f"save_{fname}"):
                info['extracted_data'] = {
                    'title': new_title, 'purpose': new_purpose,
                    'conclusion': new_conclusions, 'params': new_params,
                    'formulas': new_formulas, 'comments': new_comments, 'why': new_why
                }
                info['status'] = "已审核"
                st.session_state.word_buffer = None # 数据变更，清除旧缓存
                st.toast("保存成功！请继续下一篇或去预览页查看。")
                st.rerun() # 【修复点】从 st.experimental_rerun() 改为 st.rerun()
    else:
        st.info("👈 请在左侧选择一篇论文进行编辑。")

# --- Tab 2: 报告预览 (Word View) ---
with tab_preview:
    st.subheader("📄 最终报告预览 (Master Table View)")
    
    reviewed_papers = [p for p in st.session_state.papers_data.values() if p['status'] == "已审核"]
    
    if not reviewed_papers:
        st.warning("⚠️ 暂无已审核的论文。请在“单篇精修”页面完成审核并点击保存。")
    else:
        st.write(f"共 {len(reviewed_papers)} 篇论文准备生成。")
        
        # 1. 准备预览数据 (Pandas DataFrame)
        preview_list = []
        for p in reviewed_papers:
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
        
        df_preview = pd.DataFrame(preview_list)
        st.table(df_preview) # 展示静态表格，模拟 Word 效果

        st.divider()
        
        # 2. 生成与下载区域
        col_gen, col_down = st.columns([1, 2])
        
        with col_gen:
            # 强制重新生成按钮
            if st.button("🔄 生成/更新 Word 文件"):
                with st.spinner("正在排版 Word 文档 (包含高清图片与公式渲染)..."):
                    gen = WordReportGenerator()
                    for p in reviewed_papers:
                        img_stream = None
                        if p['selected_image']:
                            img_stream = BytesIO()
                            p['selected_image'].save(img_stream, format='PNG')
                            img_stream.seek(0)
                        gen.add_paper_row(p['extracted_data'], img_stream)
                    
                    st.session_state.word_buffer = gen.save_to_bytes()
                st.success("生成完毕！")
        
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