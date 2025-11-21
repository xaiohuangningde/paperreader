#!/usr/bin/env python3
"""
依赖安装脚本
运行方式：python install_deps.py
"""

import subprocess
import sys
import importlib
import os

def install_package(package):
    """安装Python包"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_import(module_name, package_name=None):
    """检查模块是否可导入"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        if package_name:
            print(f"❌ {module_name} 导入失败，尝试安装 {package_name}...")
            return install_package(package_name)
        return False

def main():
    """主安装函数"""
    print("DeepSpec Pro 依赖安装与检查")
    print("=" * 50)
    
    # 必需的依赖列表
    dependencies = [
        ("streamlit", "streamlit"),
        ("pdfplumber", "pdfplumber"),
        ("pandas", "pandas"),
        ("openai", "openai==0.28.1"),
        ("dotenv", "python-dotenv"),
        ("PIL", "Pillow"),
        ("docx", "python-docx"),
        ("matplotlib", "matplotlib"),
        ("cv2", "opencv-python"),  # 图片处理可能需要
        ("fitz", "PyMuPDF"),  # PDF处理
        ("pdf2image", "pdf2image"),
        ("xlsxwriter", "xlsxwriter"),
        ("tabulate", "tabulate")
    ]
    
    # 可选的依赖
    optional = [
        ("streamlit_cropper", "streamlit-cropper")
    ]
    
    print("检查必需依赖...")
    all_installed = True
    
    for module, package in dependencies:
        if check_import(module, package):
            print(f"✅ {module}")
        else:
            print(f"❌ {module} 安装失败")
            all_installed = False
    
    print("\n检查可选依赖...")
    for module, package in optional:
        if check_import(module, package):
            print(f"✅ {module}")
        else:
            print(f"⚠️ {module} 安装失败（可选）")
    
    print("\n" + "=" * 50)
    
    # 检查utils目录
    if os.path.exists("utils"):
        print("✅ utils 目录存在")
        utils_files = os.listdir("utils")
        print(f"包含文件: {utils_files}")
    else:
        print("❌ utils 目录不存在")
        all_installed = False
    
    # 检查Poppler（pdf2image需要）
    try:
        subprocess.run(["pdftoppm", "--version"], capture_output=True, check=True)
        print("✅ Poppler 已安装")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ Poppler 未安装或不在PATH中，pdf2image可能无法工作")
        print("安装建议:")
        print("- Windows: 下载 Poppler for Windows 并添加到 PATH")
        print("- macOS: brew install poppler")
        print("- Linux: sudo apt-get install poppler-utils")
    
    print("\n" + "=" * 50)
    if all_installed:
        print("🎉 所有必需依赖已安装！")
        print("\n下一步:")
        print("1. 运行 python test_components.py 测试组件")
        print("2. 运行 streamlit run app.py 启动应用")
    else:
        print("❌ 部分依赖安装失败，请检查错误信息")
        print("\n建议:")
        print("1. 尝试手动安装失败的依赖: pip install <package>")
        print("2. 更新pip: python -m pip install --upgrade pip")
        print("3. 使用虚拟环境")

if __name__ == "__main__":
    main()