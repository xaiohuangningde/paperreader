import pandas as pd
import json
import xlsxwriter
from datetime import datetime
import os
from typing import Dict, List, Any

class ResultFormatter:
    """
    结果格式化器类，负责将提取的结果格式化为各种输出格式
    """
    
    def __init__(self):
        self.output_dir = "data/exports"
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def format_to_dataframe(self, extraction_result: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """
        将提取结果转换为DataFrame格式
        
        Args:
            extraction_result: AI提取器返回的结果
            
        Returns:
            Dict[str, pd.DataFrame]: 包含各类数据DataFrame的字典
        """
        dataframes = {}
        
        # 处理核心结论
        if "summary" in extraction_result and extraction_result["summary"]:
            summary_data = []
            for item in extraction_result["summary"]:
                summary_data.append({
                    "内容": item.get("content", ""),
                    "页码": item.get("source_page", ""),
                    "置信度": item.get("confidence", ""),
                    "解释": item.get("explanation", "")
                })
            
            dataframes["核心结论"] = pd.DataFrame(summary_data)
        
        # 处理关键参数
        if "parameters" in extraction_result and extraction_result["parameters"]:
            param_data = []
            for item in extraction_result["parameters"]:
                # 解析参数信息
                content = item.get("content", "")
                
                # 尝试从内容中提取参数名称、值和单位
                param_name = content
                param_value = ""
                param_unit = ""
                
                # 这里可以添加更复杂的解析逻辑
                # 例如使用正则表达式提取数值和单位
                
                param_data.append({
                    "参数名称": param_name,
                    "参数值": param_value,
                    "单位": param_unit,
                    "页码": item.get("source_page", ""),
                    "置信度": item.get("confidence", ""),
                    "解释": item.get("explanation", "")
                })
            
            dataframes["关键参数"] = pd.DataFrame(param_data)
        
        # 处理公式
        if "equations" in extraction_result and extraction_result["equations"]:
            equation_data = []
            for item in extraction_result["equations"]:
                equation_data.append({
                    "公式名称": item.get("content", "").split('\n')[0],
                    "LaTeX公式": item.get("content", ""),
                    "物理意义": item.get("explanation", ""),
                    "页码": item.get("source_page", ""),
                    "置信度": item.get("confidence", "")
                })
            
            dataframes["公式"] = pd.DataFrame(equation_data)
        
        # 处理图表
        if "figures" in extraction_result and extraction_result["figures"]:
            figure_data = []
            for item in extraction_result["figures"]:
                figure_data.append({
                    "图表信息": item.get("content", ""),
                    "主要结论": item.get("explanation", ""),
                    "页码": item.get("source_page", ""),
                    "置信度": item.get("confidence", "")
                })
            
            dataframes["图表"] = pd.DataFrame(figure_data)
        
        return dataframes
    
    def export_to_excel(self, extraction_result: Dict[str, Any], 
                       comments: Dict[str, str] = None, 
                       filename: str = None) -> str:
        """
        将提取结果导出为Excel文件
        
        Args:
            extraction_result: AI提取器返回的结果
            comments: 用户批注
            filename: 自定义文件名
            
        Returns:
            str: 导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DeepSpec_Export_{timestamp}.xlsx"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 创建Excel写入器
        workbook = xlsxwriter.Workbook(output_path)
        
        # 添加格式
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        high_conf_format = workbook.add_format({
            'bg_color': '#D4EDDA',  # 浅绿色
            'border': 1
        })
        
        medium_conf_format = workbook.add_format({
            'bg_color': '#FFF3CD',  # 浅黄色
            'border': 1
        })
        
        low_conf_format = workbook.add_format({
            'bg_color': '#F8D7DA',  # 浅红色
            'border': 1
        })
        
        # 获取数据帧
        dataframes = self.format_to_dataframe(extraction_result)
        
        # 写入各个工作表
        for sheet_name, df in dataframes.items():
            worksheet = workbook.add_worksheet(sheet_name)
            
            # 设置列宽
            for i, col in enumerate(df.columns):
                max_len = max(
                    df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.set_column(i, i, min(max_len + 2, 50))
            
            # 写入表头
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # 写入数据
            for row_num, row_data in enumerate(df.values):
                for col_num, value in enumerate(row_data):
                    # 根据置信度设置格式
                    if col_num == 3 and row_num < len(df):  # 假设第4列是置信度
                        confidence = df.iloc[row_num, col_num]
                        if confidence == 'High':
                            cell_format = high_conf_format
                        elif confidence == 'Medium':
                            cell_format = medium_conf_format
                        elif confidence == 'Low':
                            cell_format = low_conf_format
                        else:
                            cell_format = None
                    else:
                        cell_format = None
                    
                    worksheet.write(row_num + 1, col_num, value, cell_format)
        
        # 添加元数据工作表
        if "metadata" in extraction_result:
            metadata = extraction_result["metadata"]
            worksheet = workbook.add_worksheet("元数据")
            
            worksheet.write(0, 0, "属性", header_format)
            worksheet.write(0, 1, "值", header_format)
            
            metadata_items = [
                ("分析角色", metadata.get("role", "")),
                ("提取模式", metadata.get("extraction_mode", "")),
                ("使用模型", metadata.get("model", "")),
                ("导出时间", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ]
            
            for i, (key, value) in enumerate(metadata_items, 1):
                worksheet.write(i, 0, key)
                worksheet.write(i, 1, str(value))
        
        # 添加批注工作表
        if comments:
            worksheet = workbook.add_worksheet("专家批注")
            
            worksheet.write(0, 0, "批注类型", header_format)
            worksheet.write(0, 1, "批注内容", header_format)
            
            for i, (key, value) in enumerate(comments.items(), 1):
                worksheet.write(i, 0, key)
                worksheet.write(i, 1, str(value))
        
        workbook.close()
        return output_path
    
    def export_to_json(self, extraction_result: Dict[str, Any], 
                      comments: Dict[str, str] = None, 
                      filename: str = None) -> str:
        """
        将提取结果导出为JSON文件
        
        Args:
            extraction_result: AI提取器返回的结果
            comments: 用户批注
            filename: 自定义文件名
            
        Returns:
            str: 导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DeepSpec_Export_{timestamp}.json"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 准备导出数据
        export_data = extraction_result.copy()
        
        # 添加批注
        if comments:
            export_data["comments"] = comments
        
        # 添加导出时间戳
        export_data["export_timestamp"] = datetime.now().isoformat()
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        return output_path
    
    def export_to_csv(self, extraction_result: Dict[str, Any], 
                     filename: str = None) -> str:
        """
        将提取结果导出为CSV文件（只包含关键参数）
        
        Args:
            extraction_result: AI提取器返回的结果
            filename: 自定义文件名
            
        Returns:
            str: 导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DeepSpec_Parameters_{timestamp}.csv"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 获取关键参数的DataFrame
        dataframes = self.format_to_dataframe(extraction_result)
        
        if "关键参数" in dataframes:
            dataframes["关键参数"].to_csv(output_path, index=False, encoding='utf-8-sig')
        
        return output_path
    
    def create_summary_report(self, extraction_result: Dict[str, Any], 
                             comments: Dict[str, str] = None) -> str:
        """
        创建摘要报告
        
        Args:
            extraction_result: AI提取器返回的结果
            comments: 用户批注
            
        Returns:
            str: 报告内容
        """
        # 获取数据帧
        dataframes = self.format_to_dataframe(extraction_result)
        
        # 构建报告
        report_lines = []
        report_lines.append("# DeepSpec 分析报告")
        report_lines.append("")
        
        # 添加元数据
        if "metadata" in extraction_result:
            metadata = extraction_result["metadata"]
            report_lines.append("## 分析信息")
            report_lines.append(f"- 分析角色: {metadata.get('role', '未知')}")
            report_lines.append(f"- 提取模式: {metadata.get('extraction_mode', '未知')}")
            report_lines.append(f"- 使用模型: {metadata.get('model', '未知')}")
            report_lines.append(f"- 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_lines.append("")
        
        # 添加核心结论
        if "核心结论" in dataframes and not dataframes["核心结论"].empty:
            report_lines.append("## 核心结论")
            for _, row in dataframes["核心结论"].iterrows():
                report_lines.append(f"- {row['内容']} (页码: {row['页码']}, 置信度: {row['置信度']})")
            report_lines.append("")
        
        # 添加关键参数
        if "关键参数" in dataframes and not dataframes["关键参数"].empty:
            report_lines.append("## 关键参数")
            for _, row in dataframes["关键参数"].iterrows():
                report_lines.append(f"- {row['参数名称']}: {row['参数值']} {row['单位']} (页码: {row['页码']}, 置信度: {row['置信度']})")
            report_lines.append("")
        
        # 添加批注
        if comments:
            report_lines.append("## 专家批注")
            for key, value in comments.items():
                if value.strip():  # 只添加非空批注
                    report_lines.append(f"- {key}: {value}")
            report_lines.append("")
        
        return "\n".join(report_lines)
    
    def export_summary_report(self, extraction_result: Dict[str, Any], 
                              comments: Dict[str, str] = None, 
                              filename: str = None) -> str:
        """
        导出摘要报告
        
        Args:
            extraction_result: AI提取器返回的结果
            comments: 用户批注
            filename: 自定义文件名
            
        Returns:
            str: 导出文件的路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"DeepSpec_Summary_{timestamp}.md"
        
        output_path = os.path.join(self.output_dir, filename)
        
        # 创建报告内容
        report_content = self.create_summary_report(extraction_result, comments)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_path