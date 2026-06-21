from typing import Dict, List, Any


class TemplateManager:
    @staticmethod
    def get_all_templates() -> List[Dict[str, Any]]:
        return [
            TemplateManager._get_extension_template(),
            TemplateManager._get_photo_archive_template(),
            TemplateManager._get_temp_cleanup_template(),
            TemplateManager._get_music_organize_template(),
            TemplateManager._get_downloads_organize_template(),
        ]

    @staticmethod
    def get_template(template_id: str) -> Dict[str, Any]:
        templates = {
            "extension_sort": TemplateManager._get_extension_template(),
            "photo_archive": TemplateManager._get_photo_archive_template(),
            "temp_cleanup": TemplateManager._get_temp_cleanup_template(),
            "music_organize": TemplateManager._get_music_organize_template(),
            "downloads_organize": TemplateManager._get_downloads_organize_template(),
        }
        return templates.get(template_id)

    @staticmethod
    def _get_extension_template() -> Dict[str, Any]:
        return {
            "id": "extension_sort",
            "name": "按后缀名分类到子文件夹",
            "description": "根据文件扩展名自动创建分类文件夹，并将文件移动到对应文件夹中",
            "category": "分类整理",
            "icon": "📁",
            "configurable": True,
            "params": [
                {
                    "name": "target_dir",
                    "label": "目标文件夹",
                    "type": "text",
                    "default": "",
                    "description": "整理后的文件存放目录，留空则在原目录下创建子文件夹"
                },
                {
                    "name": "extensions",
                    "label": "包含的扩展名",
                    "type": "text",
                    "default": "",
                    "description": "逗号分隔，留空表示所有文件"
                }
            ],
            "generate_rules": TemplateManager._generate_extension_rules
        }

    @staticmethod
    def _generate_extension_rules(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        target_base = params.get("target_dir", "")
        extensions_input = params.get("extensions", "")

        categories = [
            ("图片", "jpg,jpeg,png,gif,bmp,webp,svg,ico", "Images"),
            ("文档", "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,rtf,odt,ods,odp,md", "Documents"),
            ("视频", "mp4,avi,mkv,mov,wmv,flv,webm,m4v", "Videos"),
            ("音频", "mp3,wav,flac,aac,ogg,wma,m4a,aiff", "Audio"),
            ("压缩包", "zip,rar,7z,tar,gz,bz2,xz", "Archives"),
            ("代码", "py,js,ts,java,c,cpp,h,hpp,cs,go,rb,php,html,css,json,xml,yaml,yml", "Code"),
        ]

        rules = []
        for i, (name, exts, folder) in enumerate(categories):
            if extensions_input:
                input_exts = set(e.strip().lower().lstrip(".") for e in extensions_input.split(","))
                cat_exts = set(e.strip().lower() for e in exts.split(","))
                if not input_exts & cat_exts:
                    continue

            rule = {
                "name": f"按后缀分类 - {name}",
                "description": f"将{name}文件移动到{folder}文件夹",
                "priority": 10 - i,
                "enabled": True,
                "logic_operator": "AND",
                "conditions": [
                    {
                        "condition_type": "extension",
                        "condition_value": exts,
                        "negate": False,
                        "sort_order": 0
                    }
                ],
                "actions": [
                    {
                        "action_type": "move",
                        "action_params": {
                            "target_dir": target_base + folder if target_base else folder,
                            "new_name": ""
                        },
                        "sort_order": 0
                    }
                ]
            }
            rules.append(rule)

        return rules

    @staticmethod
    def _get_photo_archive_template() -> Dict[str, Any]:
        return {
            "id": "photo_archive",
            "name": "按月份归档照片",
            "description": "根据照片的拍摄或修改日期，按年份/月份结构归档照片文件",
            "category": "照片管理",
            "icon": "📸",
            "configurable": True,
            "params": [
                {
                    "name": "target_dir",
                    "label": "归档根目录",
                    "type": "text",
                    "default": "",
                    "description": "归档的根目录，留空则在原目录下归档"
                },
                {
                    "name": "date_source",
                    "label": "日期来源",
                    "type": "select",
                    "options": [
                        {"value": "modified", "label": "修改日期"},
                        {"value": "created", "label": "创建日期"}
                    ],
                    "default": "modified",
                    "description": "使用哪个日期进行归档"
                },
                {
                    "name": "structure",
                    "label": "目录结构",
                    "type": "select",
                    "options": [
                        {"value": "year_month", "label": "年/月 (2024/01)"},
                        {"value": "year_month_day", "label": "年/月/日 (2024/01/15)"},
                        {"value": "year_month_name", "label": "年-月 (2024-01)"}
                    ],
                    "default": "year_month",
                    "description": "归档的目录结构"
                }
            ],
            "generate_rules": TemplateManager._generate_photo_archive_rules
        }

    @staticmethod
    def _generate_photo_archive_rules(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        target_base = params.get("target_dir", "")
        date_source = params.get("date_source", "modified")
        structure = params.get("structure", "year_month")

        if structure == "year_month":
            path_template = "{modified_year}/{modified_month}"
        elif structure == "year_month_day":
            path_template = "{modified_year}/{modified_month}/{modified_day}"
        else:
            path_template = "{modified_year}-{modified_month}"

        if date_source == "created":
            path_template = path_template.replace("modified", "created")

        if target_base:
            full_target = target_base.rstrip("/") + "/" + path_template
        else:
            full_target = path_template

        rule = {
            "name": "按月份归档照片",
            "description": "将照片文件按日期归档",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {
                    "condition_type": "file_type",
                    "condition_value": "image",
                    "negate": False,
                    "sort_order": 0
                }
            ],
            "actions": [
                {
                    "action_type": "move",
                    "action_params": {
                        "target_dir": full_target,
                        "new_name": ""
                    },
                    "sort_order": 0
                }
            ]
        }

        return [rule]

    @staticmethod
    def _get_temp_cleanup_template() -> Dict[str, Any]:
        return {
            "id": "temp_cleanup",
            "name": "清理临时文件",
            "description": "识别并清理临时文件、日志文件和缓存文件",
            "category": "清理优化",
            "icon": "🧹",
            "configurable": True,
            "params": [
                {
                    "name": "action",
                    "label": "处理方式",
                    "type": "select",
                    "options": [
                        {"value": "zip", "label": "压缩为ZIP"},
                        {"value": "backup", "label": "创建备份"},
                        {"value": "move", "label": "移动到指定文件夹"}
                    ],
                    "default": "zip",
                    "description": "对临时文件的处理方式"
                },
                {
                    "name": "target_dir",
                    "label": "目标文件夹",
                    "type": "text",
                    "default": "temp_files",
                    "description": "移动或压缩的目标位置"
                },
                {
                    "name": "older_than",
                    "label": "仅清理早于",
                    "type": "text",
                    "default": "30d",
                    "description": "只清理修改日期早于指定时间的文件，如 30d 表示30天前"
                }
            ],
            "generate_rules": TemplateManager._generate_temp_cleanup_rules
        }

    @staticmethod
    def _generate_temp_cleanup_rules(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        action = params.get("action", "zip")
        target_dir = params.get("target_dir", "temp_files")
        older_than = params.get("older_than", "30d")

        conditions = [
            {
                "condition_type": "extension",
                "condition_value": "tmp,log,crdownload,part,dat,bak,old,temp,cache",
                "negate": False,
                "sort_order": 0
            }
        ]

        if older_than:
            conditions.append({
                "condition_type": "date_modified_to",
                "condition_value": older_than,
                "negate": False,
                "sort_order": 1
            })

        if action == "zip":
            action_config = {
                "action_type": "zip",
                "action_params": {
                    "target_dir": target_dir,
                    "zip_name": "",
                    "delete_original": True
                },
                "sort_order": 0
            }
        elif action == "backup":
            action_config = {
                "action_type": "backup",
                "action_params": {
                    "backup_dir": target_dir
                },
                "sort_order": 0
            }
        else:
            action_config = {
                "action_type": "move",
                "action_params": {
                    "target_dir": target_dir,
                    "new_name": ""
                },
                "sort_order": 0
            }

        rule = {
            "name": "清理临时文件",
            "description": "清理临时文件和日志文件",
            "priority": 5,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": conditions,
            "actions": [action_config]
        }

        return [rule]

    @staticmethod
    def _get_music_organize_template() -> Dict[str, Any]:
        return {
            "id": "music_organize",
            "name": "音乐按艺术家整理",
            "description": "读取音乐文件元数据，按艺术家/专辑结构整理音乐文件",
            "category": "音乐管理",
            "icon": "🎵",
            "configurable": True,
            "params": [
                {
                    "name": "target_dir",
                    "label": "音乐根目录",
                    "type": "text",
                    "default": "",
                    "description": "整理后的音乐存放目录，留空则在原目录下整理"
                },
                {
                    "name": "structure",
                    "label": "目录结构",
                    "type": "select",
                    "options": [
                        {"value": "artist/album", "label": "艺术家/专辑"},
                        {"value": "artist", "label": "仅艺术家"},
                        {"value": "genre/artist/album", "label": "流派/艺术家/专辑"}
                    ],
                    "default": "artist/album",
                    "description": "音乐文件的目录结构"
                },
                {
                    "name": "fallback",
                    "label": "无元数据时",
                    "type": "select",
                    "options": [
                        {"value": "unknown", "label": "放入 Unknown 文件夹"},
                        {"value": "skip", "label": "跳过不处理"}
                    ],
                    "default": "unknown",
                    "description": "当音乐文件没有元数据时的处理方式"
                }
            ],
            "generate_rules": TemplateManager._generate_music_organize_rules
        }

    @staticmethod
    def _generate_music_organize_rules(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        target_base = params.get("target_dir", "")

        rule = {
            "name": "音乐按艺术家整理",
            "description": "整理音乐文件到艺术家/专辑目录",
            "priority": 10,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [
                {
                    "condition_type": "file_type",
                    "condition_value": "audio",
                    "negate": False,
                    "sort_order": 0
                }
            ],
            "actions": [
                {
                    "action_type": "move",
                    "action_params": {
                        "target_dir": target_base + "Music/{artist}/{album}" if target_base else "Music/{artist}/{album}",
                        "new_name": ""
                    },
                    "sort_order": 0
                }
            ],
            "metadata": {
                "template_type": "music",
                "requires_metadata": True
            }
        }

        return [rule]

    @staticmethod
    def _get_downloads_organize_template() -> Dict[str, Any]:
        return {
            "id": "downloads_organize",
            "name": "下载目录自动整理",
            "description": "按文件类型自动分类下载文件夹中的内容",
            "category": "分类整理",
            "icon": "⬇️",
            "configurable": True,
            "params": [
                {
                    "name": "target_dir",
                    "label": "目标目录",
                    "type": "text",
                    "default": "",
                    "description": "整理后的文件存放目录，留空则在下载目录内分类"
                },
                {
                    "name": "categories",
                    "label": "分类方式",
                    "type": "select",
                    "options": [
                        {"value": "simple", "label": "简单分类（图片/文档/视频/其他）"},
                        {"value": "detailed", "label": "详细分类（10+分类）"}
                    ],
                    "default": "simple",
                    "description": "分类的详细程度"
                }
            ],
            "generate_rules": TemplateManager._generate_downloads_organize_rules
        }

    @staticmethod
    def _generate_downloads_organize_rules(params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        params = params or {}
        target_base = params.get("target_dir", "")
        categories_mode = params.get("categories", "simple")

        if categories_mode == "simple":
            categories = [
                ("图片", "jpg,jpeg,png,gif,bmp,webp,svg", "图片", 50),
                ("文档", "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,md", "文档", 40),
                ("视频", "mp4,avi,mkv,mov,wmv,flv,webm", "视频", 30),
                ("音频", "mp3,wav,flac,aac,ogg,m4a", "音乐", 20),
                ("压缩包", "zip,rar,7z,tar,gz", "压缩包", 10),
            ]
        else:
            categories = [
                ("图片", "jpg,jpeg,png,gif,bmp,webp,svg,ico", "图片", 60),
                ("文档", "pdf,doc,docx,xls,xlsx,ppt,pptx,txt,rtf,md", "文档", 50),
                ("视频", "mp4,avi,mkv,mov,wmv,flv,webm,m4v", "视频", 40),
                ("音乐", "mp3,wav,flac,aac,ogg,wma,m4a", "音乐", 30),
                ("软件安装包", "exe,msi,dmg,pkg,deb,rpm,apk", "软件", 25),
                ("压缩包", "zip,rar,7z,tar,gz,bz2,xz", "压缩包", 20),
                ("代码", "py,js,ts,java,c,cpp,html,css,json,xml", "代码", 15),
                ("电子书", "epub,mobi,azw3,pdf", "电子书", 10),
            ]

        rules = []
        for name, exts, folder, priority in categories:
            rule = {
                "name": f"下载分类 - {name}",
                "description": f"将{name}移动到{folder}文件夹",
                "priority": priority,
                "enabled": True,
                "logic_operator": "AND",
                "conditions": [
                    {
                        "condition_type": "extension",
                        "condition_value": exts,
                        "negate": False,
                        "sort_order": 0
                    }
                ],
                "actions": [
                    {
                        "action_type": "move",
                        "action_params": {
                            "target_dir": target_base + folder if target_base else folder,
                            "new_name": ""
                        },
                        "sort_order": 0
                    }
                ]
            }
            rules.append(rule)

        other_rule = {
            "name": "下载分类 - 其他",
            "description": "将其他文件移动到其他文件夹",
            "priority": 1,
            "enabled": True,
            "logic_operator": "AND",
            "conditions": [],
            "actions": [
                {
                    "action_type": "move",
                    "action_params": {
                        "target_dir": target_base + "其他" if target_base else "其他",
                        "new_name": ""
                    },
                    "sort_order": 0
                }
            ]
        }
        rules.append(other_rule)

        return rules

    @staticmethod
    def apply_template(db, template_id: str, params: Dict[str, Any] = None) -> List[int]:
        template = TemplateManager.get_template(template_id)
        if not template:
            return []

        generate_func = template.get("generate_rules")
        if not generate_func:
            return []

        rules = generate_func(params or {})
        rule_ids = []
        for rule_data in rules:
            rule_id = db.save_rule_complete(rule_data)
            rule_ids.append(rule_id)

        return rule_ids
