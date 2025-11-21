import pdfplumber
try:
    import fitz  # PyMuPDF
except ImportError:
    import pymupdf as fitz
from PIL import Image
import io
import base64
import pytesseract
import pandas as pd
from pdf2image import convert_from_path
import tempfile
import os

class PDFProcessor:
    """
    PDF文件处理类，负责提取PDF文本、图像和元数据
    """
    
    def __init__(self):
        self.pages = []
        self.pdf_metadata = {}
        self.file_name = ""
        self.images = []
        
    def process_pdf(self, pdf_file):
        """
        处理上传的PDF文件，提取文本和图像
        
        Args:
            pdf_file: Streamlit上传的PDF文件对象
            
        Returns:
            bool: 处理是否成功
        """
        try:
            self.file_name = pdf_file.name
            
            # 使用pdfplumber提取文本
            with pdfplumber.open(pdf_file) as pdf:
                self.pages = pdf.pages
                self.pdf_metadata = pdf.metadata
                
                # 提取每页文本
                for i, page in enumerate(self.pages):
                    page_text = page.extract_text()
                    if not page_text:
                        page_text = "此页无文本内容"
            
            # 重置文件指针到开头
            pdf_file.seek(0)
            # 使用PyMuPDF提取图像
            pdf_bytes = pdf_file.read()
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            self.images = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    
                    if pix.n - pix.alpha < 4:  # GRAY或RGB
                        img_data = pix.tobytes("png")
                        self.images.append({
                            'page': page_num + 1,
                            'index': img_index,
                            'data': img_data,
                            'base64': base64.b64encode(img_data).decode()
                        })
                    pix = None
            
            return True
            
        except Exception as e:
            print(f"处理PDF时出错: {str(e)}")
            return False
    
    def extract_text_by_page(self, page_num):
        """
        提取指定页面的文本
        
        Args:
            page_num (int): 页面编号(从1开始)
            
        Returns:
            str: 页面文本内容
        """
        if not self.pages or page_num < 1 or page_num > len(self.pages):
            return "无效的页面编号"
        
        try:
            page = self.pages[page_num-1]
            return page.extract_text()
        except Exception as e:
            print(f"提取第{page_num}页文本时出错: {str(e)}")
            return f"提取第{page_num}页文本时出错: {str(e)}"
    
    def extract_tables(self, page_num):
        """
        提取指定页面的表格
        
        Args:
            page_num (int): 页面编号(从1开始)
            
        Returns:
            list: 页面中的表格列表
        """
        if not self.pages or page_num < 1 or page_num > len(self.pages):
            return []
        
        try:
            page = self.pages[page_num-1]
            tables = page.extract_tables()
            
            # 将表格转换为DataFrame列表
            table_dfs = []
            for table in tables:
                df = pd.DataFrame(table[1:], columns=table[0])
                table_dfs.append(df)
            
            return table_dfs
        except Exception as e:
            print(f"提取第{page_num}页表格时出错: {str(e)}")
            return []
    
    def get_page_image(self, page_num):
        """
        获取指定页面的图像
        
        Args:
            page_num (int): 页面编号(从1开始)
            
        Returns:
            list: 页面中的图像列表
        """
        try:
            if not self.images:
                return []
            return [img for img in self.images if img['page'] == page_num]
        except Exception as e:
            print(f"获取页面 {page_num} 图像时出错: {str(e)}")
            return []
    
    def get_page_as_image(self, page_num):
        """
        获取整个页面作为图像
        
        Args:
            page_num (int): 页面编号(从1开始)
            
        Returns:
            bytes: 图像的bytes数据，失败返回None
        """
        try:
            if not self.pages or page_num < 1 or page_num > len(self.pages):
                return None
                
            page = self.pages[page_num-1]
            # 使用pdfplumber的to_image方法
            if hasattr(page, 'to_image'):
                img = page.to_image()
                # 将图像转换为bytes
                img_bytes = img.save(format="PNG", return_bytes=True)
                # 转换为base64
                base64_str = base64.b64encode(img_bytes).decode()
                return {
                    'page': page_num,
                    'data': img_bytes,
                    'base64': base64_str
                }
            return None
        except Exception as e:
            print(f"获取页面 {page_num} 为图像时出错: {str(e)}")
            return None
    
    def search_text(self, query, page_range=None):
        """
        在PDF中搜索文本
        
        Args:
            query (str): 要搜索的文本
            page_range (tuple): 页面范围，例如(1, 5)表示搜索第1到5页
            
        Returns:
            list: 包含匹配结果的列表，每个元素包含页码和匹配文本
        """
        results = []
        
        start_page = page_range[0] if page_range else 1
        end_page = page_range[1] if page_range else len(self.pages)
        
        for page_num in range(start_page, min(end_page, len(self.pages)) + 1):
            page_text = self.extract_text_by_page(page_num)
            
            if query.lower() in page_text.lower():
                # 提取包含查询词的上下文
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        # 获取前后几行作为上下文
                        context_start = max(0, i - 2)
                        context_end = min(len(lines), i + 3)
                        context = '\n'.join(lines[context_start:context_end])
                        
                        results.append({
                            'page': page_num,
                            'line': i + 1,
                            'text': line.strip(),
                            'context': context
                        })
        
        return results
    
    def extract_metadata(self):
        """
        提取PDF元数据
        
        Returns:
            dict: 包含PDF元数据的字典
        """
        return self.pdf_metadata or {}
    
    def get_page_count(self):
        """
        获取PDF总页数
        
        Returns:
            int: PDF总页数
        """
        return len(self.pages)
    
    def save_page_as_image(self, page_num, pdf_file_path=None, output_path=None):
        """
        将指定页面保存为图像
        
        Args:
            page_num (int): 页面编号(从1开始)
            pdf_file_path (str): 原始PDF文件路径
            output_path (str): 输出路径，如果为None则使用临时路径
            
        Returns:
            str: 保存的图像路径
        """
        if not self.pages or page_num < 1 or page_num > len(self.pages):
            return None
        
        try:
            if not pdf_file_path:
                return None
                
            if not output_path:
                output_path = f"{tempfile.gettempdir()}/page_{page_num}.png"
            
            # 将页面转换为图像
            images = convert_from_path(pdf_file_path, first_page=page_num, last_page=page_num)
            
            if images:
                images[0].save(output_path)
                return output_path
                
            return None
        except Exception as e:
            print(f"保存第{page_num}页为图像时出错: {str(e)}")
            return None