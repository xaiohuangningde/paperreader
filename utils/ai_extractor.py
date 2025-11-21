import openai
import json
import re
from typing import Dict, List, Any
import time

class AIExtractor:
    """
    AI提取器类，负责使用OpenAI API提取论文的关键信息
    """
    
    def __init__(self):
        self.model = "gpt-4o"  # 默认模型
        self.temperature = 0.1  # 较低的温度确保输出更稳定
        self.max_tokens = 4000
        
        # 预定义的专家角色提示词
        self.role_prompts = {
            "水力压裂专家": "你是一位水力压裂领域的顶级专家，擅长分析水力压裂技术的各个方面，包括压裂液、支撑剂、裂缝导流能力等。请从论文中提取与水力压裂相关的关键技术参数、实验结果和结论。",
            
            "油藏数值模拟专家": "你是一位油藏数值模拟领域的资深专家，精通各种油藏模拟软件和数学模型。请从论文中提取数值模拟相关的模型参数、网格设置、边界条件、历史匹配结果和预测分析。",
            
            "机器学习专家": "你是一位石油工程领域的机器学习专家，擅长应用各种机器学习和人工智能技术解决石油工程问题。请从论文中提取机器学习模型架构、训练数据、特征工程、模型性能和应用效果。",
            
            "通用研究员": "你是一位经验丰富的石油工程研究员，能够全面理解各种类型的SPE论文。请从论文中提取研究背景、方法、关键参数、主要结论和实际应用价值。"
        }
        
        # 提取模式配置
        self.extraction_modes = {
            "快速提取": {
                "detail_level": "基础",
                "focus_areas": ["摘要", "结论", "关键参数"],
                "max_examples": 1
            },
            "标准提取": {
                "detail_level": "标准",
                "focus_areas": ["摘要", "方法", "结果", "结论", "关键参数", "图表"],
                "max_examples": 2
            },
            "深度提取": {
                "detail_level": "详细",
                "focus_areas": ["全文内容", "引言", "方法", "结果", "讨论", "结论", "附录", "参考文献"],
                "max_examples": 3
            }
        }
    
    def set_api_key(self, api_key):
        """设置OpenAI API密钥"""
        openai.api_key = api_key
    
    def set_model(self, model):
        """设置使用的模型"""
        self.model = model
    
    def extract_from_text(self, text: str, role: str = "通用研究员", 
                         extraction_mode: str = "标准提取", 
                         custom_prompt: str = None) -> Dict[str, Any]:
        """
        从论文文本中提取关键信息
        
        Args:
            text (str): 论文文本内容
            role (str): 专家角色
            extraction_mode (str): 提取模式
            custom_prompt (str): 自定义提示词
            
        Returns:
            Dict[str, Any]: 提取的结果
        """
        # 构建提示词
        system_prompt = self._build_system_prompt(role, extraction_mode, custom_prompt)
        
        # 分割文本以处理长文档
        text_chunks = self._split_text(text)
        
        # 提取每个部分
        summary = self._extract_summary(text_chunks, system_prompt)
        parameters = self._extract_parameters(text_chunks, system_prompt)
        equations = self._extract_equations(text_chunks, system_prompt)
        figures = self._extract_figures(text_chunks, system_prompt)
        
        # 整合结果
        result = {
            "summary": summary,
            "parameters": parameters,
            "equations": equations,
            "figures": figures,
            "metadata": {
                "role": role,
                "extraction_mode": extraction_mode,
                "model": self.model
            }
        }
        
        return result
    
    def _build_system_prompt(self, role: str, extraction_mode: str, custom_prompt: str = None) -> str:
        """构建系统提示词"""
        base_prompt = """
        你是一个专业的石油工程文献分析助手，任务是从SPE论文中提取关键信息并按照指定格式返回。
        
        请按照以下JSON格式返回结果:
        {
            "items": [
                {
                    "content": "提取的内容",
                    "source_page": 页码数字,
                    "confidence": "High/Medium/Low/Missing",
                    "explanation": "解释或上下文"
                }
            ]
        }
        
        置信度标准:
        - High: 原文明确提及，可以直接引用
        - Medium: 原文间接提及或需要简单推断
        - Low: 原文提及模糊或需要较多推断
        - Missing: 原文未提及或无法找到
        
        请确保返回有效的JSON格式，不要包含任何其他文本或解释。
        """
        
        role_prompt = self.role_prompts.get(role, self.role_prompts["通用研究员"])
        mode_config = self.extraction_modes.get(extraction_mode, self.extraction_modes["标准提取"])
        
        system_prompt = f"{base_prompt}\n\n角色设定: {role_prompt}\n\n提取细节: {mode_config['detail_level']}"
        
        if custom_prompt:
            system_prompt += f"\n\n特殊要求: {custom_prompt}"
            
        return system_prompt
    
    def _split_text(self, text: str, chunk_size: int = 8000) -> List[str]:
        """将长文本分割成较小的块"""
        if len(text) <= chunk_size:
            return [text]
            
        chunks = []
        current_chunk = ""
        
        # 按段落分割
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if len(current_chunk) + len(para) < chunk_size:
                current_chunk += para + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _call_openai_api(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """调用OpenAI API并返回解析后的JSON结果"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            result_text = response.choices[0].message['content']
            
            # 尝试解析JSON
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # 尝试提取JSON部分
                json_match = re.search(r'```json(.*?)```', result_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))
                
                # 如果仍无法解析，返回错误信息
                return {
                    "error": "无法解析API响应",
                    "raw_response": result_text
                }
                
        except Exception as e:
            return {
                "error": f"API调用失败: {str(e)}",
                "items": []
            }
    
    def _extract_summary(self, text_chunks: List[str], system_prompt: str) -> List[Dict[str, Any]]:
        """提取论文核心结论"""
        prompt = """
        请从以下论文文本中提取核心结论和发现。
        
        对于每个结论，请提供:
        1. 结论的具体内容
        2. 该结论所在的页码（如果文本中没有页码信息，请估算）
        3. 置信度评估
        
        文本内容:
        {text}
        
        请按照指定的JSON格式返回结果。
        """
        
        all_items = []
        for chunk in text_chunks:
            chunk_prompt = prompt.format(text=chunk)
            result = self._call_openai_api(chunk_prompt, system_prompt)
            
            if "items" in result:
                all_items.extend(result["items"])
            
            # 添加延迟以避免API限制
            time.sleep(1)
        
        # 去重和排序
        return self._deduplicate_and_sort(all_items)
    
    def _extract_parameters(self, text_chunks: List[str], system_prompt: str) -> List[Dict[str, Any]]:
        """提取论文中的关键参数"""
        prompt = """
        请从以下论文文本中提取所有技术参数和数值。
        
        对于每个参数，请提供:
        1. 参数名称
        2. 参数值
        3. 单位
        4. 该参数所在的页码（如果文本中没有页码信息，请估算）
        5. 置信度评估
        
        文本内容:
        {text}
        
        请按照指定的JSON格式返回结果。
        """
        
        all_items = []
        for chunk in text_chunks:
            chunk_prompt = prompt.format(text=chunk)
            result = self._call_openai_api(chunk_prompt, system_prompt)
            
            if "items" in result:
                all_items.extend(result["items"])
            
            time.sleep(1)
        
        return self._deduplicate_and_sort(all_items)
    
    def _extract_equations(self, text_chunks: List[str], system_prompt: str) -> List[Dict[str, Any]]:
        """提取论文中的公式"""
        prompt = """
        请从以下论文文本中提取所有数学公式和控制方程。
        
        对于每个公式，请提供:
        1. 公式的名称或描述
        2. 公式的LaTeX表示形式
        3. 公式的物理意义或用途
        4. 该公式所在的页码（如果文本中没有页码信息，请估算）
        5. 置信度评估
        
        文本内容:
        {text}
        
        请按照指定的JSON格式返回结果。
        """
        
        all_items = []
        for chunk in text_chunks:
            chunk_prompt = prompt.format(text=chunk)
            result = self._call_openai_api(chunk_prompt, system_prompt)
            
            if "items" in result:
                all_items.extend(result["items"])
            
            time.sleep(1)
        
        return self._deduplicate_and_sort(all_items)
    
    def _extract_figures(self, text_chunks: List[str], system_prompt: str) -> List[Dict[str, Any]]:
        """提取论文中的图表信息"""
        prompt = """
        请从以下论文文本中提取所有图表的信息。
        
        对于每个图表，请提供:
        1. 图表的编号和标题
        2. 图表的主要内容和趋势
        3. 图表展示的关键结论
        4. 该图表所在的页码（如果文本中没有页码信息，请估算）
        5. 置信度评估
        
        文本内容:
        {text}
        
        请按照指定的JSON格式返回结果。
        """
        
        all_items = []
        for chunk in text_chunks:
            chunk_prompt = prompt.format(text=chunk)
            result = self._call_openai_api(chunk_prompt, system_prompt)
            
            if "items" in result:
                all_items.extend(result["items"])
            
            time.sleep(1)
        
        return self._deduplicate_and_sort(all_items)
    
    def _deduplicate_and_sort(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和排序结果"""
        # 简单去重：基于内容
        seen = set()
        deduplicated = []
        
        for item in items:
            content = item.get("content", "").lower()
            if content not in seen:
                seen.add(content)
                deduplicated.append(item)
        
        # 按页码排序
        deduplicated.sort(key=lambda x: int(x.get("source_page", 0)))
        
        return deduplicated
    
    def extract_with_retry(self, text: str, role: str = "通用研究员", 
                          extraction_mode: str = "标准提取", 
                          max_retries: int = 3) -> Dict[str, Any]:
        """
        带重试机制的提取方法
        
        Args:
            text (str): 论文文本内容
            role (str): 专家角色
            extraction_mode (str): 提取模式
            max_retries (int): 最大重试次数
            
        Returns:
            Dict[str, Any]: 提取的结果
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                return self.extract_from_text(text, role, extraction_mode)
            except Exception as e:
                last_error = e
                print(f"提取尝试 {attempt + 1} 失败: {str(e)}")
                time.sleep(2 ** attempt)  # 指数退避
        
        # 如果所有尝试都失败，返回错误信息
        return {
            "error": f"提取失败，已尝试 {max_retries} 次。最后错误: {str(last_error)}",
            "summary": [],
            "parameters": [],
            "equations": [],
            "figures": [],
            "metadata": {
                "role": role,
                "extraction_mode": extraction_mode,
                "model": self.model,
                "failed": True
            }
        }