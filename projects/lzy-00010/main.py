#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件自动整理工具 - 主入口文件
"""

import sys
import os


def main():
    if len(sys.argv) > 1:
        from file_organizer.cli import CLI
        cli = CLI()
        return cli.run()
    else:
        try:
            import tkinter
            from file_organizer.gui import FileOrganizerApp
            app = FileOrganizerApp()
            app.run()
            return 0
        except ImportError:
            from file_organizer.cli import CLI
            print("图形界面不可用，使用命令行模式")
            print("使用 -h 或 --help 查看帮助")
            cli = CLI()
            return cli.run(["--help"])


if __name__ == "__main__":
    sys.exit(main())
