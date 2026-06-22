"""
情感分析模块 - 支持中文/英文文本的正负面情感分类
输出：二元分类（正面/负面）+ 0-1置信度评分
"""
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class SentimentResult:
    """情感分析结果"""
    sentiment: str
    confidence: float
    positive_score: float
    negative_score: float
    details: Dict = None


class SentimentAnalyzer:
    """情感分析器 - 多模型融合策略（词典+规则+snownlp+句式模式）"""

    def __init__(self):
        self._init_sentiment_dictionaries()
        self._init_emoji_dictionary()
        self._init_intensifiers()
        self._init_negations()
        self._init_special_patterns()
        self._init_snownlp()

    def _init_snownlp(self):
        """初始化snownlp中文情感分析"""
        self.snownlp_available = False
        try:
            from snownlp import SnowNLP
            self.SnowNLP = SnowNLP
            self.snownlp_available = True
        except ImportError:
            self.snownlp_available = False

    def _init_sentiment_dictionaries(self):
        """初始化情感词典（按强度加权）"""
        self.chinese_positive = {
            '好': 1.0, '优秀': 1.0, '棒': 1.0, '赞': 1.0, '喜欢': 0.9, '满意': 0.9, '开心': 0.9,
            '高兴': 0.85, '快乐': 0.85, '幸福': 0.9, '美好': 0.9, '精彩': 0.9, '出色': 0.85,
            '卓越': 0.9, '完美': 0.95, '成功': 0.85, '胜利': 0.85, '厉害': 0.8, '牛': 0.8,
            '666': 0.8, '强': 0.8, '赞不绝口': 0.9, '好评': 0.85, '推荐': 0.85, '值得': 0.75,
            '划算': 0.7, '实惠': 0.7, '超值': 0.75, '方便': 0.75, '实用': 0.7, '舒适': 0.75,
            '美观': 0.7, '精致': 0.7, '高档': 0.7, '热情': 0.75, '周到': 0.75, '专业': 0.75,
            '负责': 0.75, '认真': 0.7, '耐心': 0.7, '积极': 0.7, '乐观': 0.7, '充满希望': 0.8,
            '感动': 0.8, '温暖': 0.75, '温馨': 0.75, '浪漫': 0.75, '惊喜': 0.8, '惊艳': 0.85,
            '过瘾': 0.7, '爽': 0.75, '治愈': 0.75, '给力': 0.85, '奥利给': 0.75, 'yyds': 0.95,
            '绝绝子': 0.9, '爱了': 0.85, '买它': 0.75, '冲': 0.75, '支持': 0.75, '感谢': 0.75,
            '感恩': 0.8, '珍惜': 0.7, '享受': 0.7, '期待': 0.65, '精彩绝伦': 0.95, '完美无缺': 0.95,
            '物美价廉': 0.8, '物超所值': 0.85, '事半功倍': 0.8, '精益求精': 0.85, '一丝不苟': 0.75,
            '无微不至': 0.8, '尽心尽力': 0.8, '任劳任怨': 0.75, '德高望重': 0.85, '才华横溢': 0.85,
            '出类拔萃': 0.85, '卓越不凡': 0.9, '无与伦比': 0.9, '首屈一指': 0.85, '名列前茅': 0.85,
            '独树一帜': 0.85, '匠心独运': 0.85, '巧夺天工': 0.85, '鬼斧神工': 0.85, '炉火纯青': 0.85,
            '登峰造极': 0.9, '叹为观止': 0.85, '心旷神怡': 0.8, '赏心悦目': 0.8, '爱不释手': 0.85,
            '流连忘返': 0.8, '记忆犹新': 0.7, '历历在目': 0.65, '刻骨铭心': 0.75, '永生难忘': 0.8,
            '振奋人心': 0.8, '鼓舞人心': 0.8, '激动人心': 0.8, '热血沸腾': 0.8, '心潮澎湃': 0.8,
            '欣喜若狂': 0.9, '喜出望外': 0.85, '兴高采烈': 0.85, '欢天喜地': 0.85, '喜气洋洋': 0.85,
            '春风得意': 0.8, '意气风发': 0.8, '斗志昂扬': 0.8, '朝气蓬勃': 0.8, '精神抖擞': 0.75,
            '神采奕奕': 0.75, '容光焕发': 0.75, '英姿飒爽': 0.75, '威风凛凛': 0.75, '器宇轩昂': 0.75,
            '收获': 0.7, '满满': 0.65, '收获满满': 0.85, '受益': 0.6, '受益匪浅': 0.85,
            '顺利': 0.7, '平安': 0.7, '成功': 0.85, '优秀': 0.9, '良好': 0.75, '出色': 0.85,
            'love': 0.9, 'like': 0.75, 'good': 0.75, 'great': 0.85, 'excellent': 0.9,
            'amazing': 0.9, 'awesome': 0.9, 'wonderful': 0.9, 'fantastic': 0.9,
            'perfect': 0.95, 'beautiful': 0.85, 'nice': 0.75, 'happy': 0.85, 'joyful': 0.85,
            'delightful': 0.85, 'pleased': 0.8, 'satisfied': 0.8, 'impressive': 0.85,
            'outstanding': 0.9, 'brilliant': 0.9, 'superb': 0.9, 'magnificent': 0.9,
            'splendid': 0.9, 'remarkable': 0.85, 'extraordinary': 0.9, 'incredible': 0.9,
            'gorgeous': 0.85, 'stunning': 0.85, 'breathtaking': 0.9, 'unforgettable': 0.85,
            'exceptional': 0.9, 'phenomenal': 0.9, 'sensational': 0.9, 'thrilling': 0.85,
            'heartwarming': 0.85, 'uplifting': 0.85, 'inspiring': 0.85, 'rewarding': 0.8,
            'fulfilling': 0.8, 'meaningful': 0.75, 'valuable': 0.75, 'worthwhile': 0.8,
            'affordable': 0.7, 'reliable': 0.75, 'durable': 0.75, 'comfortable': 0.75,
            'convenient': 0.75, 'efficient': 0.75, 'effective': 0.75, 'professional': 0.8,
            'friendly': 0.75, 'helpful': 0.75, 'courteous': 0.75, 'responsive': 0.75,
            'attentive': 0.75, 'generous': 0.75, 'thoughtful': 0.75, 'considerate': 0.75,
            'enjoyable': 0.8, 'pleasant': 0.75, 'positive': 0.75, 'nice': 0.75, 'best': 0.85,
            'recommend': 0.75, 'highly recommend': 0.9,
        }

        self.chinese_negative = {
            '差': -1.0, '烂': -1.0, '糟': -1.0, '垃圾': -1.0, '讨厌': -0.9, '失望': -0.85,
            '难过': -0.8, '伤心': -0.85, '痛苦': -0.9, '悲伤': -0.9, '愤怒': -0.85, '生气': -0.85,
            '恼火': -0.8, '可恶': -0.85, '可恨': -0.85, '糟糕': -0.9, '恶劣': -0.85, '低劣': -0.85,
            '差劲': -0.85, '失败': -0.85, '亏损': -0.75, '损失': -0.75, '昂贵': -0.7, '贵': -0.55,
            '不值': -0.8, '坑': -0.8, '骗': -0.9, '欺诈': -0.95, '虚假': -0.9, '骗人': -0.9,
            '拖延': -0.7, '慢': -0.55, '卡顿': -0.75, '死机': -0.85, '崩溃': -0.9, '故障': -0.8,
            '冷漠': -0.75, '敷衍': -0.8, '不负责任': -0.85, '不专业': -0.8, '粗鲁': -0.8,
            '恶劣态度': -0.85, '投诉': -0.85, '差评': -0.9, '不推荐': -0.85, '后悔': -0.8,
            '心疼': -0.75, '心碎': -0.9, '绝望': -0.95, '恐惧': -0.85, '害怕': -0.8, '担忧': -0.7,
            '焦虑': -0.75, '压力': -0.7, '疲劳': -0.6, '累': -0.6, '无聊': -0.7, '枯燥': -0.7,
            '乏味': -0.65, '郁闷': -0.75, '烦躁': -0.75, '无语': -0.65, '服了': -0.6, '醉了': -0.6,
            '垃圾产品': -0.95, '垃圾服务': -0.95, '糟糕透顶': -0.95, '一无是处': -0.95, '令人发指': -0.95,
            '罄竹难书': -0.95, '擢发难数': -0.9, '恶贯满盈': -0.95, '十恶不赦': -0.95, '丧尽天良': -0.95,
            '惨不忍睹': -0.95, '惨绝人寰': -0.95, '惨无人道': -0.95, '触目惊心': -0.85, '骇人听闻': -0.9,
            '毛骨悚然': -0.85, '不寒而栗': -0.85, '心惊肉跳': -0.8, '胆战心惊': -0.85, '提心吊胆': -0.8,
            '忧心忡忡': -0.8, '愁眉苦脸': -0.8, '垂头丧气': -0.8, '萎靡不振': -0.8, '无精打采': -0.75,
            '闷闷不乐': -0.75, '郁郁寡欢': -0.8, '黯然神伤': -0.85, '潸然泪下': -0.85, '泪如雨下': -0.85,
            '悲痛欲绝': -0.95, '痛不欲生': -0.95, '生不如死': -0.95, '万念俱灰': -0.95, '心灰意冷': -0.9,
            '大失所望': -0.9, '灰心丧气': -0.85, '黯然失色': -0.85, '得不偿失': -0.8, '因小失大': -0.75,
            '赔了夫人又折兵': -0.9, '偷鸡不成蚀把米': -0.85, '竹篮打水一场空': -0.85, '鸡飞蛋打': -0.85,
            '两败俱伤': -0.8, '玉石俱焚': -0.9, '同归于尽': -0.9, '鱼死网破': -0.9,
            '失望': -0.85, '遗憾': -0.65, '缺陷': -0.7, '问题': -0.5, '不足': -0.5, '错误': -0.7,
            'bug': -0.7, 'Bug': -0.7, 'BUG': -0.7, '翻车': -0.75, '拉胯': -0.75, '摆烂': -0.7,
            'bad': -0.8, 'terrible': -0.95, 'awful': -0.9, 'horrible': -0.95,
            'hate': -0.95, 'dislike': -0.8, 'disappointed': -0.9, 'sad': -0.85,
            'angry': -0.85, 'upset': -0.8, 'frustrated': -0.85, 'annoyed': -0.8,
            'disgusting': -0.9, 'vile': -0.9, 'dreadful': -0.9, 'abysmal': -0.95,
            'appalling': -0.9, 'atrocious': -0.9, 'deplorable': -0.85, 'lousy': -0.8,
            'poor': -0.7, 'inferior': -0.8, 'substandard': -0.8, 'unacceptable': -0.85,
            'unsatisfactory': -0.85, 'regret': -0.8, 'waste': -0.8, 'scam': -0.95,
            'fraud': -0.95, 'fake': -0.9, 'defective': -0.85, 'broken': -0.8,
            'pathetic': -0.85, 'pitiful': -0.8, 'ridiculous': -0.8, 'absurd': -0.75,
            'outrageous': -0.9, 'intolerable': -0.9, 'unbearable': -0.9, 'insufferable': -0.85,
            'mediocre': -0.7, 'subpar': -0.7, 'lackluster': -0.65, 'unremarkable': -0.6,
            'forgettable': -0.55, 'disappointing': -0.9, 'underwhelming': -0.75,
            'unreliable': -0.8, 'unstable': -0.75, 'inconsistent': -0.75, 'flawed': -0.75,
            'rude': -0.8, 'arrogant': -0.8, 'ignorant': -0.75, 'stupid': -0.8,
            'lazy': -0.75, 'careless': -0.75, 'negligent': -0.85, 'incompetent': -0.85,
        }

        self.negator_words = {'不', '没', '没有', '无', '非', '不是', '不要', '不能', '不会', '不可', '未曾', '未尝', '莫', '勿', '毋'}
        self.negation_prefixes = ['不', '没', '无', '非', '未', '莫', '勿']

    def _init_emoji_dictionary(self):
        """初始化表情符号词典"""
        self.emoji_sentiment = {
            '😊': 0.8, '😄': 0.85, '😃': 0.85, '😀': 0.8, '😁': 0.75, '😆': 0.8,
            '😅': 0.5, '🤣': 0.85, '😂': 0.8, '🙂': 0.6, '😉': 0.7, '😍': 0.9,
            '🥰': 0.9, '😘': 0.85, '😗': 0.75, '😙': 0.75, '😚': 0.75, '😋': 0.7,
            '😛': 0.65, '😜': 0.65, '🤪': 0.7, '😝': 0.65, '🤑': 0.6, '🤗': 0.8,
            '🤭': 0.6, '🤫': 0.4, '🤔': 0.3, '🤐': 0.4, '🤨': 0.3, '😐': 0.2,
            '😑': 0.1, '😶': 0.1, '😏': 0.4, '😒': -0.4, '🙄': -0.5, '😬': 0.3,
            '😮‍💨': -0.3, '🤥': -0.5, '😌': 0.6, '😔': -0.6, '😪': -0.3, '🤤': 0.5,
            '😴': -0.2, '😷': -0.5, '🤒': -0.6, '🤕': -0.6, '🤢': -0.7, '🤮': -0.8,
            '🤧': -0.6, '🥵': -0.4, '🥶': -0.4, '🥴': -0.5, '😵': -0.6, '😵‍💫': -0.6,
            '🤯': -0.7, '😕': -0.5, '😟': -0.6, '🙁': -0.5, '☹️': -0.6, '😮': 0.3,
            '😯': 0.3, '😲': 0.4, '😳': 0.3, '🥺': -0.3, '😦': -0.4, '😧': -0.5,
            '😨': -0.6, '😰': -0.6, '😥': -0.6, '😢': -0.7, '😭': -0.8, '😱': -0.7,
            '😖': -0.6, '😣': -0.6, '😞': -0.65, '😓': -0.5, '😩': -0.7, '😫': -0.75,
            '🥱': -0.3, '😤': -0.6, '😡': -0.8, '😠': -0.75, '🤬': -0.9, '😈': -0.5,
            '👿': -0.6, '💀': -0.5, '☠️': -0.7, '💩': -0.7, '🤡': -0.3, '👹': -0.6,
            '👺': -0.6, '👻': 0.3, '👽': 0.3, '👾': 0.3, '🤖': 0.3, '😺': 0.7,
            '😸': 0.7, '😹': 0.75, '😻': 0.8, '😼': 0.6, '😽': 0.7, '🙀': -0.5,
            '😿': -0.7, '😾': -0.6, '❤️': 0.85, '🧡': 0.8, '💛': 0.8, '💚': 0.8,
            '💙': 0.8, '💜': 0.8, '🖤': 0.5, '🤍': 0.6, '🤎': 0.6, '💔': -0.8,
            '❣️': 0.8, '💕': 0.85, '💞': 0.85, '💓': 0.85, '💗': 0.85, '💖': 0.85,
            '💘': 0.85, '💝': 0.85, '👍': 0.75, '👎': -0.75, '👏': 0.8, '🙌': 0.8,
            '🤝': 0.7, '🙏': 0.7, '💯': 0.85, '✅': 0.65, '❌': -0.65, '⭐': 0.75,
            '🌟': 0.8, '✨': 0.75, '🎉': 0.85, '🎊': 0.85, '🏆': 0.8, '🥇': 0.85,
            '💢': -0.7, '💥': -0.5, '🔥': 0.65, '💦': -0.3, '💨': 0.3,
            '<3': 0.8, '</3': -0.8, ':)': 0.75, ':(': -0.75, ':D': 0.85, 'XD': 0.8,
            ':-)': 0.75, ':-(': -0.75, ':-D': 0.85, ';\)': 0.65, ':P': 0.55, ':-P': 0.55,
            ':\'(': -0.75, ':\'-(': -0.8, ':-O': 0.35, ':O': 0.35, ':-|': 0.2,
        }

    def _init_intensifiers(self):
        """初始化程度副词"""
        self.intensifiers = {
            '非常': 1.8, '极其': 2.0, '极度': 2.0, '万分': 1.9, '分外': 1.6,
            '格外': 1.6, '特别': 1.7, '尤其': 1.7, '十分': 1.6, '相当': 1.5,
            '很': 1.5, '挺': 1.3, '蛮': 1.3, '够': 1.3, '太': 1.7,
            '更加': 1.5, '越发': 1.5, '越来越': 1.5, '加倍': 1.7, '尤为': 1.7,
            '最': 2.0, '顶': 1.7, '绝': 1.7, '极': 1.8, '超': 1.8,
            '巨': 1.7, '狂': 1.6, '暴': 1.6, '死': 1.5, '坏': 1.5,
            '真的': 1.4, '真的太': 1.8, '真的很': 1.6, '真的非常': 1.9,
            'so': 1.5, 'very': 1.6, 'extremely': 1.9, 'incredibly': 1.9,
            'absolutely': 1.8, 'totally': 1.6, 'completely': 1.7, 'utterly': 1.8,
            'highly': 1.7, 'greatly': 1.7, 'deeply': 1.6, 'strongly': 1.7,
            'most': 1.9, 'more': 1.4, 'less': 0.7, 'little': 0.6, 'bit': 0.7,
        }

    def _init_negations(self):
        """初始化否定词"""
        self.negations = {
            '不': -1.0, '没': -1.0, '没有': -1.0, '无': -1.0, '非': -1.0,
            '不是': -1.0, '不要': -1.0, '不能': -1.0, '不会': -1.0, '不可': -1.0,
            '未曾': -1.0, '未尝': -1.0, '莫': -1.0, '勿': -1.0, '毋': -1.0,
            '未必': -0.7, '不见得': -0.7, '不一定': -0.7, '很难': -0.8,
            '难以': -0.7, 'failed': -1.0, 'not': -1.0, "n't": -1.0,
            'no': -1.0, 'never': -1.0, 'none': -1.0, 'nobody': -1.0,
            'nothing': -1.0, 'neither': -1.0, 'nor': -1.0, 'nowhere': -1.0,
            'hardly': -0.8, 'scarcely': -0.8, 'barely': -0.8, 'rarely': -0.7,
            'seldom': -0.7, 'without': -1.0, 'lack': -0.7, 'missing': -0.7,
            'unable': -1.0, 'unlikely': -0.8, 'doubtful': -0.7,
        }

    def _init_special_patterns(self):
        """初始化特殊句式模式"""
        self.positive_patterns = [
            (r'(强烈|极力|重点|真心|特别|非常|超级|最|真的太|真的非常)(推荐|推|赞|支持|喜欢|满意)', 0.8),
            (r'(好评|点赞|打call|给力|奥利给|yyds|YYDS|666)', 0.85),
            (r'(物美价廉|物超所值|性价比高|划算|实惠|超值)', 0.8),
            (r'(五星好评|满分|五星|全五星)', 0.85),
            (r'(爱了|爱死|太爱|狂爱)', 0.85),
            (r'(必买|必入|必选|必看|必听|必去)', 0.8),
            (r'(神作|神级|神片|神曲|神颜)', 0.85),
            (r'(天花板|yyds|永远的神)', 0.85),
            (r'(收获满满|受益匪浅|大开眼界)', 0.8),
            (r'(非常精彩|十分精彩|特别精彩|精彩绝伦)', 0.85),
            (r'(非常优秀|十分优秀|特别优秀|极其优秀)', 0.85),
            (r'(非常满意|十分满意|特别满意)', 0.8),
            (r'(非常专业|十分专业|特别专业)', 0.8),
            (r'(体验.*?(好|棒|赞|佳|优秀|不错)|非常.*?精彩|非常.*?优秀)', 0.7),
            (r'(非常.*?美丽|非常.*?美好|非常.*?温暖|非常.*?温馨)', 0.8),
            (r'(收获.*?(满满|很多|颇丰)|受益匪浅)', 0.75),
        ]

        self.negative_patterns = [
            (r'(千万不要|千万别|别买|别入|别去|别看|别听)', -0.85),
            (r'(垃圾|辣鸡|lj|LJ|乐色)', -0.85),
            (r'(差评|一星|负分|零分)', -0.85),
            (r'(坑|坑爹|坑人|被骗|被坑|上当)', -0.85),
            (r'(后悔|悔不当初|肠子都悔青了)', -0.8),
            (r'(垃圾产品|垃圾服务|垃圾质量)', -0.95),
            (r'(投诉|举报|曝光|维权)', -0.8),
            (r'(一生黑|永不回购|再也不买)', -0.85),
            (r'(非常差|特别差|十分差|极其差|烂透了|糟糕透顶)', -0.9),
            (r'(非常失望|十分失望|彻底失望|大失所望)', -0.9),
            (r'(非常糟糕|特别糟糕|十分糟糕)', -0.9),
            (r'(非常垃圾|特别垃圾|十分垃圾)', -0.95),
            (r'(客服.*?(差|烂|糟|冷漠|敷衍|不专业)|态度.*?(差|烂|糟|恶劣))', -0.85),
            (r'(物流.*?(慢|差|烂|糟糕)|配送.*?(慢|差|烂))', -0.75),
            (r'(再也不|永不再|再也不会)', -0.85),
            (r'(不推荐|不建议|不值得|不划算)', -0.8),
            (r'(Do\s+not\s+buy|dont\s+buy|do\s+not\s+waste|dont\s+waste|never\s+buy|never\s+again|stopped\s+working|stopped\s+working|broke\s+after|cracked|broken|refund|unhelpful|rude|delayed|worst\s+ever)', -0.85),
        ]

        self.english_positive_patterns = [
            (r'highly (recommend|rated|impressive)', 0.85),
            r'would (definitely|certainly|gladly) (recommend|buy|use)',
            r'(five|5) star(s)?',
            r'(love|loved|adore) (it|this|so much)',
            r'best (ever|i have ever had)',
            r'worth (every|the) (penny|cent|money)',
        ]

        self.english_negative_patterns = [
            r'would (never|not) (recommend|buy|use)',
            r'(one|1) star(s)?',
            r'waste (of|my) (time|money)',
            r'(do not|don\'t|dont) (buy|purchase|waste)',
            r'(worst|terrible|horrible|bad) (ever|i have ever had|experience)',
            r'(total|complete) (waste|garbage|junk)',
        ]

    def detect_language(self, text: str) -> str:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        return 'chinese' if chinese_chars >= english_chars else 'english'

    def _tokenize(self, text: str, language: str) -> List[str]:
        if language == 'chinese':
            try:
                import jieba
                words = list(jieba.cut(text))
            except ImportError:
                words = re.findall(r'[\u4e00-\u9fa5]+|[a-zA-Z]+|[^\s]', text)
        else:
            words = re.findall(r"[a-zA-Z']+|[^\s]", text)
        return [w.strip() for w in words if w.strip()]

    def _find_longest_match(self, text: str, dictionary: Dict) -> Tuple[float, int]:
        """在text中寻找词典最长匹配，返回累计分数和匹配次数"""
        total_score = 0.0
        match_count = 0
        sorted_items = sorted(dictionary.items(), key=lambda x: len(x[0]), reverse=True)
        for word, score in sorted_items:
            count = text.count(word)
            if count > 0:
                total_score += score * count
                match_count += count
        return total_score, match_count

    def _detect_negation_before(self, text: str, position: int, window: int = 4) -> float:
        """检测位置之前是否有否定词（返回-1或1）"""
        prefix = text[max(0, position - window):position]
        for neg_word in self.negations:
            if neg_word in prefix:
                return self.negations[neg_word]
        return 1.0

    def _detect_intensifier_before(self, text: str, position: int, window: int = 4) -> float:
        """检测位置之前是否有程度副词"""
        prefix = text[max(0, position - window):position]
        best_mult = 1.0
        best_len = 0
        for inten, mult in self.intensifiers.items():
            if inten in prefix and len(inten) > best_len:
                best_mult = mult
                best_len = len(inten)
        return best_mult

    def _calculate_lexicon_score(self, text: str, language: str) -> float:
        """基于词典和位置信息计算情感分数"""
        score = 0.0
        count = 0

        if language == 'chinese':
            # 正向词典
            for word, val in self.chinese_positive.items():
                start = 0
                while True:
                    idx = text.find(word, start)
                    if idx == -1:
                        break
                    neg_mult = self._detect_negation_before(text, idx, window=4)
                    inten_mult = self._detect_intensifier_before(text, idx, window=4)
                    weight = neg_mult * inten_mult
                    score += val * weight
                    count += 1
                    start = idx + len(word)

            # 负向词典
            for word, val in self.chinese_negative.items():
                start = 0
                while True:
                    idx = text.find(word, start)
                    if idx == -1:
                        break
                    neg_mult = self._detect_negation_before(text, idx, window=4)
                    inten_mult = self._detect_intensifier_before(text, idx, window=4)
                    weight = neg_mult * inten_mult
                    score += val * weight
                    count += 1
                    start = idx + len(word)

            # 额外检查"不+积极词" 和 "没+积极词"
            for pos_word, val in self.chinese_positive.items():
                for neg_prefix in ['不', '没', '没有', '无', '非']:
                    combined = neg_prefix + pos_word
                    start = 0
                    while True:
                        idx = text.find(combined, start)
                        if idx == -1:
                            break
                        score += -val * 1.2
                        count += 1
                        start = idx + len(combined)
        else:
            text_lower = text.lower()
            for word, val in self.chinese_positive.items():
                wl = word.lower()
                start = 0
                while True:
                    idx = text_lower.find(wl, start)
                    if idx == -1:
                        break
                    neg_mult = self._detect_negation_before(text_lower, idx, window=5)
                    inten_mult = self._detect_intensifier_before(text_lower, idx, window=5)
                    weight = neg_mult * inten_mult
                    score += val * weight
                    count += 1
                    start = idx + len(wl)

            for word, val in self.chinese_negative.items():
                wl = word.lower()
                start = 0
                while True:
                    idx = text_lower.find(wl, start)
                    if idx == -1:
                        break
                    neg_mult = self._detect_negation_before(text_lower, idx, window=5)
                    inten_mult = self._detect_intensifier_before(text_lower, idx, window=5)
                    weight = neg_mult * inten_mult
                    score += val * weight
                    count += 1
                    start = idx + len(wl)

        if count > 0:
            return score / count
        return 0.0

    def _calculate_pattern_score(self, text: str, language: str) -> float:
        """基于句式模式计算情感分数"""
        score = 0.0
        text_lower = text.lower()

        if language == 'chinese':
            for item in self.positive_patterns:
                pattern, val = item[0], item[1]
                matches = re.findall(pattern, text)
                if matches:
                    score += val * len(matches)
            for item in self.negative_patterns:
                pattern, val = item[0], item[1]
                matches = re.findall(pattern, text)
                if matches:
                    score += val * len(matches)
        else:
            for item in self.positive_patterns:
                pattern, val = item[0], item[1]
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    score += val * len(matches)
            for item in self.negative_patterns:
                pattern, val = item[0], item[1]
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    score += val * len(matches)
            for item in self.english_positive_patterns:
                pattern = item[0] if isinstance(item, tuple) else item
                default_val = item[1] if isinstance(item, tuple) else 0.75
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += default_val * len(matches)
            for item in self.english_negative_patterns:
                pattern = item[0] if isinstance(item, tuple) else item
                default_val = item[1] if isinstance(item, tuple) else -0.75
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += default_val * len(matches)

        return score

    def _calculate_emoji_score(self, text: str) -> float:
        total_score = 0.0
        count = 0
        for emoji, score in self.emoji_sentiment.items():
            occ = text.count(emoji)
            if occ > 0:
                total_score += score * occ
                count += occ
        return total_score / count if count > 0 else 0.0

    def _calculate_sentence_score(self, text: str, language: str) -> float:
        """按句子计算情感分数"""
        sentences = re.split(r'[。！？.!?!?；;\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0

        scores = []
        for sentence in sentences:
            s = 0.0
            c = 0

            # 词典匹配
            if language == 'chinese':
                for word, val in self.chinese_positive.items():
                    if word in sentence:
                        neg = self._detect_negation_before(sentence, sentence.find(word), 4)
                        mult = self._detect_intensifier_before(sentence, sentence.find(word), 4)
                        s += val * neg * mult
                        c += 1
                for word, val in self.chinese_negative.items():
                    if word in sentence:
                        neg = self._detect_negation_before(sentence, sentence.find(word), 4)
                        mult = self._detect_intensifier_before(sentence, sentence.find(word), 4)
                        s += val * neg * mult
                        c += 1
            else:
                sl = sentence.lower()
                for word, val in self.chinese_positive.items():
                    if word.lower() in sl:
                        s += val
                        c += 1
                for word, val in self.chinese_negative.items():
                    if word.lower() in sl:
                        s += val
                        c += 1

            if c > 0:
                scores.append(s / c)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def analyze(self, text: str) -> Dict:
        if not text or not text.strip():
            return {
                'sentiment': 'positive',
                'sentiment_name': '正面',
                'confidence': 0.5,
                'positive_score': 0.5,
                'negative_score': 0.5,
                'raw_score': 0.0,
                'details': {
                    'lexicon_score': 0.0,
                    'pattern_score': 0.0,
                    'sentence_score': 0.0,
                    'emoji_score': 0.0,
                    'snownlp_score': None,
                    'sentence_count': 0,
                    'word_count': 0
                },
                'gauge_data': self._generate_gauge_data(0.5, 0.5)
            }

        language = self.detect_language(text)
        words = self._tokenize(text, language)
        sentences = [s.strip() for s in re.split(r'[。！？.!?!?；;\n]+', text) if s.strip()]

        lexicon_score = self._calculate_lexicon_score(text, language)
        pattern_score = self._calculate_pattern_score(text, language)
        sentence_score = self._calculate_sentence_score(text, language)
        emoji_score = self._calculate_emoji_score(text)

        snownlp_score = 0.0
        if language == 'chinese' and self.snownlp_available:
            try:
                s = self.SnowNLP(text)
                snownlp_score = (s.sentiments - 0.5) * 2
            except Exception:
                snownlp_score = 0.0

        if language == 'chinese' and self.snownlp_available:
            combined = (
                lexicon_score * 0.35 +
                pattern_score * 0.15 +
                sentence_score * 0.15 +
                emoji_score * 0.05 +
                snownlp_score * 0.30
            )
        else:
            combined = (
                lexicon_score * 0.50 +
                pattern_score * 0.20 +
                sentence_score * 0.15 +
                emoji_score * 0.15
            )

        combined = max(-1.0, min(1.0, combined))

        positive_score = (combined + 1) / 2
        positive_score = max(0.01, min(0.99, positive_score))
        negative_score = 1 - positive_score

        if positive_score >= 0.5:
            sentiment = 'positive'
            sentiment_name = '正面'
            if positive_score >= 0.8:
                sentiment_name = '非常正面'
            elif positive_score >= 0.65:
                sentiment_name = '比较正面'
        else:
            sentiment = 'negative'
            sentiment_name = '负面'
            if positive_score <= 0.2:
                sentiment_name = '非常负面'
            elif positive_score <= 0.35:
                sentiment_name = '比较负面'

        confidence = abs(positive_score - 0.5) * 2
        confidence = max(0.5, min(0.99, 0.5 + confidence * 0.5))

        return {
            'sentiment': sentiment,
            'sentiment_name': sentiment_name,
            'confidence': round(confidence, 4),
            'positive_score': round(positive_score, 4),
            'negative_score': round(negative_score, 4),
            'raw_score': round(combined, 4),
            'language': language,
            'details': {
                'lexicon_score': round(lexicon_score, 4),
                'pattern_score': round(pattern_score, 4),
                'sentence_score': round(sentence_score, 4),
                'emoji_score': round(emoji_score, 4),
                'snownlp_score': round(snownlp_score, 4) if self.snownlp_available else None,
                'sentence_count': len(sentences),
                'word_count': len(words)
            },
            'gauge_data': self._generate_gauge_data(positive_score, confidence)
        }

    def _generate_gauge_data(self, positive_score: float, confidence: float) -> Dict:
        segments = [
            {'from': 0, 'to': 0.2, 'color': '#e74c3c', 'label': '非常负面'},
            {'from': 0.2, 'to': 0.4, 'color': '#e67e22', 'label': '比较负面'},
            {'from': 0.4, 'to': 0.6, 'color': '#f39c12', 'label': '中性'},
            {'from': 0.6, 'to': 0.8, 'color': '#27ae60', 'label': '比较正面'},
            {'from': 0.8, 'to': 1.0, 'color': '#2ecc71', 'label': '非常正面'},
        ]
        current_segment = None
        for seg in segments:
            if seg['from'] <= positive_score <= seg['to']:
                current_segment = seg
                break
        if not current_segment:
            current_segment = segments[-1] if positive_score > 0.5 else segments[0]

        return {
            'value': positive_score,
            'confidence': confidence,
            'segments': segments,
            'current_color': current_segment['color'],
            'current_label': current_segment['label'],
            'percentage': positive_score * 100
        }

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        return [self.analyze(t) for t in texts]

    def get_sentiment_distribution(self, texts: List[str]) -> Dict:
        results = self.analyze_batch(texts)
        distribution = {
            'positive': 0,
            'negative': 0,
            'average_positive_score': 0.0,
            'average_confidence': 0.0,
            'total_count': len(results)
        }
        for r in results:
            distribution[r['sentiment']] += 1
            distribution['average_positive_score'] += r['positive_score']
            distribution['average_confidence'] += r['confidence']
        if len(results) > 0:
            distribution['average_positive_score'] /= len(results)
            distribution['average_confidence'] /= len(results)
        return distribution
