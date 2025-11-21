from typing import Dict, List, Any
import re
import json
from .ai_extractor import AIExtractor

class StructuredExtractor:
    """
    结构化数据提取器，专门用于提取格式化数据以生成Word报告
    """
    
    def __init__(self):
        self.ai_extractor = AIExtractor()
        
    def extract_structured_data(self, text: str, role: str = "水力压裂专家", 
                               extraction_mode: str = "标准提取") -> Dict[str, Any]:
        """
        提取结构化数据，返回适合Word报告格式的字典
        
        Args:
            text: 论文文本
            role: 专家角色
            extraction_mode: 提取模式
            
        Returns:
            Dict: 结构化数据
        """
        # 使用AI提取器获取基础数据
        basic_extraction = self.ai_extractor.extract_from_text(text, role, extraction_mode)
        
        # 将基础数据转换为结构化格式
        structured_data = self._convert_to_structured_format(basic_extraction)
        
        return structured_data
    
    def _convert_to_structured_format(self, basic_extraction: Dict[str, Any]) -> Dict[str, Any]:
        """
        将基础提取结果转换为Word报告所需的结构化格式
        
        Args:
            basic_extraction: AI提取器的基础结果
            
        Returns:
            Dict: 结构化数据
        """
        structured_data = {
            "title": "",
            "purpose": "",
            "conclusion": [],
            "params": "",
            "formulas": [],
            "comments": "",
            "why": "",
            "page_source": ""
        }
        
        # 提取论文标题
        if "metadata" in basic_extraction:
            structured_data["title"] = self._extract_title(basic_extraction)
        
        # 提取研究目的
        structured_data["purpose"] = self._extract_purpose(basic_extraction)
        
        # 提取核心结论
        structured_data["conclusion"] = self._extract_conclusions(basic_extraction)
        
        # 提取参数
        structured_data["params"] = self._extract_parameters(basic_extraction)
        
        # 提取公式
        structured_data["formulas"] = self._extract_formulas(basic_extraction)
        
        # 提取页码来源
        structured_data["page_source"] = self._extract_page_source(basic_extraction)
        
        return structured_data
    
    def _extract_title(self, extraction_result: Dict[str, Any]) -> str:
        """
        从提取结果中提取论文标题
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            str: 论文标题
        """
        # 尝试从摘要或结论中提取标题
        if "summary" in extraction_result and extraction_result["summary"]:
            for item in extraction_result["summary"]:
                if "title" in item.get("explanation", "").lower():
                    return item.get("content", "")
        
        # 如果没有找到标题，使用默认值
        return "未知标题"
    
    def _extract_purpose(self, extraction_result: Dict[str, Any]) -> str:
        """
        从提取结果中提取研究目的
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            str: 研究目的
        """
        # 从摘要中提取目的相关内容
        if "summary" in extraction_result and extraction_result["summary"]:
            purpose_items = []
            
            for item in extraction_result["summary"]:
                content = item.get("content", "")
                if any(keyword in content.lower() for keyword in ["目的", "目标", "aim", "objective", "purpose"]):
                    purpose_items.append(content)
            
            if purpose_items:
                return " ".join(purpose_items)
        
        # 如果没有找到目的，返回默认值
        return "提取研究目的失败，请手动补充。"
    
    def _extract_conclusions(self, extraction_result: Dict[str, Any]) -> List[str]:
        """
        从提取结果中提取核心结论
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            List[str]: 核心结论列表
        """
        conclusions = []
        
        if "summary" in extraction_result and extraction_result["summary"]:
            for item in extraction_result["summary"]:
                content = item.get("content", "")
                # 排除已经用于目的的项
                if not any(keyword in content.lower() for keyword in ["目的", "目标", "aim", "objective", "purpose"]):
                    conclusions.append(content)
        
        return conclusions
    
    def _extract_parameters(self, extraction_result: Dict[str, Any]) -> str:
        """
        从提取结果中提取参数
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            str: 格式化的参数字符串
        """
        params_list = []
        
        if "parameters" in extraction_result and extraction_result["parameters"]:
            for item in extraction_result["parameters"]:
                content = item.get("content", "")
                # 尝试格式化参数
                param = self._format_parameter(content)
                params_list.append(param)
        
        return "\n".join(params_list)
    
    def _format_parameter(self, param_content: str) -> str:
        """
        格式化参数内容
        
        Args:
            param_content: 参数原始内容
            
        Returns:
            str: 格式化的参数
        """
        # 尝试提取参数名称、值和单位
        # 使用正则表达式匹配常见参数格式
        
        # 模式1: 参数名: 值 单位
        match1 = re.match(r"(.+?):\s*([\d.]+)\s*([a-zA-Z/%]+)", param_content)
        if match1:
            name, value, unit = match1.groups()
            return f"• {name}: {value} {unit}"
        
        # 模式2: 参数名 = 值 单位
        match2 = re.match(r"(.+?)\s*=\s*([\d.]+)\s*([a-zA-Z/%]+)", param_content)
        if match2:
            name, value, unit = match2.groups()
            return f"• {name}: {value} {unit}"
        
        # 模式3: 仅包含数值和单位
        match3 = re.match(r"([\d.]+)\s*([a-zA-Z/%]+)", param_content)
        if match3:
            value, unit = match3.groups()
            return f"• 参数值: {value} {unit}"
        
        # 如果都不匹配，直接返回原内容
        return f"• {param_content}"
    
    def _extract_formulas(self, extraction_result: Dict[str, Any]) -> List[str]:
        """
        从提取结果中提取公式
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            List[str]: 公式列表
        """
        formulas = []
        
        if "equations" in extraction_result and extraction_result["equations"]:
            for item in extraction_result["equations"]:
                content = item.get("content", "")
                # 尝试提取LaTeX公式
                latex_match = re.search(r"\$\$([^$]+)\$\$", content)
                if latex_match:
                    formulas.append(latex_match.group(1))
                else:
                    # 如果没有LaTeX格式，使用整个内容
                    formulas.append(content)
        
        return formulas
    
    def _extract_page_source(self, extraction_result: Dict[str, Any]) -> str:
        """
        从提取结果中提取页码来源
        
        Args:
            extraction_result: 提取结果
            
        Returns:
            str: 页码来源
        """
        # 尝试从摘要中提取页码
        if "summary" in extraction_result and extraction_result["summary"]:
            pages = set()
            for item in extraction_result["summary"]:
                if "source_page" in item:
                    pages.add(str(item["source_page"]))
            
            if pages:
                return ", ".join(sorted(pages))
        
        return "未知"
    
    def get_mock_structured_data(self) -> Dict[str, Any]:
        """
        获取模拟的结构化数据，用于测试
        
        Returns:
            Dict: 模拟结构化数据
        """
        return {
            "title": "Achieving Uniform Proppant Distribution in Multi-Cluster Perforations (SPE-223571)",
            "purpose": "采用CFD-EGM模型研究支撑剂在射孔簇中的分布，解决趾端分布不均问题",
            "conclusion": [
                "倒数第二簇支撑剂浓度最高",
                "增加注入速率能减少底部沉降",
                "射孔方向从90°调至70°能增加侧射孔收集量"
            ],
            "params": "• 网格类型: 四面体+六面体 (边界层加密)\n• 支撑剂: 40/70目\n• 排量: 70-120 bpm\n• 粘度: 10-50 cp\n• 砂比: 0.5-2.0 ppg",
            "formulas": [
                "C_p = \\frac{Q_p}{Q_f + Q_p} \\times 100\\%",
                "\\frac{\\partial (\\phi \\rho)}{\\partial t} + \\nabla \\cdot (\\rho \\mathbf{v}) = q"
            ],
            "comments": "这篇论文的网格划分策略值得参考，特别是针对分支缝的加密处理。",
            "why": "CFD, Proppant Transport, Perforation Efficiency",
            "page_source": "4, 6, 8"
        }