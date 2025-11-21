# DeepSpec Pro 调试指南

## 问题诊断步骤

### 1. 环境检查

首先运行依赖安装脚本：
```bash
python install_deps.py
```

然后运行组件测试：
```bash
python test_components.py
```

如果这两个脚本都成功通过，环境基本正常。

### 2. 启动调试版本

使用调试版本启动应用：
```bash
streamlit run app_debug.py
```

调试版本包含详细的错误信息和日志记录。

### 3. 常见问题排查

#### 问题1：模块导入失败

**错误信息**：
```
❌ 核心模块导入失败: No module named 'utils.pdf_processor'
```

**解决方案**：
1. 确保在项目根目录运行
2. 检查utils目录是否存在
3. 检查utils目录中是否有__init__.py文件

#### 问题2：PDF处理失败

**错误信息**：
```
PDF 处理失败: 无法读取PDF文件
```

**解决方案**：
1. 确保PDF文件没有密码保护
2. 尝试使用其他PDF文件测试
3. 检查Poppler是否已安装（pdf2image需要）

#### 问题3：没有提取内容

**现象**：
- 上传PDF后，提取的内容为空
- 所有字段显示"N/A"或为空

**解决方案**：
1. 勾选"使用模拟数据"选项进行测试
2. 检查PDF是否包含可提取的文本
3. 尝试只提取前3页内容

#### 问题4：图片裁剪失败

**错误信息**：
```
无法提取第 X 页图像
```

**解决方案**：
1. 安装streamlit-cropper库：`pip install streamlit-cropper`
2. 检查PyMuPDF是否正确安装
3. 尝试不同的PDF文件

#### 问题5：Word文档生成失败

**错误信息**：
```
生成Word文档失败: PermissionError
```

**解决方案**：
1. 关闭已打开的Word文档
2. 检查写入权限
3. 尝试生成到不同目录

### 4. 高级调试

#### 查看详细日志

在调试版本中，所有操作都会记录到"调试日志"标签页。查看这些日志可以定位具体问题。

#### 检查数据流

在"单篇精修"页面，展开"原始提取数据(调试)"部分，查看AI提取的原始数据。

#### 使用模拟数据

如果真实数据处理有问题，勾选"使用模拟数据"选项进行测试。

### 5. 环境变量设置

如果使用真实API，确保设置了正确的环境变量：
```bash
# 在命令行中临时设置
export OPENAI_API_KEY="your-api-key"

# 或者创建.env文件
echo "OPENAI_API_KEY=your-api-key" > .env
```

### 6. 最小复现测试

如果问题持续存在，尝试最小复现：

1. 使用简单的PDF文件测试
2. 只使用核心功能
3. 逐步添加复杂功能

### 7. 获取帮助

如果问题仍未解决：

1. 收集错误信息和日志
2. 描述操作步骤
3. 提供PDF文件样本（如可能）

## 快速修复命令

```bash
# 重新安装所有依赖
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# 检查Python版本
python --version

# 检查Streamlit版本
streamlit --version

# 清理Streamlit缓存
streamlit cache clear
```

## 性能优化建议

1. **大型PDF处理**：限制只处理前3-5页
2. **内存问题**：重启应用清理内存
3. **并发问题**：避免同时处理多个PDF
4. **网络问题**：使用模拟数据绕过API调用