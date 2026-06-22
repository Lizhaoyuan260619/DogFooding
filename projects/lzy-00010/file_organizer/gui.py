import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict, Any
import threading

from .database import Database
from .organizer import OrganizerEngine
from .templates import TemplateManager
from .file_operator import FileOperation
from .smart_recommend import SmartRecommenderEngine
from .exporter import ExportOptions, RuleExporter


class FileOrganizerApp:
    def __init__(self, root: tk.Tk = None):
        if root is None:
            root = tk.Tk()
        self.root = root
        self.root.title("文件自动整理工具")
        self.root.geometry("900x650")
        self.root.minsize(800, 550)

        self.db = Database()
        self.engine = OrganizerEngine(db=self.db)
        self.smart_engine = SmartRecommenderEngine(db=self.db)
        self.selected_dirs = []
        self._last_smart_result = None

        self._setup_style()
        self._create_menu()
        self._create_main_layout()
        self._load_rules()

    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass

        style.configure("Title.TLabel", font=("Microsoft YaHei", 14, "bold"))
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei", 10))
        style.configure("Card.TFrame", background="white", relief="flat")
        style.configure("Accent.TButton", font=("Microsoft YaHei", 10, "bold"))

    def _create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="添加目录", command=self._add_directory)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        rule_menu = tk.Menu(menubar, tearoff=0)
        rule_menu.add_command(label="新建规则", command=self._new_rule_dialog)
        rule_menu.add_command(label="从模板创建", command=self._template_dialog)
        rule_menu.add_command(label="管理规则", command=self._manage_rules_dialog)
        menubar.add_cascade(label="规则", menu=rule_menu)

        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="操作日志", command=self._show_logs_dialog)
        tools_menu.add_command(label="撤销操作", command=self._undo_dialog)
        tools_menu.add_separator()
        tools_menu.add_command(label="智能推荐分析", command=self._smart_analyze_dialog)
        menubar.add_cascade(label="工具", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self._show_help)
        help_menu.add_command(label="关于", command=self._show_about)
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)

    def _create_main_layout(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="文件自动整理工具", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(header_frame, text="  智能分类、整理您的文件",
                 style="Subtitle.TLabel").pack(side=tk.LEFT, padx=10)

        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        self._create_directory_panel(left_panel)
        self._create_rules_panel(right_panel)

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        self.dry_run_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(bottom_frame, text="干跑模式（仅预览，不实际操作）",
                       variable=self.dry_run_var).pack(side=tk.LEFT)

        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(bottom_frame, text="包含子目录",
                       variable=self.recursive_var).pack(side=tk.LEFT, padx=20)

        ttk.Button(bottom_frame, text="智能推荐",
                  command=self._smart_analyze_dialog, width=12).pack(side=tk.RIGHT, padx=5)
        ttk.Button(bottom_frame, text="开始整理", style="Accent.TButton",
                  command=self._start_organize, width=15).pack(side=tk.RIGHT)

        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(main_frame, textvariable=self.progress_var,
                 foreground="gray").pack(anchor=tk.W, pady=(5, 0))

    def _create_directory_panel(self, parent):
        dir_frame = ttk.LabelFrame(parent, text="目标目录", padding="10")
        dir_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(dir_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="添加目录", command=self._add_directory,
                  width=10).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="移除选中", command=self._remove_directory,
                  width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear_directories,
                  width=10).pack(side=tk.LEFT)

        self.dir_listbox = tk.Listbox(dir_frame, height=8, selectmode=tk.EXTENDED)
        self.dir_listbox.pack(fill=tk.BOTH, expand=True)

        dir_scrollbar = ttk.Scrollbar(dir_frame, orient=tk.VERTICAL,
                                     command=self.dir_listbox.yview)
        dir_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.dir_listbox.config(yscrollcommand=dir_scrollbar.set)

    def _create_rules_panel(self, parent):
        rule_frame = ttk.LabelFrame(parent, text="整理规则", padding="10")
        rule_frame.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(rule_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="新建", command=self._new_rule_dialog,
                  width=8).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="模板", command=self._template_dialog,
                  width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑", command=self._edit_rule_dialog,
                  width=8).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="删除", command=self._delete_rule,
                  width=8).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="测试", command=self._test_rule,
                  width=8).pack(side=tk.LEFT)

        self.rules_tree = ttk.Treeview(rule_frame, columns=("priority", "status", "conditions"),
                                       show="tree headings", height=10)
        self.rules_tree.heading("#0", text="规则名称")
        self.rules_tree.heading("priority", text="优先级")
        self.rules_tree.heading("status", text="状态")
        self.rules_tree.heading("conditions", text="条件数")
        self.rules_tree.column("#0", width=150)
        self.rules_tree.column("priority", width=60, anchor=tk.CENTER)
        self.rules_tree.column("status", width=60, anchor=tk.CENTER)
        self.rules_tree.column("conditions", width=60, anchor=tk.CENTER)
        self.rules_tree.pack(fill=tk.BOTH, expand=True)

    def _load_rules(self):
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)

        rules = self.db.get_all_rules()
        for rule in rules:
            status = "启用" if rule["enabled"] else "禁用"
            self.rules_tree.insert("", tk.END, iid=str(rule["id"]),
                                   text=rule["name"],
                                   values=(rule["priority"], status, len(rule["conditions"])))

    def _add_directory(self):
        directory = filedialog.askdirectory(title="选择要整理的目录")
        if directory:
            if directory not in self.selected_dirs:
                self.selected_dirs.append(directory)
                self.dir_listbox.insert(tk.END, directory)
                self.progress_var.set(f"已添加 {len(self.selected_dirs)} 个目录")

    def _remove_directory(self):
        selection = self.dir_listbox.curselection()
        for index in reversed(selection):
            self.dir_listbox.delete(index)
            del self.selected_dirs[index]
        self.progress_var.set(f"已添加 {len(self.selected_dirs)} 个目录")

    def _clear_directories(self):
        self.dir_listbox.delete(0, tk.END)
        self.selected_dirs.clear()
        self.progress_var.set("已清空目录列表")

    def _new_rule_dialog(self):
        RuleDialog(self.root, self.db, on_saved=self._load_rules)

    def _edit_rule_dialog(self):
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要编辑的规则")
            return
        rule_id = int(selection[0])
        rule = self.db.get_rule(rule_id)
        if rule:
            RuleDialog(self.root, self.db, rule_data=rule, on_saved=self._load_rules)

    def _delete_rule(self):
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的规则")
            return
        rule_id = int(selection[0])
        if messagebox.askyesno("确认", "确定要删除选中的规则吗？"):
            self.db.delete_rule(rule_id)
            self._load_rules()
            self.progress_var.set("规则已删除")

    def _test_rule(self):
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要测试的规则")
            return
        rule_id = int(selection[0])
        rule = self.db.get_rule(rule_id)
        if rule:
            TestRuleDialog(self.root, self.engine, rule)

    def _template_dialog(self):
        TemplateDialog(self.root, self.db, on_applied=self._load_rules)

    def _manage_rules_dialog(self):
        self._template_dialog()

    def _show_logs_dialog(self):
        LogsDialog(self.root, self.db)

    def _undo_dialog(self):
        if messagebox.askyesno("撤销操作", "确定要撤销最近一次整理操作吗？"):
            result = self.engine.undo()
            if result["success"]:
                messagebox.showinfo("撤销完成",
                    f"撤销了 {result['total_operations']} 个操作\n"
                    f"成功: {result['success_count']}, 失败: {result['failed_count']}")
            else:
                messagebox.showwarning("提示", result["message"])

    def _show_help(self):
        HelpDialog(self.root)

    def _show_about(self):
        messagebox.showinfo("关于",
            "文件自动整理工具 v1.0.0\n\n"
            "智能分类、整理和管理您的文件\n"
            "支持自定义规则、模板、干跑模式和撤销功能\n\n"
            "智能推荐模块：自动分析项目结构并生成优化建议")

    def _smart_analyze_dialog(self):
        SmartAnalyzeDialog(self.root, self.smart_engine,
                           self.selected_dirs, on_result=self._on_smart_result)

    def _on_smart_result(self, result):
        self._last_smart_result = result

    def _start_organize(self):
        if not self.selected_dirs:
            messagebox.showinfo("提示", "请先添加要整理的目录")
            return

        rules = self.db.get_all_rules(enabled_only=True)
        if not rules:
            messagebox.showinfo("提示", "没有启用的规则，请先创建或启用规则")
            return

        dry_run = self.dry_run_var.get()
        recursive = self.recursive_var.get()

        dialog = OrganizeProgressDialog(self.root, self.engine, self.selected_dirs,
                                        dry_run, recursive)
        dialog.show()

    def run(self):
        self.root.mainloop()


class RuleDialog:
    def __init__(self, parent, db: Database, rule_data: Dict = None, on_saved=None):
        self.db = db
        self.rule_data = rule_data
        self.on_saved = on_saved

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑规则" if rule_data else "新建规则")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.conditions = []
        self.actions = []

        if rule_data:
            self.conditions = list(rule_data.get("conditions", []))
            self.actions = list(rule_data.get("actions", []))

        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="规则名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(main_frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        if self.rule_data:
            self.name_entry.insert(0, self.rule_data.get("name", ""))

        ttk.Label(main_frame, text="描述:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.desc_entry = ttk.Entry(main_frame, width=40)
        self.desc_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        if self.rule_data:
            self.desc_entry.insert(0, self.rule_data.get("description", ""))

        ttk.Label(main_frame, text="优先级:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.priority_spin = ttk.Spinbox(main_frame, from_=0, to=100, width=10)
        self.priority_spin.grid(row=2, column=1, sticky=tk.W, pady=5)
        if self.rule_data:
            self.priority_spin.set(self.rule_data.get("priority", 0))

        ttk.Label(main_frame, text="逻辑运算:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.logic_var = tk.StringVar(value=self.rule_data.get("logic_operator", "AND") if self.rule_data else "AND")
        logic_frame = ttk.Frame(main_frame)
        logic_frame.grid(row=3, column=1, sticky=tk.W, pady=5)
        ttk.Radiobutton(logic_frame, text="AND", variable=self.logic_var, value="AND").pack(side=tk.LEFT)
        ttk.Radiobutton(logic_frame, text="OR", variable=self.logic_var, value="OR").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(logic_frame, text="NOT", variable=self.logic_var, value="NOT").pack(side=tk.LEFT)

        ttk.Label(main_frame, text="条件:").grid(row=4, column=0, sticky=tk.NW, pady=5)
        cond_frame = ttk.Frame(main_frame)
        cond_frame.grid(row=4, column=1, sticky=tk.EW, pady=5)

        self.cond_listbox = tk.Listbox(cond_frame, height=6)
        self.cond_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        cond_btn_frame = ttk.Frame(cond_frame)
        cond_btn_frame.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(cond_btn_frame, text="添加", command=self._add_condition, width=8).pack(pady=2)
        ttk.Button(cond_btn_frame, text="编辑", command=self._edit_condition, width=8).pack(pady=2)
        ttk.Button(cond_btn_frame, text="删除", command=self._delete_condition, width=8).pack(pady=2)
        ttk.Button(cond_btn_frame, text="上移", command=lambda: self._move_condition(-1), width=8).pack(pady=2)
        ttk.Button(cond_btn_frame, text="下移", command=lambda: self._move_condition(1), width=8).pack(pady=2)

        self._refresh_conditions()

        ttk.Label(main_frame, text="操作:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        act_frame = ttk.Frame(main_frame)
        act_frame.grid(row=5, column=1, sticky=tk.EW, pady=5)

        self.act_listbox = tk.Listbox(act_frame, height=6)
        self.act_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        act_btn_frame = ttk.Frame(act_frame)
        act_btn_frame.pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(act_btn_frame, text="添加", command=self._add_action, width=8).pack(pady=2)
        ttk.Button(act_btn_frame, text="编辑", command=self._edit_action, width=8).pack(pady=2)
        ttk.Button(act_btn_frame, text="删除", command=self._delete_action, width=8).pack(pady=2)
        ttk.Button(act_btn_frame, text="上移", command=lambda: self._move_action(-1), width=8).pack(pady=2)
        ttk.Button(act_btn_frame, text="下移", command=lambda: self._move_action(1), width=8).pack(pady=2)

        self._refresh_actions()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="保存", command=self._save, width=15).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=10)

        main_frame.columnconfigure(1, weight=1)

    def _refresh_conditions(self):
        self.cond_listbox.delete(0, tk.END)
        for cond in self.conditions:
            negate_str = "NOT " if cond.get("negate") else ""
            self.cond_listbox.insert(tk.END,
                f"{negate_str}{cond['condition_type']}: {cond.get('condition_value', '')}")

    def _add_condition(self):
        dialog = ConditionDialog(self.dialog)
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self.conditions.append(dialog.result)
            self._refresh_conditions()

    def _edit_condition(self):
        selection = self.cond_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        dialog = ConditionDialog(self.dialog, self.conditions[idx])
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self.conditions[idx] = dialog.result
            self._refresh_conditions()

    def _delete_condition(self):
        selection = self.cond_listbox.curselection()
        if selection:
            del self.conditions[selection[0]]
            self._refresh_conditions()

    def _move_condition(self, direction):
        selection = self.cond_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.conditions):
            self.conditions[idx], self.conditions[new_idx] = self.conditions[new_idx], self.conditions[idx]
            self.conditions[idx]["sort_order"] = idx
            self.conditions[new_idx]["sort_order"] = new_idx
            self._refresh_conditions()
            self.cond_listbox.selection_set(new_idx)

    def _refresh_actions(self):
        self.act_listbox.delete(0, tk.END)
        for action in self.actions:
            params = action.get("action_params", {})
            params_str = ", ".join(f"{k}={v}" for k, v in params.items())
            self.act_listbox.insert(tk.END, f"{action['action_type']}: {params_str}")

    def _add_action(self):
        dialog = ActionDialog(self.dialog)
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self.actions.append(dialog.result)
            self._refresh_actions()

    def _edit_action(self):
        selection = self.act_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        dialog = ActionDialog(self.dialog, self.actions[idx])
        self.dialog.wait_window(dialog.dialog)
        if dialog.result:
            self.actions[idx] = dialog.result
            self._refresh_actions()

    def _delete_action(self):
        selection = self.act_listbox.curselection()
        if selection:
            del self.actions[selection[0]]
            self._refresh_actions()

    def _move_action(self, direction):
        selection = self.act_listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        new_idx = idx + direction
        if 0 <= new_idx < len(self.actions):
            self.actions[idx], self.actions[new_idx] = self.actions[new_idx], self.actions[idx]
            self.actions[idx]["sort_order"] = idx
            self.actions[new_idx]["sort_order"] = new_idx
            self._refresh_actions()
            self.act_listbox.selection_set(new_idx)

    def _save(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("错误", "请输入规则名称")
            return

        rule_data = {
            "name": name,
            "description": self.desc_entry.get().strip(),
            "priority": int(self.priority_spin.get()),
            "enabled": True,
            "logic_operator": self.logic_var.get(),
            "conditions": self.conditions,
            "actions": self.actions
        }

        if self.rule_data:
            rule_data["id"] = self.rule_data["id"]

        self.db.save_rule_complete(rule_data)

        if self.on_saved:
            self.on_saved()

        self.dialog.destroy()


class ConditionDialog:
    def __init__(self, parent, condition_data: Dict = None):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑条件" if condition_data else "添加条件")
        self.dialog.geometry("400x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.condition_data = condition_data
        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="条件类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(frame, textvariable=self.type_var, state="readonly", width=30)
        self.type_combo['values'] = [
            "extension",
            "filename_keyword",
            "file_size_min",
            "file_size_max",
            "date_modified_from",
            "date_modified_to",
            "date_created_from",
            "date_created_to",
            "regex",
            "file_type"
        ]
        self.type_combo.grid(row=0, column=1, sticky=tk.EW, pady=5)
        self.type_combo.current(0)

        ttk.Label(frame, text="条件值:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.value_entry = ttk.Entry(frame, width=32)
        self.value_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)

        self.negate_var = tk.BooleanVar()
        ttk.Checkbutton(frame, text="NOT（取反）", variable=self.negate_var).grid(
            row=2, column=1, sticky=tk.W, pady=5)

        desc_label = ttk.Label(frame, text="", foreground="gray", wraplength=350)
        desc_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        self.type_combo.bind('<<ComboboxSelected>>',
                            lambda e: desc_label.config(text=self._get_description()))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="确定", command=self._ok, width=12).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=12).pack(side=tk.RIGHT, padx=10)

        frame.columnconfigure(1, weight=1)

        if self.condition_data:
            self.type_var.set(self.condition_data["condition_type"])
            self.value_entry.insert(0, self.condition_data.get("condition_value", ""))
            self.negate_var.set(self.condition_data.get("negate", False))
            desc_label.config(text=self._get_description())

    def _get_description(self):
        descriptions = {
            "extension": "按文件后缀名匹配，多个后缀用逗号分隔，如: jpg,png,gif",
            "filename_keyword": "按文件名关键词匹配，多个关键词用逗号分隔",
            "file_size_min": "文件最小大小，如: 1MB, 500KB, 1GB",
            "file_size_max": "文件最大大小，如: 10MB, 100KB",
            "date_modified_from": "修改日期从，格式: 2024-01-01 或 30d",
            "date_modified_to": "修改日期到，格式: 2024-01-01 或 7d",
            "date_created_from": "创建日期从，格式同上",
            "date_created_to": "创建日期到，格式同上",
            "regex": "正则表达式匹配文件名",
            "file_type": "按文件类型匹配：image, document, audio, video, archive, code"
        }
        return descriptions.get(self.type_var.get(), "")

    def _ok(self):
        cond_type = self.type_var.get()
        value = self.value_entry.get().strip()

        if not value and cond_type not in [""]:
            pass

        self.result = {
            "condition_type": cond_type,
            "condition_value": value,
            "negate": self.negate_var.get(),
            "sort_order": 0
        }
        self.dialog.destroy()


class ActionDialog:
    def __init__(self, parent, action_data: Dict = None):
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑操作" if action_data else "添加操作")
        self.dialog.geometry("450x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.action_data = action_data
        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="操作类型:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(frame, textvariable=self.type_var, state="readonly", width=30)
        self.type_combo['values'] = ["move", "rename", "copy", "backup", "zip"]
        self.type_combo.grid(row=0, column=1, sticky=tk.EW, pady=5)
        self.type_combo.current(0)
        self.type_combo.bind('<<ComboboxSelected>>', lambda e: self._update_params_fields())

        self.params_frame = ttk.Frame(frame)
        self.params_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=10)

        self.params_entries = {}
        self._update_params_fields()

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="确定", command=self._ok, width=12).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=12).pack(side=tk.RIGHT, padx=10)

        frame.columnconfigure(1, weight=1)

        if self.action_data:
            self.type_var.set(self.action_data["action_type"])
            self._update_params_fields()
            params = self.action_data.get("action_params", {})
            for key, entry in self.params_entries.items():
                if key in params:
                    entry.delete(0, tk.END)
                    entry.insert(0, str(params[key]))

    def _update_params_fields(self):
        for widget in self.params_frame.winfo_children():
            widget.destroy()
        self.params_entries.clear()

        action_type = self.type_var.get()

        param_configs = {
            "move": [
                ("target_dir", "目标文件夹", "移动到的目标目录路径"),
                ("new_name", "新文件名", "可选，留空保持原名")
            ],
            "rename": [
                ("new_name", "新文件名", "新的文件名（含扩展名）")
            ],
            "copy": [
                ("target_dir", "目标文件夹", "复制到的目标目录路径"),
                ("new_name", "新文件名", "可选，留空保持原名")
            ],
            "backup": [
                ("backup_dir", "备份目录", "备份文件存放目录，留空使用默认")
            ],
            "zip": [
                ("target_dir", "目标文件夹", "压缩文件存放目录，留空使用当前目录"),
                ("zip_name", "压缩文件名", "可选，留空使用原文件名"),
                ("delete_original", "删除原文件", "压缩后是否删除原文件（是/否）")
            ]
        }

        configs = param_configs.get(action_type, [])
        for i, (key, label, desc) in enumerate(configs):
            ttk.Label(self.params_frame, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(self.params_frame, width=30)
            entry.grid(row=i, column=1, sticky=tk.EW, pady=3)
            ttk.Label(self.params_frame, text=desc, foreground="gray",
                     font=("Microsoft YaHei", 8)).grid(row=i + 1, column=1, sticky=tk.W, pady=(0, 5))
            self.params_entries[key] = entry

        self.params_frame.columnconfigure(1, weight=1)

    def _ok(self):
        action_type = self.type_var.get()
        params = {}

        for key, entry in self.params_entries.items():
            value = entry.get().strip()
            if value:
                if key == "delete_original":
                    params[key] = value.lower() in ["是", "true", "yes", "1", "y"]
                else:
                    params[key] = value

        self.result = {
            "action_type": action_type,
            "action_params": params,
            "sort_order": 0
        }
        self.dialog.destroy()


class TemplateDialog:
    def __init__(self, parent, db: Database, on_applied=None):
        self.db = db
        self.on_applied = on_applied
        self.selected_template = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("规则模板")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_templates()

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="选择模板", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 10))

        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        self.template_list = tk.Listbox(list_frame, height=12)
        self.template_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.template_list.bind('<<ListboxSelect>>', self._on_template_select)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL,
                                 command=self.template_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.template_list.config(yscrollcommand=scrollbar.set)

        self.detail_frame = ttk.LabelFrame(main_frame, text="模板详情", padding="10")
        self.detail_frame.pack(fill=tk.X, pady=(10, 0))

        self.detail_text = tk.Text(self.detail_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(15, 0))
        ttk.Button(btn_frame, text="应用模板", command=self._apply_template,
                  width=15, style="Accent.TButton").pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy,
                  width=15).pack(side=tk.RIGHT, padx=10)

    def _load_templates(self):
        self.templates = TemplateManager.get_all_templates()
        for template in self.templates:
            self.template_list.insert(tk.END, f"  {template['icon']}  {template['name']}")

    def _on_template_select(self, event):
        selection = self.template_list.curselection()
        if not selection:
            return
        idx = selection[0]
        template = self.templates[idx]

        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete(1.0, tk.END)

        text = f"名称: {template['name']}\n"
        text += f"分类: {template['category']}\n"
        text += f"描述: {template['description']}\n\n"

        if template.get("params"):
            text += "可配置参数:\n"
            for param in template["params"]:
                text += f"  - {param['label']}: {param['description']}\n"
                text += f"    默认值: {param['default']}\n"

        self.detail_text.insert(1.0, text)
        self.detail_text.config(state=tk.DISABLED)

        self.selected_template = template

    def _apply_template(self):
        if not self.selected_template:
            messagebox.showinfo("提示", "请先选择一个模板")
            return

        template = self.selected_template
        params = {}

        if template.get("params") and template["params"]:
            TemplateParamsDialog(self.dialog, template, self._do_apply)
        else:
            self._do_apply(params)

    def _do_apply(self, params):
        rule_ids = TemplateManager.apply_template(self.db, self.selected_template["id"], params)
        messagebox.showinfo("成功",
            f"模板 \"{self.selected_template['name']}\" 已应用\n"
            f"生成了 {len(rule_ids)} 条规则")
        if self.on_applied:
            self.on_applied()
        self.dialog.destroy()


class TemplateParamsDialog:
    def __init__(self, parent, template: Dict, on_apply):
        self.template = template
        self.on_apply = on_apply

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("配置模板参数")
        self.dialog.geometry("450x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.param_vars = {}
        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=self.template["name"], style="Title.TLabel").pack(anchor=tk.W)
        ttk.Label(frame, text=self.template["description"], foreground="gray").pack(anchor=tk.W, pady=(0, 15))

        params = self.template.get("params", [])
        for i, param in enumerate(params):
            ttk.Label(frame, text=f"{param['label']}:").pack(anchor=tk.W, pady=(10, 3))

            var = tk.StringVar(value=str(param.get("default", "")))
            self.param_vars[param["name"]] = var

            if param.get("type") == "select":
                combo = ttk.Combobox(frame, textvariable=var, state="readonly")
                options = [opt["label"] for opt in param.get("options", [])]
                combo['values'] = options
                combo.pack(fill=tk.X)
            else:
                entry = ttk.Entry(frame, textvariable=var)
                entry.pack(fill=tk.X)

            ttk.Label(frame, text=param.get("description", ""), foreground="gray",
                     font=("Microsoft YaHei", 8)).pack(anchor=tk.W, pady=(2, 0))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        ttk.Button(btn_frame, text="应用", command=self._apply, width=15).pack(side=tk.RIGHT)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy, width=15).pack(side=tk.RIGHT, padx=10)

    def _apply(self):
        params = {}
        for key, var in self.param_vars.items():
            params[key] = var.get()
        self.on_apply(params)
        self.dialog.destroy()


class TestRuleDialog:
    def __init__(self, parent, engine: OrganizerEngine, rule: Dict):
        self.engine = engine
        self.rule = rule

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"测试规则: {rule['name']}")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="测试文件:").pack(anchor=tk.W)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="添加文件", command=self._add_files, width=10).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="添加文件夹", command=self._add_dir, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空", command=self._clear, width=10).pack(side=tk.LEFT)

        self.result_tree = ttk.Treeview(frame, columns=("status",), show="tree headings")
        self.result_tree.heading("#0", text="文件路径")
        self.result_tree.heading("status", text="结果")
        self.result_tree.column("#0", width=350)
        self.result_tree.column("status", width=80, anchor=tk.CENTER)
        self.result_tree.pack(fill=tk.BOTH, expand=True, pady=10)

        ttk.Button(frame, text="关闭", command=self.dialog.destroy, width=15).pack(pady=10)

    def _add_files(self):
        files = filedialog.askopenfilenames(title="选择测试文件")
        if files:
            self._test_files(list(files))

    def _add_dir(self):
        directory = filedialog.askdirectory(title="选择测试文件夹")
        if directory:
            files = []
            for root, dirs, filenames in os.walk(directory):
                for f in filenames:
                    files.append(os.path.join(root, f))
            self._test_files(files)

    def _clear(self):
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

    def _test_files(self, files):
        results = self.engine.test_rule(self.rule, files)
        for result in results:
            status = "✓ 匹配" if result.get("matched") else "✗ 不匹配"
            self.result_tree.insert("", tk.END, text=result["path"], values=(status,))


class LogsDialog:
    def __init__(self, parent, db: Database):
        self.db = db

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("操作日志")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)

        self._create_widgets()
        self._load_logs()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="最近操作日志", style="Title.TLabel").pack(anchor=tk.W, pady=(0, 10))

        columns = ("time", "type", "status", "source", "target")
        self.logs_tree = ttk.Treeview(frame, columns=columns, show="headings")
        self.logs_tree.heading("time", text="时间")
        self.logs_tree.heading("type", text="类型")
        self.logs_tree.heading("status", text="状态")
        self.logs_tree.heading("source", text="源文件")
        self.logs_tree.heading("target", text="目标")
        self.logs_tree.column("time", width=150)
        self.logs_tree.column("type", width=80)
        self.logs_tree.column("status", width=60, anchor=tk.CENTER)
        self.logs_tree.column("source", width=180)
        self.logs_tree.column("target", width=180)
        self.logs_tree.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL,
                                 command=self.logs_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.logs_tree.configure(yscrollcommand=scrollbar.set)

        ttk.Button(frame, text="关闭", command=self.dialog.destroy, width=15).pack(pady=10)

    def _load_logs(self):
        logs = self.db.get_operation_logs(limit=100)
        for log in logs:
            status = "✓" if log["status"] == "success" else "✗"
            source = os.path.basename(log["source_path"])
            target = os.path.basename(log["target_path"]) if log["target_path"] else ""
            self.logs_tree.insert("", tk.END, values=(
                log["executed_at"],
                log["operation_type"],
                status,
                source,
                target
            ))


class OrganizeProgressDialog:
    def __init__(self, parent, engine: OrganizerEngine, dirs: List[str],
                 dry_run: bool, recursive: bool):
        self.engine = engine
        self.dirs = dirs
        self.dry_run = dry_run
        self.recursive = recursive

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("整理进度")
        self.dialog.geometry("600x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        frame = ttk.Frame(self.dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        mode_text = "干跑模式（预览）" if self.dry_run else "执行模式"
        ttk.Label(frame, text=f"文件整理 - {mode_text}", style="Title.TLabel").pack(anchor=tk.W)

        self.progress_var = tk.StringVar(value="正在准备...")
        ttk.Label(frame, textvariable=self.progress_var, foreground="gray").pack(anchor=tk.W, pady=5)

        self.progress_bar = ttk.Progressbar(frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=10)

        ttk.Label(frame, text="操作详情:").pack(anchor=tk.W, pady=(5, 5))

        self.log_text = scrolledtext.ScrolledText(frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        self.close_btn = ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy,
                                   width=15, state=tk.DISABLED)
        self.close_btn.pack(side=tk.RIGHT)

    def show(self):
        self.progress_bar.start(20)
        thread = threading.Thread(target=self._run_organize)
        thread.daemon = True
        thread.start()
        self.dialog.wait_window()

    def _run_organize(self):
        def on_progress(op: FileOperation):
            self.dialog.after(0, lambda: self._add_log(op))

        result = self.engine.organize(
            target_dirs=self.dirs,
            dry_run=self.dry_run,
            recursive=self.recursive,
            on_progress=on_progress
        )

        self.dialog.after(0, lambda: self._on_complete(result))

    def _add_log(self, op: FileOperation):
        self.log_text.config(state=tk.NORMAL)
        status_icon = "✓" if op.status == "success" else ("⊙" if op.status == "dry_run" else "✗")
        line = f"{status_icon} [{op.operation_type}] {os.path.basename(op.source_path)}"
        if op.target_path:
            line += f" → {os.path.basename(op.target_path)}"
        if op.error_message:
            line += f" - {op.error_message}"
        self.log_text.insert(tk.END, line + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _on_complete(self, result):
        self.progress_bar.stop()
        self.progress_bar.configure(mode='determinate')
        self.progress_bar['value'] = 100

        if result["success"]:
            self.progress_var.set(
                f"完成! 扫描 {result['total_files']} 个文件, "
                f"匹配 {result['matched_files']} 个, "
                f"操作 {result['success_count']}/{result['operations_count']} 成功"
            )
        else:
            self.progress_var.set(f"错误: {result['message']}")

        self.close_btn.config(state=tk.NORMAL)


class HelpDialog:
    def __init__(self, parent):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("使用说明")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)

        text = scrolledtext.ScrolledText(self.dialog, wrap=tk.WORD, padx=15, pady=15)
        text.pack(fill=tk.BOTH, expand=True)

        help_content = """
文件自动整理工具 - 使用说明
================================

1. 快速开始
   - 点击"添加目录"选择要整理的文件夹
   - 在"规则"菜单中选择模板或创建自定义规则
   - 勾选"干跑模式"可先预览效果
   - 点击"开始整理"执行操作

2. 规则管理
   - 支持创建多条规则，按优先级从高到低匹配
   - 每条规则可设置多个条件，支持 AND/OR/NOT 逻辑
   - 支持的条件类型：
     * 后缀名 (extension)
     * 文件名关键词 (filename_keyword)
     * 文件大小 (file_size_min/max)
     * 修改/创建日期 (date_modified/date_created)
     * 正则表达式 (regex)
     * 文件类型 (file_type)

3. 操作类型
   - 移动 (move): 将文件移动到指定文件夹
   - 重命名 (rename): 重命名文件
   - 复制 (copy): 复制文件到指定位置
   - 备份 (backup): 创建文件备份
   - 压缩 (zip): 将文件压缩为ZIP格式

4. 模板功能
   - 内置5套常用规则模板
   - 模板参数可自定义调整
   - 应用模板后生成的规则可进一步编辑

5. 安全机制
   - 同名文件自动添加序号避免覆盖
   - 干跑模式可预览所有操作
   - 支持撤销最近一次操作
   - 所有操作记录保存到数据库

6. 命令行使用
   - 整理文件: file-organizer organize <目录>
   - 干跑模式: file-organizer organize --dry-run <目录>
   - 撤销操作: file-organizer undo
   - 查看规则: file-organizer rules list
        """

        text.insert(1.0, help_content)
        text.config(state=tk.DISABLED)

        ttk.Button(self.dialog, text="关闭", command=self.dialog.destroy,
                  width=15).pack(pady=10)


class SmartAnalyzeDialog:
    def __init__(self, parent, engine: SmartRecommenderEngine,
                 selected_dirs: List[str], on_result=None):
        self.engine = engine
        self.selected_dirs = selected_dirs
        self.on_result = on_result
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("智能推荐分析")
        self.dialog.geometry("1000x700")
        self.dialog.minsize(900, 600)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

        if self.selected_dirs:
            self._start_analysis(self.selected_dirs[0])

    def _create_widgets(self):
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(main_frame)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header, text="智能推荐分析", style="Title.TLabel").pack(side=tk.LEFT)

        dir_frame = ttk.Frame(main_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(dir_frame, text="分析目录:").pack(side=tk.LEFT)
        self.dir_var = tk.StringVar()
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=60)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="浏览...", command=self._browse_dir, width=8).pack(side=tk.LEFT)
        self.analyze_btn = ttk.Button(dir_frame, text="开始分析",
                                      command=self._on_analyze_click, width=10)
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.StringVar(value="请选择要分析的目录")
        ttk.Label(main_frame, textvariable=self.progress_var,
                 foreground="gray").pack(anchor=tk.W, pady=(0, 5))

        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self._create_recommendations_tab()
        self._create_structure_tab()
        self._create_naming_tab()
        self._create_modules_tab()
        self._create_stats_tab()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="导出报告", command=self._export_report,
                  width=12).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="应用推荐规则", command=self._apply_rules,
                  width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy,
                  width=12).pack(side=tk.RIGHT)

    def _create_recommendations_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="推荐建议")

        filter_frame = ttk.Frame(tab)
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(filter_frame, text="筛选:").pack(side=tk.LEFT)
        self.severity_var = tk.StringVar(value="全部")
        severity_combo = ttk.Combobox(filter_frame, textvariable=self.severity_var,
                                     state="readonly", width=10)
        severity_combo['values'] = ["全部", "critical", "high", "warning", "info", "suggestion"]
        severity_combo.pack(side=tk.LEFT, padx=5)
        severity_combo.bind('<<ComboboxSelected>>', lambda e: self._refresh_recommendations())

        columns = ("severity", "category", "title")
        self.rec_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)
        self.rec_tree.heading("severity", text="级别")
        self.rec_tree.heading("category", text="分类")
        self.rec_tree.heading("title", text="标题")
        self.rec_tree.column("severity", width=80, anchor=tk.CENTER)
        self.rec_tree.column("category", width=100, anchor=tk.CENTER)
        self.rec_tree.column("title", width=500)
        self.rec_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        rec_scroll = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.rec_tree.yview)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.rec_tree.configure(yscrollcommand=rec_scroll.set)
        self.rec_tree.bind('<<TreeviewSelect>>', self._on_rec_select)

        self.rec_detail = scrolledtext.ScrolledText(tab, height=8, wrap=tk.WORD)
        self.rec_detail.pack(fill=tk.X, pady=(10, 0))

    def _create_structure_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="结构对比")

        paned = ttk.Panedwindow(tab, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left = ttk.LabelFrame(paned, text="当前结构", padding="10")
        paned.add(left, weight=1)
        self.current_tree = ttk.Treeview(left, show="tree")
        self.current_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        cur_scroll = ttk.Scrollbar(left, orient=tk.VERTICAL, command=self.current_tree.yview)
        cur_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.current_tree.configure(yscrollcommand=cur_scroll.set)

        right = ttk.LabelFrame(paned, text="推荐结构", padding="10")
        paned.add(right, weight=1)
        self.recommended_tree = ttk.Treeview(right, show="tree")
        self.recommended_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        rec_scroll = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.recommended_tree.yview)
        rec_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.recommended_tree.configure(yscrollcommand=rec_scroll.set)

        self.structure_summary = ttk.Label(tab, text="", foreground="gray")
        self.structure_summary.pack(anchor=tk.W, pady=(10, 0))

        mapping_frame = ttk.LabelFrame(tab, text="文件移动映射", padding="10")
        mapping_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        map_columns = ("source", "target", "action")
        self.mapping_tree = ttk.Treeview(mapping_frame, columns=map_columns, show="headings", height=6)
        self.mapping_tree.heading("source", text="源路径")
        self.mapping_tree.heading("target", text="目标路径")
        self.mapping_tree.heading("action", text="操作")
        self.mapping_tree.column("source", width=350)
        self.mapping_tree.column("target", width=350)
        self.mapping_tree.column("action", width=80, anchor=tk.CENTER)
        self.mapping_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        map_scroll = ttk.Scrollbar(mapping_frame, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        map_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapping_tree.configure(yscrollcommand=map_scroll.set)

    def _create_naming_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="命名规范")

        self.naming_info = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=30)
        self.naming_info.pack(fill=tk.BOTH, expand=True)

    def _create_modules_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="模块边界")

        columns = ("name", "files", "internal", "external", "cohesion")
        self.module_tree = ttk.Treeview(tab, columns=columns, show="headings", height=10)
        self.module_tree.heading("name", text="模块名")
        self.module_tree.heading("files", text="文件数")
        self.module_tree.heading("internal", text="内部依赖")
        self.module_tree.heading("external", text="外部依赖")
        self.module_tree.heading("cohesion", text="内聚度")
        self.module_tree.column("name", width=200)
        self.module_tree.column("files", width=80, anchor=tk.CENTER)
        self.module_tree.column("internal", width=80, anchor=tk.CENTER)
        self.module_tree.column("external", width=80, anchor=tk.CENTER)
        self.module_tree.column("cohesion", width=100, anchor=tk.CENTER)
        self.module_tree.pack(fill=tk.BOTH, expand=True)

        self.module_detail = scrolledtext.ScrolledText(tab, height=10, wrap=tk.WORD)
        self.module_detail.pack(fill=tk.X, pady=(10, 0))

    def _create_stats_tab(self):
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="统计信息")

        self.stats_text = scrolledtext.ScrolledText(tab, wrap=tk.WORD, height=30)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

    def _browse_dir(self):
        directory = filedialog.askdirectory(title="选择要分析的目录")
        if directory:
            self.dir_var.set(directory)

    def _on_analyze_click(self):
        target = self.dir_var.get().strip()
        if not target:
            messagebox.showinfo("提示", "请先选择要分析的目录")
            return
        if not os.path.isdir(target):
            messagebox.showerror("错误", "目录不存在")
            return
        self._start_analysis(target)

    def _start_analysis(self, target_dir: str):
        self.dir_var.set(target_dir)
        self.analyze_btn.config(state=tk.DISABLED)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))
        self.progress_bar.start(20)
        self.progress_var.set("分析中...")

        def run():
            def on_progress(msg):
                self.dialog.after(0, lambda: self.progress_var.set(msg))

            try:
                result = self.engine.analyze(target_dir, on_progress=on_progress)
                self.dialog.after(0, lambda: self._on_analysis_done(result))
            except Exception as e:
                self.dialog.after(0, lambda: self._on_analysis_error(str(e)))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def _on_analysis_done(self, result):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.analyze_btn.config(state=tk.NORMAL)
        self.result = result
        if self.on_result:
            self.on_result(result)

        self._populate_recommendations()
        self._populate_structure()
        self._populate_naming()
        self._populate_modules()
        self._populate_stats()

        rec_count = len(result.recommendation_result.recommendations)
        if result.is_incremental and result.incremental_diff:
            changes = result.incremental_diff.summary
            self.progress_var.set(
                f"增量分析完成 - 新增: {changes.get('added', 0)}, "
                f"修改: {changes.get('modified', 0)}, "
                f"删除: {changes.get('removed', 0)}, "
                f"共 {rec_count} 条推荐"
            )
        else:
            self.progress_var.set(f"分析完成 - 生成 {rec_count} 条推荐建议")

    def _on_analysis_error(self, error_msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.analyze_btn.config(state=tk.NORMAL)
        self.progress_var.set(f"分析失败: {error_msg}")
        messagebox.showerror("错误", f"分析失败: {error_msg}")

    def _refresh_recommendations(self):
        self._populate_recommendations()

    def _populate_recommendations(self):
        for item in self.rec_tree.get_children():
            self.rec_tree.delete(item)

        if not self.result:
            return

        filter_sev = self.severity_var.get()
        severity_icons = {
            "critical": "🔴 critical",
            "high": "🟠 high",
            "warning": "🟡 warning",
            "info": "🔵 info",
            "suggestion": "⚪ suggestion",
        }

        for rec in self.result.recommendation_result.recommendations:
            if filter_sev != "全部" and rec.severity != filter_sev:
                continue
            self.rec_tree.insert("", tk.END, iid=rec.id, values=(
                severity_icons.get(rec.severity, rec.severity),
                rec.category,
                rec.title,
            ))

    def _on_rec_select(self, event):
        selection = self.rec_tree.selection()
        if not selection or not self.result:
            return

        rec_id = selection[0]
        rec = next((r for r in self.result.recommendation_result.recommendations
                    if r.id == rec_id), None)
        if not rec:
            return

        self.rec_detail.config(state=tk.NORMAL)
        self.rec_detail.delete(1.0, tk.END)

        text = f"【{rec.title}】\n\n"
        text += f"描述: {rec.description}\n\n"
        if rec.rationale:
            text += f"理由: {rec.rationale}\n\n"
        if rec.best_practice:
            text += f"最佳实践: {rec.best_practice}\n\n"
        if rec.affected_files:
            text += f"受影响文件 ({len(rec.affected_files)} 个):\n"
            for f in rec.affected_files[:15]:
                text += f"  - {f}\n"
            if len(rec.affected_files) > 15:
                text += f"  ... 等 {len(rec.affected_files)} 个文件\n"

        self.rec_detail.insert(1.0, text)
        self.rec_detail.config(state=tk.DISABLED)

    def _populate_structure(self):
        for item in self.current_tree.get_children():
            self.current_tree.delete(item)
        for item in self.recommended_tree.get_children():
            self.recommended_tree.delete(item)
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)

        if not self.result:
            return

        comparison = self.engine.get_structure_comparison(self.result)

        self._build_tree_view(self.current_tree, "", comparison["current_tree"])

        rec_root = self.recommended_tree.insert("", tk.END,
            text=os.path.basename(comparison["root_path"]), open=True)
        for d in comparison["recommended_directories"]:
            self._add_dir_tree(self.recommended_tree, rec_root, d)

        for m in comparison["file_mappings"]:
            self.mapping_tree.insert("", tk.END, values=(
                m["source_display"],
                m["target_display"],
                m["action"],
            ))

        stats = comparison["stats"]
        summary = comparison["summary"]
        self.structure_summary.config(
            text=f"统计: {stats['total_files']} 个文件, {stats['total_dirs']} 个目录, "
                 f"总大小: {self._format_size(stats['total_size'])} | "
                 f"建议移动: {summary.get('total_files_to_move', 0)} 个文件, "
                 f"新建目录: {len(summary.get('new_directories', []))} 个"
        )

    def _add_dir_tree(self, tree, parent, path):
        parts = path.split("/")
        current = parent
        for part in parts:
            children = tree.get_children(current)
            found = None
            for c in children:
                if tree.item(c, "text") == part:
                    found = c
                    break
            if found is None:
                current = tree.insert(current, tk.END, text=part + "/", open=True)
            else:
                current = found

    def _build_tree_view(self, tree, parent, node):
        if not node:
            return
        name = node.get("name", "")
        if node.get("is_dir", False):
            name += "/"
        display = name
        if node.get("truncated_children", 0) > 0:
            display += f" ...(+{node['truncated_children']})"
        item = tree.insert(parent, tk.END, text=display, open=(node.get("depth", 0) < 2))
        for child in node.get("children", []):
            self._build_tree_view(tree, item, child)

    def _populate_naming(self):
        self.naming_info.config(state=tk.NORMAL)
        self.naming_info.delete(1.0, tk.END)

        if not self.result:
            return

        nc = self.result.recommendation_result.naming_convention
        current = nc.get("current_state", {})

        text = "=== 命名规范分析 ===\n\n"
        text += "【当前状态】\n"
        text += f"  主流命名风格: {current.get('dominant_pattern', 'N/A')}\n"
        text += f"  一致性评分: {current.get('consistency_score', 0):.0%}\n\n"

        patterns = current.get("pattern_distribution", {})
        if patterns:
            text += "【各风格文件数量】\n"
            for pat, count in sorted(patterns.items(), key=lambda x: -x[1]):
                text += f"  {pat}: {count}\n"
            text += "\n"

        recs = nc.get("recommendations", {})
        if recs:
            text += "【推荐规范】\n"
            for lang, rules in recs.items():
                if lang.startswith("_"):
                    continue
                text += f"\n  {lang}:\n"
                for k, v in rules.items():
                    text += f"    {k}: {v}\n"

        self.naming_info.insert(1.0, text)
        self.naming_info.config(state=tk.DISABLED)

    def _populate_modules(self):
        for item in self.module_tree.get_children():
            self.module_tree.delete(item)

        if not self.result:
            return

        for mod in self.result.recommendation_result.module_boundaries:
            self.module_tree.insert("", tk.END, iid=mod["id"], values=(
                mod.get("name", "Unknown"),
                mod.get("file_count", 0),
                mod.get("internal_dependencies", 0),
                mod.get("external_dependencies", 0),
                f"{mod.get('cohesion_score', 0):.0%}",
            ))

    def _populate_stats(self):
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)

        if not self.result:
            return

        stats = self.result.recommendation_result.statistics
        scan = self.result.scan_result

        text = "=== 项目分析统计 ===\n\n"
        scanned = stats.get("total_scanned", {})
        text += "【概览】\n"
        text += f"  扫描目录: {scan.root_path}\n"
        text += f"  扫描时间: {scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += f"  总文件数: {scanned.get('files', 0)}\n"
        text += f"  总目录数: {scanned.get('directories', 0)}\n"
        text += f"  总大小: {self._format_size(scanned.get('total_size_bytes', 0))}\n"
        text += f"  最大嵌套深度: {scanned.get('max_depth', 0)}\n"
        text += f"  平均每目录文件数: {scanned.get('avg_files_per_dir', 0)}\n\n"

        dist = stats.get("distribution", {})
        cats = dist.get("by_category", {})
        if cats:
            text += "【按类型分布】\n"
            for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
                pct = count / max(scanned.get('files', 1), 1) * 100
                text += f"  {cat}: {count} ({pct:.1f}%)\n"
            text += "\n"

        exts = dist.get("by_extension", {})
        if exts:
            text += "【Top 扩展名】\n"
            for ext, count in list(exts.items())[:15]:
                text += f"  .{ext}: {count}\n"
            text += "\n"

        sizes = dist.get("by_size_bucket", {})
        if sizes:
            text += "【按大小分布】\n"
            for bucket, count in sizes.items():
                text += f"  {bucket}: {count}\n"
            text += "\n"

        rec_stats = stats.get("recommendations", {})
        text += "【推荐统计】\n"
        text += f"  总建议数: {rec_stats.get('total', 0)}\n"
        by_sev = rec_stats.get("by_severity", {})
        for sev, count in by_sev.items():
            text += f"    {sev}: {count}\n"

        text += f"\n  检测模块数: {stats.get('modules_detected', 0)}\n"
        text += f"  异常数: {stats.get('anomalies', 0)}\n"

        self.stats_text.insert(1.0, text)
        self.stats_text.config(state=tk.DISABLED)

    def _export_report(self):
        if not self.result:
            messagebox.showinfo("提示", "请先完成分析")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出推荐报告",
            defaultextension=".md",
            filetypes=[
                ("Markdown 报告", "*.md"),
                ("JSON 格式", "*.json"),
                ("YAML 格式", "*.yaml"),
                ("所有文件", "*.*"),
            ],
            initialfile="file_organizer_recommendations"
        )
        if not file_path:
            return

        try:
            self.engine.export(self.result.recommendation_result, file_path)
            messagebox.showinfo("成功", f"报告已导出到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {e}")

    def _apply_rules(self):
        if not self.result:
            messagebox.showinfo("提示", "请先完成分析")
            return

        rules = self.result.recommendation_result.generated_rules
        if not rules:
            messagebox.showinfo("提示", "没有可应用的规则")
            return

        if messagebox.askyesno("确认", f"确定要应用 {len(rules)} 条推荐规则吗？"):
            try:
                rule_ids = self.engine.apply_generated_rules(self.result.recommendation_result)
                messagebox.showinfo("成功", f"已应用 {len(rule_ids)} 条规则\n请在规则管理中查看")
            except Exception as e:
                messagebox.showerror("错误", f"应用失败: {e}")

    def _format_size(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / 1024 / 1024:.1f} MB"
        else:
            return f"{size_bytes / 1024 / 1024 / 1024:.1f} GB"


def main():
    root = tk.Tk()
    app = FileOrganizerApp(root)
    app.run()


if __name__ == "__main__":
    main()
