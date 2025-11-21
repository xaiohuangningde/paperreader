# 运行 DeepSpec: SPE Paper Scrutinizer

## 环境准备

1. 安装 Python 3.8 或更高版本
2. 安装 Poppler（用于PDF图像处理）
   - Windows: 下载 Poppler for Windows 并添加到 PATH
   - macOS: `brew install poppler`
   - Linux: `sudo apt-get install poppler-utils`

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行应用

```bash
streamlit run app.py
```

## 使用说明

1. 在侧边栏上传SPE论文PDF文件
2. 选择您的专家角色（水力压裂专家、油藏数值模拟专家或机器学习专家）
3. 输入OpenAI API密钥
4. 点击"开始深度提取"按钮
5. 查看右侧提取结果，点击条目可在PDF视图中定位
6. 添加专家批注
7. 导出提取结果到Excel

## 注意事项

- 请确保上传的PDF文件为SPE论文格式
- API密钥将安全存储在本地，不会上传到服务器
- 导出结果将保存在data/exports/目录下

## 故障排除

如果遇到PDF处理错误，请确保已安装Poppler并添加到系统PATH中。