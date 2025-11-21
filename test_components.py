#!/usr/bin/env python3
"""
测试脚本：验证各个组件是否正常工作
运行方式：python test_components.py
"""

import os
import sys
import traceback
from io import BytesIO

def test_imports():
    """测试模块导入"""
    print("=" * 50)
    print("测试模块导入...")
    print("=" * 50)
    
    try:
        from utils.pdf_processor import PDFProcessor
        print("✅ PDFProcessor 导入成功")
    except Exception as e:
        print(f"❌ PDFProcessor 导入失败: {str(e)}")
        return False
    
    try:
        from utils.ai_extractor import AIExtractor
        print("✅ AIExtractor 导入成功")
    except Exception as e:
        print(f"❌ AIExtractor 导入失败: {str(e)}")
        return False
    
    try:
        from utils.structured_extractor import StructuredExtractor
        print("✅ StructuredExtractor 导入成功")
    except Exception as e:
        print(f"❌ StructuredExtractor 导入失败: {str(e)}")
        return False
    
    try:
        from utils.report_generator import WordReportGenerator
        print("✅ WordReportGenerator 导入成功")
    except Exception as e:
        print(f"❌ WordReportGenerator 导入失败: {str(e)}")
        return False
    
    try:
        from utils.image_cropper import ImageCropper
        print("✅ ImageCropper 导入成功")
    except Exception as e:
        print(f"❌ ImageCropper 导入失败: {str(e)}")
        return False
    
    return True

def test_structured_extractor():
    """测试结构化数据提取器"""
    print("\n" + "=" * 50)
    print("测试结构化数据提取器...")
    print("=" * 50)
    
    try:
        from utils.structured_extractor import StructuredExtractor
        
        extractor = StructuredExtractor()
        print("✅ StructuredExtractor 实例化成功")
        
        # 获取模拟数据
        mock_data = extractor.get_mock_structured_data()
        print(f"✅ 获取模拟数据成功，包含字段: {list(mock_data.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ StructuredExtractor 测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_word_report_generator():
    """测试Word报告生成器"""
    print("\n" + "=" * 50)
    print("测试Word报告生成器...")
    print("=" * 50)
    
    try:
        from utils.report_generator import WordReportGenerator
        
        # 创建Word生成器
        gen = WordReportGenerator()
        print("✅ WordReportGenerator 实例化成功")
        
        # 获取模拟数据
        from utils.structured_extractor import StructuredExtractor
        extractor = StructuredExtractor()
        mock_data = extractor.get_mock_structured_data()
        
        # 添加数据到报告
        gen.add_paper_analysis(mock_data)
        print("✅ 成功添加论文数据到报告")
        
        # 保存到字节流
        buffer = gen.save_to_bytes()
        print(f"✅ 成功生成Word文档，大小: {len(buffer.getvalue())} 字节")
        
        # 保存测试文件
        with open("test_report.docx", "wb") as f:
            f.write(buffer.getvalue())
        print("✅ 保存测试文件: test_report.docx")
        
        return True
    except Exception as e:
        print(f"❌ WordReportGenerator 测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_pdf_processor():
    """测试PDF处理器"""
    print("\n" + "=" * 50)
    print("测试PDF处理器...")
    print("=" * 50)
    
    try:
        from utils.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        print("✅ PDFProcessor 实例化成功")
        
        # 获取页数（应该为0，因为没有加载PDF）
        page_count = processor.get_page_count()
        print(f"✅ 获取页数: {page_count}")
        
        return True
    except Exception as e:
        print(f"❌ PDFProcessor 测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_image_cropper():
    """测试图片裁剪器"""
    print("\n" + "=" * 50)
    print("测试图片裁剪器...")
    print("=" * 50)
    
    try:
        from utils.image_cropper import ImageCropper
        from PIL import Image
        import numpy as np
        
        # 创建一个测试图片
        test_img = Image.new('RGB', (300, 200), color='blue')
        print("✅ 创建测试图片成功")
        
        # 测试转换方法
        test_dict = {'data': BytesIO()}
        test_img.save(test_dict['data'], format='PNG')
        test_dict['data'].seek(0)
        
        result = ImageCropper.convert_pdf_image_to_pil(test_dict)
        if result:
            print("✅ PDF图像转换为PIL成功")
        else:
            print("⚠️ PDF图像转换为PIL返回None（可能正常）")
        
        return True
    except Exception as e:
        print(f"❌ ImageCropper 测试失败: {str(e)}")
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("DeepSpec Pro 组件测试")
    print("=" * 50)
    
    # 测试模块导入
    if not test_imports():
        print("\n❌ 模块导入测试失败，请检查utils目录和依赖")
        return False
    
    # 测试各个组件
    results = []
    results.append(("StructuredExtractor", test_structured_extractor()))
    results.append(("WordReportGenerator", test_word_report_generator()))
    results.append(("PDFProcessor", test_pdf_processor()))
    results.append(("ImageCropper", test_image_cropper()))
    
    # 显示测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 所有测试通过！组件工作正常。")
        print("\n下一步：")
        print("1. 运行 streamlit run app.py 或 streamlit run app_debug.py")
        print("2. 上传PDF文件进行测试")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息并修复问题。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)