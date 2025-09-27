#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票信息系统启动脚本
运行此脚本启动Web服务器
"""

import os
import sys

def check_dependencies():
    """检查依赖包是否安装"""
    required_packages = [
        'flask',
        'tushare',
        'pandas',
        'requests',
        'flask_cors'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

    return True

def main():
    """主函数"""
    print("=" * 50)
    print("股票信息系统")
    print("=" * 50)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    # 导入并运行Flask应用
    try:
        from app import app
        print("正在启动服务器...")
        print("服务器地址: http://localhost:5000")
        print("按 Ctrl+C 停止服务器")
        print("-" * 50)

        app.run(debug=True, host='0.0.0.0', port=5000)

    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()