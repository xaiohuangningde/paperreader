# DeepSpec: SPE Paper Scrutinizer

## 介绍

DeepSpec是一款专为石油工程师和科研人员设计的SPE论文智能分析工具，旨在提高文献阅读效率并确保科研真实性。本工具结合了先进的AI技术与交互式验证系统，为用户提供论文内容的精准提取与原文溯源功能。

## 功能特点

- **智能内容提取**：使用AI模型自动提取论文关键结论、参数和公式
- **置信度系统**：通过红绿灯机制标识提取内容的可信度
- **原文溯源**：一键定位到原文位置，便于核实
- **公式渲染**：LaTeX公式渲染与源码复制
- **专家批注**：支持添加个人批注并导出到Excel
- **多模态分析**：支持文本与图像的综合分析

## 安装与运行

### 环境要求

- Python 3.8+
- 安装了Poppler（用于PDF图像处理）

### 安装步骤

1. 克隆仓库：
```bash
git clone [repository-url]
cd paperreader
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行应用：
```bash
streamlit run app.py
```

### 使用说明

1. 在侧边栏上传SPE论文PDF文件
2. 选择您的专家角色（水力压裂专家、油藏数值模拟专家或机器学习专家）
3. 输入OpenAI API密钥
4. 点击"开始深度提取"按钮
5. 查看右侧提取结果，点击条目可在PDF视图中定位
6. 添加专家批注
7. 导出提取结果到Excel

## 项目结构

```
paperreader/
├── app.py              # 主应用文件
├── requirements.txt    # 项目依赖
├── README.md           # 项目说明
├── utils/              # 工具模块
│   ├── __init__.py
│   ├── pdf_processor.py    # PDF处理模块
│   ├── ai_extractor.py     # AI提取模块
│   └── formatter.py        # 结果格式化模块
└── data/               # 数据目录
    └── exports/         # 导出结果存储
```

## 注意事项

- 请确保上传的PDF文件为SPE论文格式
- API密钥将安全存储在本地，不会上传到服务器
- 导出结果将保存在data/exports/目录下

## 开发者

DeepSpec由石油工程专家团队开发，旨在提高科研效率与准确性。