"""
简化版DeepSpec应用，用于快速测试核心功能
"""

import streamlit as st
import pandas as pd
from io import BytesIO
import os
import traceback
from PIL import Image
import sys

st.set_page_config(layout="wide", page_title="DeepSpec Simple", initial_sidebar_state="expanded")

# 标题
st.title("DeepSpec Pro - 简化版")
st.markdown("这是一个简化版本，用于测试核心功能和诊断问题。")

# 侧边栏
with st.sidebar:
    st.header("控制面板")
    
    # 模拟数据选项
    use_mock = st.checkbox("使用模拟数据", value=True, help="勾选此项绕过PDF处理和API调用")
    
    # 文件上传
    uploaded_file = st.file_uploader("上传PDF", type=["pdf"])
    
    if uploaded_file and not use_mock:
        st.success(f"已上传: {uploaded_file.name}")
        file_details = {
            "文件名": uploaded_file.name,
            "大小 (MB)": round(uploaded_file.size / (1024 * 1024), 2)
        }
        st.json(file_details)

# 主界面
if use_mock:
    st.header("🔧 使用模拟数据进行测试")
    
    # 模拟论文数据
    mock_data = {
        "title": "Achieving Uniform Proppant Distribution (SPE-223571)",
        "purpose": "采用CFD-EGM模型研究支撑剂在射孔簇中的分布，解决趾端分布不均问题",
        "conclusions": [
            "倒数第二簇支撑剂浓度最高",
            "增加注入速率能减少底部沉降",
            "射孔方向从90°调至70°能增加侧射孔收集量"
        ],
        "params": "• 网格类型: 四面体+六面体 (边界层加密)\n• 支撑剂: 40/70目\n• 排量: 70-120 bpm",
        "formulas": [
            "C_p = \\frac{Q_p}{Q_f + Q_p} \\times 100\\%",
            "\\frac{\\partial (\\phi \\rho)}{\\partial t} + \\nabla \\cdot (\\rho \\mathbf{v}) = q"
        ],
        "comments": "这篇论文的网格划分策略值得参考，特别是针对分支缝的加密处理。",
        "why": "CFD, Proppant Transport, Perforation Efficiency"
    }
    
    # 编辑界面
    st.subheader("📝 编辑数据")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 可编辑字段
        title = st.text_input("论文标题", value=mock_data["title"])
        purpose = st.text_area("研究目的", value=mock_data["purpose"], height=100)
        
        # 可编辑结论
        st.write("**核心结论**")
        conclusions = []
        for i, conclusion in enumerate(mock_data["conclusions"]):
            conclusions.append(st.text_area(f"结论 {i+1}", value=conclusion, height=60))
        
        # 添加新结论
        if st.button("添加结论"):
            conclusions.append("")
            st.rerun()
        
        params = st.text_area("详细参数", value=mock_data["params"], height=100)
        
        # 可编辑公式
        st.write("**核心公式**")
        formulas = []
        for i, formula in enumerate(mock_data["formulas"]):
            col_form, col_preview = st.columns([3, 1])
            with col_form:
                form_text = st.text_input(f"LaTeX {i+1}", value=formula)
                formulas.append(form_text)
            with col_preview:
                try:
                    st.latex(form_text)
                except:
                    st.caption("渲染失败")
        
        # 添加新公式
        if st.button("添加公式"):
            formulas.append("")
            st.rerun()
        
        comments = st.text_area("专家批注", value=mock_data["comments"])
        why = st.text_input("标签", value=mock_data["why"])
    
    with col2:
        st.subheader("📊 预览")
        
        # 显示数据预览
        preview_data = {
            "标题": title,
            "目的": purpose[:50] + "..." if len(purpose) > 50 else purpose,
            "结论数量": len(conclusions),
            "参数长度": len(params),
            "公式数量": len(formulas),
            "评论长度": len(comments)
        }
        st.json(preview_data)
        
        # 模拟图片上传
        st.subheader("📷 示例图片")
        st.image("https://via.placeholder.com/300x200?text=Sample+Figure", caption="占位图 (在完整版本中会显示PDF截图)")
        
        # 添加到报告按钮
        if st.button("➕ 添加到报告"):
            # 创建会话状态变量存储报告数据
            if 'report_data' not in st.session_state:
                st.session_state.report_data = []
            
            # 添加当前数据到报告
            st.session_state.report_data.append({
                "title": title,
                "purpose": purpose,
                "conclusions": conclusions,
                "params": params,
                "formulas": formulas,
                "comments": comments,
                "why": why
            })
            
            st.success(f"已添加！当前报告包含 {len(st.session_state.report_data)} 篇论文。")

# 显示已添加的论文
if 'report_data' in st.session_state and st.session_state.report_data:
    st.header("📋 已添加的论文")
    
    for i, paper in enumerate(st.session_state.report_data):
        with st.expander(f"{i+1}. {paper['title']}"):
            col_title, col_delete = st.columns([4, 1])
            with col_title:
                st.write(f"**目的**: {paper['purpose'][:100]}...")
                st.write(f"**评论**: {paper['comments'][:100]}...")
            with col_delete:
                if st.button("删除", key=f"del_{i}"):
                    st.session_state.report_data.pop(i)
                    st.rerun()
    
    # 生成简单预览表格
    st.subheader("📄 报告预览")
    preview_df = pd.DataFrame([
        {
            "Article": p['title'],
            "目的": p['purpose'][:50] + "...",
            "结论数量": len(p['conclusions']),
            "标签": p['why']
        }
        for p in st.session_state.report_data
    ])
    st.dataframe(preview_df, use_container_width=True)
    
    # 导出按钮
    st.subheader("📥 导出选项")
    
    col_csv, col_json = st.columns(2)
    
    with col_csv:
        csv_data = pd.DataFrame(st.session_state.report_data).to_csv(index=False)
        st.download_button(
            label="下载 CSV",
            data=csv_data,
            file_name="deep_spec_report.csv",
            mime="text/csv"
        )
    
    with col_json:
        json_data = str(st.session_state.report_data)
        st.download_button(
            label="下载 JSON",
            data=json_data,
            file_name="deep_spec_report.json",
            mime="application/json"
        )

# 技术信息
with st.expander("🔧 技术信息"):
    st.write(f"Python 版本: {sys.version}")
    st.write(f"当前工作目录: {os.getcwd()}")
    st.write("已安装的核心库:")
    
    libraries = ["streamlit", "pandas", "PIL"]
    for lib in libraries:
        try:
            __import__(lib)
            st.write(f"✅ {lib}")
        except ImportError:
            st.write(f"❌ {lib}")

# 使用说明
with st.expander("📖 使用说明"):
    st.markdown("""
    1. **使用模拟数据**: 勾选"使用模拟数据"复选框，绕过PDF处理和API调用
    2. **编辑内容**: 在左侧编辑框中修改内容
    3. **添加到报告**: 点击"添加到报告"按钮将论文添加到报告列表
    4. **管理报告**: 在下方查看、编辑或删除已添加的论文
    5. **导出数据**: 使用CSV或JSON格式导出报告数据
    
    **完整版本功能**:
    - 真实PDF处理和文本提取
    - AI自动内容提取（需要OpenAI API Key）
    - 图片裁剪和插入
    - Word文档生成
    
    要使用完整版本，请运行 `streamlit run app.py` 或 `streamlit run app_debug.py`
    """)