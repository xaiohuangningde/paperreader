from io import BytesIO
import streamlit as st
from PIL import Image
import numpy as np
import cv2

class ImageCropper:
    """
    图片裁剪和选择工具类
    """
    
    @staticmethod
    def crop_image_with_streamlit(image, key_prefix="cropper"):
        """
        使用streamlit-cropper库裁剪图片
        
        Args:
            image: PIL Image对象
            key_prefix: 组件键前缀
            
        Returns:
            PIL Image对象或None
        """
        try:
            # 尝试导入streamlit_cropper
            from streamlit_cropper import st_cropper
            
            # 获取图片尺寸
            img_width, img_height = image.size
            
            # 设置裁剪框的默认参数
            box_color = '#0000FF'
            aspect_ratio = None
            
            # 显示裁剪器
            cropped_img = st_cropper(
                image=image,
                realtime_update=True,
                box_color=box_color,
                aspect_ratio=aspect_ratio,
                key=f"{key_prefix}_cropper"
            )
            
            return cropped_img
            
        except ImportError:
            # 如果没有安装streamlit-cropper，使用简单的裁剪方法
            st.warning("未安装streamlit-cropper库，使用简单裁剪方法。运行 `pip install streamlit-cropper` 以获得更好的体验。")
            return ImageCropper.simple_crop(image, key_prefix)
    
    @staticmethod
    def simple_crop(image, key_prefix="simple_crop"):
        """
        简单的图片裁剪方法，使用滑块控制
        
        Args:
            image: PIL Image对象
            key_prefix: 组件键前缀
            
        Returns:
            PIL Image对象或None
        """
        img_width, img_height = image.size
        
        # 创建裁剪区域控制
        st.write("### 裁剪控制")
        
        col1, col2 = st.columns(2)
        
        with col1:
            x1 = st.slider("左边界", 0, img_width, int(img_width * 0.1))
            y1 = st.slider("上边界", 0, img_height, int(img_height * 0.1))
            
        with col2:
            x2 = st.slider("右边界", 0, img_width, int(img_width * 0.9))
            y2 = st.slider("下边界", 0, img_height, int(img_height * 0.9))
        
        # 确保坐标有效
        x1, y1 = min(x1, x2), min(y1, y2)
        x2, y2 = max(x1, x2), max(y1, y2)
        
        # 裁剪图片
        if st.button("确认裁剪", key=f"{key_prefix}_confirm"):
            cropped_image = image.crop((x1, y1, x2, y2))
            return cropped_image
        
        return None
    
    @staticmethod
    def extract_pdf_page_as_image(pdf_processor, page_num):
        """
        从PDF处理器中提取指定页面为图像
        
        Args:
            pdf_processor: PDFProcessor实例
            page_num: 页面编号
            
        Returns:
            PIL Image对象或None
        """
        try:
            # 获取PDF页面图像
            page_image_data = pdf_processor.get_page_as_image(page_num)
            
            if page_image_data:
                # 将字节数据转换为PIL图像
                image = Image.open(BytesIO(page_image_data['data']))
                return image
                
            return None
        except Exception as e:
            st.error(f"提取PDF页面为图像失败: {str(e)}")
            return None
    
    @staticmethod
    def show_cropped_images(cropped_images, key_prefix="display"):
        """
        显示已裁剪的图片
        
        Args:
            cropped_images: PIL Image对象列表
            key_prefix: 组件键前缀
        """
        if not cropped_images:
            return
            
        st.write("### 已裁剪的图片")
        
        for i, img in enumerate(cropped_images):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.image(img, caption=f"图片 {i+1}", use_column_width=True)
                
            with col2:
                if st.button(f"删除", key=f"{key_prefix}_del_{i}"):
                    cropped_images.pop(i)
                    st.experimental_rerun()
                    
            with col3:
                if st.button(f"使用", key=f"{key_prefix}_use_{i}"):
                    st.session_state[f"{key_prefix}_selected_image"] = i
    
    @staticmethod
    def convert_pdf_image_to_pil(image_data):
        """
        将PDF图像数据转换为PIL Image对象
        
        Args:
            image_data: PDF图像数据字典
            
        Returns:
            PIL Image对象或None
        """
        try:
            if 'data' in image_data:
                return Image.open(BytesIO(image_data['data']))
            return None
        except Exception as e:
            print(f"转换PDF图像为PIL失败: {str(e)}")
            return None