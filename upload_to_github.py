#!/usr/bin/env python3
"""
上传项目到GitHub的辅助脚本
"""

import subprocess
import webbrowser
import os

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"错误: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"运行命令时出错: {str(e)}")
        return False

def main():
    print("=== DeepSpec: SPE Paper Scrutinizer GitHub上传助手 ===\n")
    
    # 1. 检查当前Git状态
    print("当前Git状态:")
    run_command("git status", "检查Git状态")
    
    # 2. 显示当前远程仓库
    print("\n当前远程仓库:")
    run_command("git remote -v", "显示远程仓库")
    
    # 3. 提示用户创建GitHub仓库
    repo_url = "https://github.com/xaiohuangningde/paperreader"
    print(f"\n请按以下步骤操作:")
    print(f"1. 在浏览器中访问: {repo_url}")
    print("2. 点击'Create a new repository'按钮")
    print("3. 仓库名称输入: paperreader")
    print("4. 选择公开(Public)或私有(Private)")
    print("5. 不要勾选'Initialize this repository with a README'")
    print("6. 点击'Create repository'")
    
    # 询问是否自动打开GitHub页面
    choice = input("\n是否自动打开GitHub创建页面? (y/n): ")
    if choice.lower() == 'y':
        webbrowser.open(f"{repo_url}/new")
    
    # 等待用户创建仓库
    input("\n请在GitHub上创建仓库后，按Enter键继续...")
    
    # 4. 推送代码到GitHub
    print("\n正在推送代码到GitHub...")
    success = run_command("git push -u origin main", "推送代码到GitHub")
    
    if success:
        print("\n✅ 成功上传到GitHub!")
        print(f"您可以在 {repo_url} 查看您的项目")
    else:
        print("\n❌ 上传失败，请检查:")
        print("1. 您是否已成功创建GitHub仓库")
        print("2. 您是否已登录GitHub账户")
        print("3. 仓库URL是否正确")
        print("4. 您是否有推送权限")

if __name__ == "__main__":
    main()