"""
实体识别模块 - 支持中文/英文文本的多类型实体识别
识别类型：人物(PER)、组织(ORG)、地点(LOC)、时间(TIME)、专有名词(NOUN)
"""
import re
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

import jieba
import jieba.posseg as pseg


@dataclass
class Entity:
    """实体数据类"""
    text: str
    entity_type: str
    start: int
    end: int
    confidence: float = 0.0
    type_name: str = field(init=False)

    def __post_init__(self):
        type_map = {
            'PER': '人物',
            'ORG': '组织',
            'LOC': '地点',
            'TIME': '时间',
            'NOUN': '专有名词'
        }
        self.type_name = type_map.get(self.entity_type, self.entity_type)


class EntityRecognizer:
    """实体识别器 - 多模型融合策略（词典+词性标注+正则）"""

    ENTITY_TYPES = {
        'PER': {'name': '人物', 'color': '#e74c3c'},
        'ORG': {'name': '组织', 'color': '#3498db'},
        'LOC': {'name': '地点', 'color': '#2ecc71'},
        'TIME': {'name': '时间', 'color': '#f39c12'},
        'NOUN': {'name': '专有名词', 'color': '#9b59b6'}
    }

    def __init__(self):
        self._init_dictionaries()
        self._init_patterns()
        self._init_jieba()

    def _init_jieba(self):
        """初始化jieba分词和词性标注"""
        try:
            jieba.setLogLevel(jieba.logging.WARNING)
        except Exception:
            pass

    def _init_dictionaries(self):
        """初始化自定义词典"""
        self.person_suffixes = {
            '先生', '女士', '同志', '同学', '老师', '教授', '博士',
            '院长', '校长', '总经理', 'CEO', '董事长', '主席',
            '总统', '总理', '书记', '局长', '处长', '科长', '主任',
            '经理', '总监', '总裁', '总理', '部长', '省长', '市长',
            '县长', '区长', '镇长', '乡长', '队长', '组长', '主管',
            '工程师', '设计师', '律师', '医生', '护士', '会计',
            '总', '董', '秘'
        }

        self.person_surnames = set('赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭郎鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍虞万支柯昝管卢莫经房裘缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴弓牧隗山谷车侯宓蓬全郗班仰秋仲伊宫宁仇栾暴甘钭厉戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴郁胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍却璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东殴殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养鞠须丰巢关蒯相查后荆红游竺权逯盖益桓公欧阳司马上官诸葛夏侯尉迟公孙轩辕令狐宇文慕容司徒')

        self.chinese_cities = {
            '北京', '上海', '广州', '深圳', '天津', '重庆', '杭州', '南京', '苏州', '成都',
            '武汉', '西安', '长沙', '郑州', '青岛', '大连', '厦门', '宁波', '无锡', '合肥',
            '福州', '南昌', '济南', '昆明', '贵阳', '拉萨', '兰州', '西宁', '银川', '乌鲁木齐',
            '呼和浩特', '沈阳', '长春', '哈尔滨', '石家庄', '太原', '南宁', '海口', '三亚',
            '泉州', '东莞', '佛山', '珠海', '中山', '惠州', '汕头', '江门', '湛江', '肇庆',
            '桂林', '柳州', '温州', '绍兴', '金华', '嘉兴', '台州', '湖州', '徐州', '常州',
            '南通', '扬州', '镇江', '泰州', '盐城', '淮安', '连云港', '宿迁', '芜湖', '蚌埠',
            '安庆', '黄山', '滁州', '阜阳', '宿州', '六安', '亳州', '池州', '宣城', '莆田',
            '三明', '泉州', '漳州', '南平', '龙岩', '宁德', '景德镇', '萍乡', '九江', '新余',
            '鹰潭', '赣州', '吉安', '宜春', '抚州', '上饶', '淄博', '枣庄', '东营', '烟台',
            '潍坊', '济宁', '泰安', '威海', '日照', '临沂', '德州', '聊城', '滨州', '菏泽',
            '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡',
            '南阳', '商丘', '信阳', '周口', '驻马店', '黄石', '十堰', '宜昌', '襄阳', '鄂州',
            '荆门', '孝感', '荆州', '黄冈', '咸宁', '随州', '株洲', '湘潭', '衡阳', '邵阳',
            '岳阳', '常德', '张家界', '益阳', '郴州', '永州', '怀化', '娄底', '韶关', '深圳',
            '珠海', '汕头', '佛山', '江门', '湛江', '茂名', '肇庆', '惠州', '梅州', '汕尾',
            '河源', '阳江', '清远', '东莞', '中山', '潮州', '揭阳', '云浮', '柳州', '桂林',
            '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池', '来宾',
            '崇左', '遵义', '六盘水', '安顺', '毕节', '铜仁', '曲靖', '玉溪', '保山', '昭通',
            '丽江', '普洱', '临沧', '日喀则', '昌都', '林芝', '山南', '那曲', '阿里', '铜川',
            '宝鸡', '咸阳', '渭南', '延安', '汉中', '榆林', '安康', '商洛', '嘉峪关', '金昌',
            '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南', '海东',
            '石嘴山', '吴忠', '固原', '中卫', '克拉玛依', '吐鲁番', '哈密', '包头', '乌海',
            '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布', '鞍山', '抚顺',
            '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭', '朝阳', '葫芦岛',
            '吉林', '四平', '辽源', '通化', '白山', '松原', '白城', '齐齐哈尔', '鸡西', '鹤岗',
            '双鸭山', '大庆', '伊春', '佳木斯', '七台河', '牡丹江', '黑河', '绥化', '唐山',
            '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水', '大同',
            '阳泉', '长治', '晋城', '朔州', '晋中', '运城', '忻州', '临汾', '吕梁'
        }

        self.chinese_provinces = {
            '河北', '山西', '辽宁', '吉林', '黑龙江', '江苏', '浙江', '安徽', '福建', '江西',
            '山东', '河南', '湖北', '湖南', '广东', '海南', '四川', '贵州', '云南', '陕西',
            '甘肃', '青海', '台湾', '内蒙古', '广西', '西藏', '宁夏', '新疆', '香港', '澳门'
        }

        self.countries = {
            '中国', '美国', '英国', '法国', '德国', '日本', '韩国', '朝鲜', '俄罗斯', '印度',
            '巴西', '澳大利亚', '加拿大', '意大利', '西班牙', '墨西哥', '印度尼西亚', '土耳其',
            '沙特阿拉伯', '阿根廷', '南非', '埃及', '伊朗', '泰国', '越南', '菲律宾', '马来西亚',
            '新加坡', '巴基斯坦', '孟加拉国', '尼日利亚', '埃塞俄比亚', '刚果', '坦桑尼亚',
            '肯尼亚', '乌干达', '阿尔及利亚', '苏丹', '伊拉克', '摩洛哥', '秘鲁', '委内瑞拉',
            '尼泊尔', '阿富汗', '缅甸', '柬埔寨', '老挝', '文莱', '东帝汶', '不丹', '斯里兰卡',
            '马尔代夫', '巴勒斯坦', '以色列', '约旦', '黎巴嫩', '叙利亚', '科威特', '卡塔尔',
            '巴林', '阿曼', '也门', '格鲁吉亚', '亚美尼亚', '阿塞拜疆', '哈萨克斯坦', '乌兹别克斯坦',
            '吉尔吉斯斯坦', '塔吉克斯坦', '土库曼斯坦', '蒙古', '乌克兰', '白俄罗斯', '波兰',
            '捷克', '斯洛伐克', '匈牙利', '罗马尼亚', '保加利亚', '塞尔维亚', '克罗地亚',
            '斯洛文尼亚', '波黑', '黑山', '北马其顿', '阿尔巴尼亚', '希腊', '塞浦路斯', '冰岛',
            '丹麦', '挪威', '瑞典', '芬兰', '爱沙尼亚', '拉脱维亚', '立陶宛', '摩尔多瓦',
            '瑞士', '奥地利', '列支敦士登', '荷兰', '比利时', '卢森堡', '爱尔兰', '葡萄牙',
            '马耳他', '新西兰', '斐济', '巴布亚新几内亚', '智利', '哥伦比亚', '古巴', '捷克',
            '多米尼加', '厄瓜多尔', '芬兰', '危地马拉', '洪都拉斯', '牙买加', '肯尼亚',
            '科威特', '拉脱维亚', '黎巴嫩', '立陶宛', '马达加斯加', '马来西亚', '马里',
            '毛里塔尼亚', '墨西哥', '摩尔多瓦', '摩洛哥', '纳米比亚', '尼泊尔', '尼加拉瓜',
            '尼日尔', '阿曼', '巴拿马', '巴拉圭', '秘鲁', '菲律宾', '波兰', '葡萄牙', '卡塔尔',
            '罗马尼亚', '卢旺达', '沙特阿拉伯', '塞内加尔', '塞尔维亚', '斯洛伐克', '斯洛文尼亚',
            '索马里', '南非', '韩国', '南苏丹', '西班牙', '斯里兰卡', '苏丹', '苏里南', '瑞典',
            '瑞士', '叙利亚', '塔吉克斯坦', '坦桑尼亚', '泰国', '多哥', '突尼斯', '土耳其',
            '土库曼斯坦', '乌干达', '乌克兰', '阿联酋', '英国', '美国', '乌拉圭', '乌兹别克斯坦',
            '委内瑞拉', '越南', '也门', '赞比亚', '津巴布韦'
        }

        self.location_keywords = {
            '省', '市', '自治区', '特别行政区', '地区', '州', '县', '区', '镇', '乡', '村',
            '街', '路', '道', '巷', '弄', '号', '楼', '座', '小区', '公寓', '花园', '广场',
            '大厦', '中心', '公园', '体育馆', '体育场', '机场', '火车站', '高铁站', '地铁站',
            '港口', '码头', '大桥', '隧道', '水库', '湖', '河', '江', '山', '峰', '高原',
            '平原', '盆地', '沙漠', '森林', '草原', '湿地', '区', '县', '市', '省', '州'
        }

        self.organization_keywords = {
            '公司', '集团', '企业', '工厂', '学校', '大学', '学院', '研究所', '研究院',
            '中心', '协会', '学会', '委员会', '局', '部', '厅', '处', '科', '院', '馆',
            '站', '所', '队', '团', '组', '社', '室', '银行', '证券', '保险', '基金',
            '医院', '法院', '检察院', '政府', '署', '办', '出版社', '杂志社', '报社',
            '电视台', '广播电台', '传媒', '媒体', '网络科技', '信息科技', '电子科技',
            '软件', '科技', '股份有限公司', '有限责任公司', '有限公司'
        }

        self.chinese_leaders = {
            '习近平', '李克强', '栗战书', '汪洋', '王沪宁', '赵乐际', '韩正',
            '胡锦涛', '温家宝', '江泽民', '朱镕基', '李鹏', '乔石', '李瑞环',
            '毛泽东', '周恩来', '刘少奇', '朱德', '邓小平', '陈云',
            '孙中山', '蒋介石', '宋子文', '孔祥熙',
            '特朗普', '拜登', '奥巴马', '布什', '克林顿', '里根', '普京',
            '默克尔', '马克龙', '约翰逊', '安倍晋三', '菅义伟', '岸田文雄',
            '文在寅', '尹锡悦', '莫迪', '杜特尔特'
        }

        self.chinese_organizations = {
            '阿里巴巴', '腾讯', '百度', '字节跳动', '京东', '美团', '拼多多', '网易',
            '小米', '华为', '中兴', '联想', '格力', '美的', '海尔', '比亚迪', '宁德时代',
            '招商银行', '平安', '中国人寿', '中国移动', '中国联通', '中国电信',
            '中国石油', '中国石化', '中国建筑', '工商银行', '建设银行', '农业银行',
            '中国银行', '交通银行', '浦发银行', '兴业银行', '中信银行', '民生银行',
            '光大银行', '华夏银行', '万科', '保利', '碧桂园', '恒大', '万达', '融创',
            '华润', '中粮', '国家电网', '南方电网', '中国烟草', '中国邮政', '中国铁路',
            '中国航天', '中国航空', '中国商飞', '三一重工', 'TCL', '创维', '康佳',
            '长虹', '海信', 'OPPO', 'vivo', '大疆', '蔚来', '小鹏', '理想', '长城',
            '长安', '吉利', '奇瑞', '上汽', '一汽', '东风', '广汽', '北汽',
            '福耀玻璃', '海螺水泥', '贵州茅台', '五粮液', '泸州老窖', '洋河股份',
            '海天味业', '伊利股份', '蒙牛', '双汇发展', '牧原股份', '温氏股份',
            '海大集团', '中国中免', '顺丰控股', '韵达股份', '圆通速递', '中通快递',
            '申通快递', '京东物流', '美团外卖', '饿了么', '滴滴出行', '高德地图',
            '百度地图', '腾讯地图', '支付宝', '微信支付', '云闪付', '快手', '抖音',
            'Bilibili', '小红书', '知乎', '豆瓣', '微博', '微信', 'QQ', '腾讯视频',
            '爱奇艺', '优酷', '芒果TV', '喜马拉雅', '网易云音乐', 'QQ音乐',
            '酷狗音乐', '酷我音乐', '全民K歌', '唱吧', '虎牙', '斗鱼', '陌陌',
            '得物', '蘑菇街', '唯品会', '苏宁易购', '国美', '当当网', '亚马逊',
            '联合国', '世界卫生组织', 'WHO', 'UN', 'WTO', '欧盟', '北约', '东盟',
            '国际货币基金组织', 'IMF', '世界银行', '红十字会', '奥林匹克委员会',
            '教育部', '科技部', '工信部', '发改委', '财政部', '商务部', '公安部',
            '司法部', '住建部', '交通部', '水利部', '农业农村部', '文化和旅游部',
            '卫健委', '人民银行', '审计署', '海关总署', '税务总局', '市场监管总局',
            '清华大学', '北京大学', '复旦大学', '上海交通大学', '浙江大学',
            '南京大学', '中国科学技术大学', '武汉大学', '华中科技大学', '中山大学',
            '西安交通大学', '哈尔滨工业大学', '同济大学', '北京师范大学', '南开大学',
            '北京航空航天大学', '中国人民大学', '天津大学', '东南大学', '四川大学',
            '吉林大学', '山东大学', '厦门大学', '华南理工大学', '大连理工大学',
            '西北工业大学', '重庆大学', '兰州大学', '湖南大学', '中南大学',
            '中国科学院', '中国工程院', '社科院', '国务院', '全国人大', '政协',
            '中共中央', '中央军委', '国防部', '外交部', '国防部'
        }

        self.location_landmarks = {
            '天安门', '故宫', '紫禁城', '长城', '颐和园', '圆明园', '天坛', '地坛',
            '中南海', '北海', '什刹海', '景山', '王府井', '西单', '东单', '前门',
            '大栅栏', '三里屯', '国贸', 'CBD', '中关村', '望京', '五道口', '西二旗',
            '上地', '亦庄', '通州', '雄安新区', '浦东新区', '陆家嘴', '外滩', '南京路',
            '人民广场', '豫园', '静安寺', '徐家汇', '虹桥', '张江高科', '深圳湾',
            '福田', '罗湖', '南山', '蛇口', '前海', '广州塔', '珠江新城', '天河',
            '越秀', '荔湾', '海珠', '白云', '番禺', '黄埔', '西湖', '外滩', '东方明珠',
            '迪士尼', '欢乐谷', '长隆', '兵马俑', '大雁塔', '华清池', '黄山', '泰山',
            '华山', '衡山', '恒山', '嵩山', '庐山', '峨眉山', '五台山', '普陀山',
            '九华山', '武夷山', '长白山', '天山', '昆仑山', '喜马拉雅山', '珠穆朗玛峰',
            '白宫', '五角大楼', '国会山', '华尔街', '硅谷', '好莱坞', '百老汇',
            '泰晤士河', '埃菲尔铁塔', '卢浮宫', '凯旋门', '金字塔', '悉尼歌剧院'
        }

        self.tech_terms = {
            '人工智能', '机器学习', '深度学习', '神经网络', '自然语言处理', '计算机视觉',
            '大数据', '云计算', '区块链', '物联网', '5G', '6G', '量子计算', '元宇宙',
            'ChatGPT', 'GPT-3', 'GPT-4', 'GPT-5', 'LLaMA', 'BERT', 'Transformer',
            '大语言模型', '生成式AI', 'AIGC', '多模态', '强化学习', '监督学习', '无监督学习',
            '迁移学习', '小样本学习', '零样本学习', '提示工程', '思维链', '检索增强生成', 'RAG',
            'Python', 'Java', 'C++', 'C#', 'JavaScript', 'TypeScript', 'Go', 'Rust', 'Swift',
            'Kotlin', 'PHP', 'Ruby', 'Perl', 'Flask', 'Django', 'Spring', 'React', 'Vue',
            'Angular', 'Node.js', 'Express', 'MySQL', 'PostgreSQL', 'MongoDB', 'Redis',
            'Oracle', 'SQL Server', 'Docker', 'Kubernetes', 'AWS', 'Azure', '阿里云',
            '腾讯云', '华为云', 'API', 'SDK', 'IDE', 'CPU', 'GPU', 'TPU', 'NPU',
            'HTTP', 'HTTPS', 'TCP', 'IP', 'DNS', 'SSL', 'TLS', 'COVID-19', '新冠病毒',
            'SARS', 'H1N1', '甲型流感', '乙型流感', 'GDP', 'CPI', 'PPI', 'PMI', 'IPO',
            'A股', '港股', '美股', '科创板', '创业板', '新能源汽车', '自动驾驶',
            '智能驾驶', '辅助驾驶', '无人驾驶', '车路协同', 'V2X', '光伏发电', '风力发电',
            '水力发电', '核能发电', '储能', '锂电池', '固态电池', '钠离子电池',
            '碳中和', '碳达峰', '双碳', 'ESG', '半导体', '芯片', '集成电路', '晶圆',
            '光刻机', '刻蚀机', '薄膜沉积', '封装测试', 'Micro-LED', 'Mini-LED',
            'OLED', 'QLED', 'LCD', 'AMOLED', 'VR', 'AR', 'MR', 'XR', '混合现实',
            '虚拟现实', '增强现实', '智能家居', '智慧交通', '智慧城市', '智慧医疗',
            '智慧教育', '智慧金融', '数字人民币', 'e-CNY', '移动支付', '第三方支付',
            '卫星互联网', '低轨卫星', '星链', '北斗导航', 'GPS', '可控核聚变',
            '托卡马克', '仿星器', '脑机接口', 'BCI', '神经接口', '合成生物学',
            '基因编辑', 'CRISPR', 'mRNA', 'DNA', 'RNA', '纳米技术', '石墨烯',
            '碳纳米管', '二维材料', '拓扑绝缘体', 'Web3.0', '去中心化金融', 'DeFi',
            '非同质化代币', 'NFT', '去中心化自治组织', 'DAO', '智能合约', '以太坊',
            '比特币', 'BTC', 'ETH', 'USDT', 'USDC', '大模型', '基座模型', '微调',
            '对齐', 'RLHF', '红队测试', '数据中心', '超算', '超级计算机', '量子计算机',
            '超导量子比特', '离子阱', '光量子计算', '拓扑量子计算', '边缘计算',
            '雾计算', '算力网络', '东数西算', '隐私计算', '联邦学习', '多方安全计算',
            '同态加密', '零知识证明', '网络安全', '信息安全', '数据安全', '密码学',
            '渗透测试', '漏洞挖掘', '产品发布会', '研讨会', '庆典', '会议', '论坛',
            '展览会', '博览会', '峰会', '听证会', '发布会'
        }

        self.english_name_pattern = re.compile(r'\b([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b')
        self.english_org_pattern = re.compile(r'\b[A-Z][a-zA-Z0-9&.,-]+(?:\s+[A-Z][a-zA-Z0-9&.,-]+){0,4}\s+(Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?|Group|Company|Corporation|Limited|Holdings|Solutions|Technologies|Systems|Services|Industries|International|Global|Worldwide|University|College|Institute|Academy|School|Hospital|Association|Society|Federation|Committee|Commission|Department|Ministry|Bureau|Agency|Authority|Board|Council|Chamber|Foundation|Fund|Union|League)\b', re.IGNORECASE)
        self.english_location_pattern = re.compile(r'\b[A-Z][a-zA-Z]+\s+(Province|State|City|County|Town|Village|District|Region|Area|Ocean|Sea|River|Lake|Mountain|Mount|Mt\.|Peak|Island|Peninsula|Bay|Gulf|Strait|Channel|Canal|Desert|Forest|Valley|Canyon|Falls|Park|Square|Plaza|Center|Centre|Airport|Station|Tower|Bridge|Road|Street|Avenue|Boulevard|Lane|Drive|Court|Place|Way|Terrace|Gardens|Heights|Hills|Estates|Manor|Castle|Palace|Hall|Museum|Library|Memorial|Monument)\b')

    def _init_patterns(self):
        """初始化正则匹配模式 - 严格边界检查"""
        self.strict_time_patterns = [
            (r'\d{4}年\d{1,2}月\d{1,2}[日号]', 'TIME', 0.95),
            (r'\d{4}年\d{1,2}月', 'TIME', 0.93),
            (r'(?<!\d)\d{4}年(?!\d)', 'TIME', 0.90),
            (r'\d{1,2}月\d{1,2}[日号]', 'TIME', 0.90),
            (r'\d{4}[-/]\d{1,2}[-/]\d{1,2}', 'TIME', 0.95),
            (r'\d{1,2}:\d{2}(:\d{2})?', 'TIME', 0.92),
            (r'\d{1,2}点\d{0,2}分?\d{0,2}秒?', 'TIME', 0.90),
            (r'\d{1,2}点半', 'TIME', 0.90),
            (r'公元[前后]?\d{1,4}年', 'TIME', 0.92),
            (r'[一二三四五六七八九十百千万零〇]+世纪', 'TIME', 0.88),
            (r'\d{4}年代', 'TIME', 0.90),
            (r'第[一二三四五六七八九十百千0-9]+(?:季度|学期|周|期|届|次|轮)', 'TIME', 0.88),
            (r'[上下]半年', 'TIME', 0.88),
            (r'\d{2,4}学年', 'TIME', 0.85),
        ]

        self.time_keywords = [
            '今天', '昨天', '前天', '明天', '后天', '大前天', '大后天',
            '去年', '今年', '明年', '前年', '后年',
            '上午', '下午', '晚上', '凌晨', '早晨', '早上', '中午', '傍晚', '深夜', '半夜',
            '每周', '每月', '每天', '每日', '每季度', '每年',
            '年初', '年末', '月底', '月初', '周末', '周初',
            '春节', '端午节', '中秋节', '国庆节', '劳动节', '元旦', '清明节', '元宵节',
            '情人节', '圣诞节', '万圣节', '感恩节', '复活节', '母亲节', '父亲节',
            '儿童节', '教师节', '建军节', '建党节', '妇女节', '青年节', '植树节',
            '春运', '暑运', '黄金周', '小长假'
        ]

        self.weekdays = [
            '星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日', '星期天',
            '周一', '周二', '周三', '周四', '周五', '周六', '周日',
            '礼拜一', '礼拜二', '礼拜三', '礼拜四', '礼拜五', '礼拜六', '礼拜天', '礼拜日'
        ]

        self.week_prefixes = ['这', '那', '上', '下', '前', '后', '本']

    def detect_language(self, text: str) -> str:
        """检测文本语言"""
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        return 'chinese' if chinese_chars >= english_chars else 'english'

    def _find_substring_positions(self, text: str, substring: str) -> List[Tuple[int, int]]:
        """查找子串的所有位置"""
        positions = []
        start = 0
        while True:
            pos = text.find(substring, start)
            if pos == -1:
                break
            positions.append((pos, pos + len(substring)))
            start = pos + 1
        return positions

    def _extract_dict_entities(self, text: str) -> List[Entity]:
        """基于词典提取实体"""
        entities = []

        for leader in self.chinese_leaders:
            for start, end in self._find_substring_positions(text, leader):
                entities.append(Entity(
                    text=leader, entity_type='PER',
                    start=start, end=end, confidence=0.96
                ))

        for org in self.chinese_organizations:
            for start, end in self._find_substring_positions(text, org):
                if len(org) >= 2:
                    confidence = 0.92 if len(org) >= 4 else 0.88
                    entities.append(Entity(
                        text=org, entity_type='ORG',
                        start=start, end=end, confidence=confidence
                    ))

        for country in self.countries:
            for start, end in self._find_substring_positions(text, country):
                entities.append(Entity(
                    text=country, entity_type='LOC',
                    start=start, end=end, confidence=0.95
                ))

        for city in self.chinese_cities:
            for start, end in self._find_substring_positions(text, city):
                entities.append(Entity(
                    text=city, entity_type='LOC',
                    start=start, end=end, confidence=0.92
                ))

        for province in self.chinese_provinces:
            for start, end in self._find_substring_positions(text, province):
                entities.append(Entity(
                    text=province, entity_type='LOC',
                    start=start, end=end, confidence=0.93
                ))

        for landmark in self.location_landmarks:
            for start, end in self._find_substring_positions(text, landmark):
                entities.append(Entity(
                    text=landmark, entity_type='LOC',
                    start=start, end=end, confidence=0.90
                ))

        for term in self.tech_terms:
            for start, end in self._find_substring_positions(text, term):
                confidence = 0.95 if len(term) >= 4 else 0.85
                entities.append(Entity(
                    text=term, entity_type='NOUN',
                    start=start, end=end, confidence=confidence
                ))

        for wk in self.time_keywords:
            for start, end in self._find_substring_positions(text, wk):
                entities.append(Entity(
                    text=wk, entity_type='TIME',
                    start=start, end=end, confidence=0.92
                ))

        for wd in self.weekdays:
            for start, end in self._find_substring_positions(text, wd):
                entities.append(Entity(
                    text=wd, entity_type='TIME',
                    start=start, end=end, confidence=0.93
                ))

        for prefix in self.week_prefixes:
            for suffix in ['周', '星期', '礼拜', '月', '季度', '年', '个星期', '个月']:
                compound = prefix + suffix
                if compound in text:
                    for start, end in self._find_substring_positions(text, compound):
                        entities.append(Entity(
                            text=compound, entity_type='TIME',
                            start=start, end=end, confidence=0.90
                        ))

        return entities

    def _extract_strict_regex_entities(self, text: str) -> List[Entity]:
        """使用严格正则提取实体"""
        entities = []

        for pattern, etype, conf in self.strict_time_patterns:
            try:
                for match in re.finditer(pattern, text):
                    matched = match.group()
                    if 1 <= len(matched) <= 25:
                        entities.append(Entity(
                            text=matched, entity_type=etype,
                            start=match.start(), end=match.end(),
                            confidence=conf
                        ))
            except re.error:
                continue

        year_pattern = r'(?<!\d)(?:19|20)\d{2}(?!\d)'
        for match in re.finditer(year_pattern, text):
            matched = match.group()
            if matched.isdigit() and 1900 <= int(matched) <= 2100:
                entities.append(Entity(
                    text=matched, entity_type='TIME',
                    start=match.start(), end=match.end(),
                    confidence=0.88
                ))

        suffix_org_pattern = r'(?<![\u4e00-\u9fa5年月日时分秒号第在于是到和与及或、，。！？；：])([\u4e00-\u9fa5]{2,8})(?:股份有限|有限责任|有限|责任)?公司'
        for match in re.finditer(suffix_org_pattern, text):
            matched = match.group(0)
            core = match.group(1)
            if 3 <= len(matched) <= 20 and len(core) >= 2:
                entities.append(Entity(
                    text=matched, entity_type='ORG',
                    start=match.start(), end=match.end(),
                    confidence=0.88
                ))

        suffix_orgs2 = r'(?<![\u4e00-\u9fa5年月日时分秒号第在于是到和与及或、，。！？；：])([\u4e00-\u9fa5]{2,8})(集团|学校|大学|学院|研究所|研究院|银行|医院|协会|学会|委员会|局|部|出版社|杂志社|报社|电视台|广播电台|传媒|政府)'
        for match in re.finditer(suffix_orgs2, text):
            matched = match.group(0)
            core = match.group(1)
            if 3 <= len(matched) <= 20 and len(core) >= 2:
                entities.append(Entity(
                    text=matched, entity_type='ORG',
                    start=match.start(), end=match.end(),
                    confidence=0.85
                ))

        suffix_locs = r'(?<![\u4e00-\u9fa5年月日时分秒号第在于是到和与及或、，。！？；：0-9])([\u4e00-\u9fa5]{2,8})(省|市|自治区|特别行政区|州|县|区|镇|乡|村|路|街|道|巷|弄|公园|广场|机场|火车站|高铁站|地铁站|港口|码头|大桥|大厦)'
        for match in re.finditer(suffix_locs, text):
            matched = match.group(0)
            core = match.group(1)
            if 2 <= len(matched) <= 20 and len(core) >= 2:
                entities.append(Entity(
                    text=matched, entity_type='LOC',
                    start=match.start(), end=match.end(),
                    confidence=0.83
                ))

        return entities

    def _extract_jieba_entities(self, text: str) -> List[Entity]:
        """使用jieba词性标注提取实体"""
        entities = []
        try:
            words = pseg.cut(text)
            current_pos = 0

            for word, flag in words:
                if not word.strip():
                    current_pos += len(word)
                    continue

                start = text.find(word, current_pos)
                if start == -1:
                    start = current_pos
                end = start + len(word)
                current_pos = end

                if len(word) < 2:
                    continue

                if flag == 'nr' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='PER',
                        start=start, end=end, confidence=0.86
                    ))
                elif flag == 'nrfg' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='PER',
                        start=start, end=end, confidence=0.91
                    ))
                elif flag == 'nrt' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='PER',
                        start=start, end=end, confidence=0.93
                    ))
                elif flag == 'ns' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='LOC',
                        start=start, end=end, confidence=0.82
                    ))
                elif flag == 'nsf' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='LOC',
                        start=start, end=end, confidence=0.87
                    ))
                elif flag in ['nt', 'ntc', 'ntcb', 'ntcf', 'ntch', 'nth', 'nto', 'nts', 'ntu'] and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='ORG',
                        start=start, end=end, confidence=0.80
                    ))
                elif flag in ['nz', 'nl'] and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='NOUN',
                        start=start, end=end, confidence=0.78
                    ))
                elif flag == 't' and len(word) >= 2:
                    entities.append(Entity(
                        text=word, entity_type='TIME',
                        start=start, end=end, confidence=0.75
                    ))
        except Exception:
            pass

        return entities

    def _extract_person_with_suffix(self, text: str) -> List[Entity]:
        entities = []

        for suffix in self.person_suffixes:
            escaped_suffix = re.escape(suffix)
            pattern = r'(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]{1,3})' + escaped_suffix
            for match in re.finditer(pattern, text):
                full_name = match.group(1) + suffix
                name_part = match.group(1)
                if 2 <= len(full_name) <= 8:
                    if len(name_part) >= 1 and name_part[0] in self.person_surnames:
                        entities.append(Entity(
                            text=full_name, entity_type='PER',
                            start=match.start(), end=match.end(),
                            confidence=0.88
                        ))
                    elif len(name_part) >= 2:
                        entities.append(Entity(
                            text=full_name, entity_type='PER',
                            start=match.start(), end=match.end(),
                            confidence=0.82
                        ))

        short_title_pattern = re.compile(
            r'(?<![\u4e00-\u9fa5a-zA-Z])([李王张刘陈杨赵黄周吴徐孙胡朱高林何郭马罗梁宋郑谢韩唐冯于董萧程曹袁邓许傅沈曾彭吕苏卢蒋蔡贾丁魏薛叶阎余潘杜戴夏钟汪田任姜范方石姚谭廖周熊金陆郝孔白崔康毛邱秦江史顾侯邵孟万段雷钱汤尹黎易常武乔贺赖龚文])'
            r'(总|董|秘|局|处|科|队|组|主|长|管|师|生|士|官|员|导|监|裁|席)'
            r'(?![\u4e00-\u9fa5])'
        )
        for match in short_title_pattern.finditer(text):
            full = match.group(1) + match.group(2)
            entities.append(Entity(
                text=full, entity_type='PER',
                start=match.start(), end=match.end(),
                confidence=0.86
            ))

        quoted_name_pattern = re.compile(
            r'[，。！？；：\s]([\u4e00-\u9fa5]{2,3})(说|表示|认为|指出|强调|称|提到|透露|声称|道|讲|告诉|介绍|回答|回应|表态)'
        )
        for match in quoted_name_pattern.finditer(text):
            name = match.group(1)
            if name[0] in self.person_surnames:
                entities.append(Entity(
                    text=name, entity_type='PER',
                    start=match.start(1), end=match.end(1),
                    confidence=0.86
                ))

        title_prefix_pattern = re.compile(
            r'(总统|总理|主席|省长|市长|县长|局长|处长|科长|校长|院长|教授|博士|工程师|总监|总裁|经理|主任|董事长|首席执行官|总书记|议长|酋长|司令|将军|上校|中校|少校|上尉|中尉|少尉)'
            r'([\u4e00-\u9fa5]{2,3})'
            r'([，。！？；：\s说表示]|$)'
        )
        for match in title_prefix_pattern.finditer(text):
            name = match.group(2)
            if name[0] in self.person_surnames or len(name) >= 2:
                entities.append(Entity(
                    text=name, entity_type='PER',
                    start=match.start(2), end=match.end(2),
                    confidence=0.84
                ))

        return entities

    def _extract_english_entities(self, text: str) -> List[Entity]:
        """提取英文实体"""
        entities = []

        famous_orgs_en = {
            'Google', 'Apple', 'Microsoft', 'Amazon', 'Meta', 'Facebook', 'Tesla', 'NVIDIA',
            'Nvidia', 'Netflix', 'Adobe', 'Oracle', 'SAP', 'IBM', 'Intel', 'AMD', 'Cisco',
            'Samsung', 'Sony', 'Panasonic', 'LG', 'Xiaomi', 'Huawei', 'Honor', 'OnePlus',
            'Realme', 'Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'MSI', 'Razer', 'Logitech',
            'Corsair', 'Steam', 'Nintendo', 'PlayStation', 'Xbox', 'United Nations', 'UN',
            'World Health Organization', 'WHO', 'Congress', 'Parliament',
            'Supreme Court', 'Wall Street', 'Silicon Valley', 'Hollywood', 'Broadway'
        }
        for org in famous_orgs_en:
            for start, end in self._find_substring_positions(text, org):
                current = Entity(text=org, entity_type='ORG', start=start, end=end, confidence=0.92)
                entities.append(current)

        title_name_pattern = re.compile(
            r'\b(?:Dr|Mr|Mrs|Ms|Prof|Professor|Sir|Madam|President|CEO|CTO|CFO|VP|Vice|Secretary|Senator|Representative|Ambassador)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b'
        )
        for match in title_name_pattern.finditer(text):
            name = match.group()
            skip = False
            for e in entities:
                if not (match.end() <= e.start or match.start() >= e.end):
                    skip = True
                    break
            if not skip:
                entities.append(Entity(
                    text=name, entity_type='PER',
                    start=match.start(), end=match.end(),
                    confidence=0.88
                ))

        for match in self.english_name_pattern.finditer(text):
            name = match.group()
            skip = False
            for e in entities:
                if not (match.end() <= e.start or match.start() >= e.end):
                    skip = True
                    break
            if skip:
                continue
            words = name.split()
            if 2 <= len(words) <= 3:
                if all(w[0].isupper() for w in words):
                    entities.append(Entity(
                        text=name, entity_type='PER',
                        start=match.start(), end=match.end(),
                        confidence=0.85
                    ))

        for match in self.english_org_pattern.finditer(text):
            matched = match.group()
            if 3 <= len(matched.split()) <= 6:
                skip = False
                for e in entities:
                    if not (match.end() <= e.start or match.start() >= e.end):
                        skip = True
                        break
                if not skip:
                    entities.append(Entity(
                        text=matched, entity_type='ORG',
                        start=match.start(), end=match.end(),
                        confidence=0.82
                    ))

        for match in self.english_location_pattern.finditer(text):
            matched = match.group()
            if 2 <= len(matched.split()) <= 5:
                skip = False
                for e in entities:
                    if not (match.end() <= e.start or match.start() >= e.end):
                        skip = True
                        break
                if not skip:
                    entities.append(Entity(
                        text=matched, entity_type='LOC',
                        start=match.start(), end=match.end(),
                        confidence=0.80
                    ))

        english_times = [
            (r'\b\d{4}-\d{2}-\d{2}\b', 'TIME', 0.95),
            (r'\b\d{2}/\d{2}/\d{4}\b', 'TIME', 0.95),
            (r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b', 'TIME', 0.93),
            (r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}(?:,\s+\d{4})?\b', 'TIME', 0.90),
            (r'\b\d{1,2}:\d{2}(:\d{2})?\s*(?:AM|PM|am|pm)?\b', 'TIME', 0.92),
            (r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b', 'TIME', 0.92),
            (r'\b(?:today|tomorrow|yesterday)\b', 'TIME', 0.90),
            (r'\b(?:Spring|Summer|Autumn|Winter|Fall)\b', 'TIME', 0.85),
            (r'(?<!\d)(?:19|20)\d{2}(?!\d)', 'TIME', 0.88),
        ]

        for pattern, etype, conf in english_times:
            for match in re.finditer(pattern, text):
                matched = match.group()
                if etype == 'TIME' and matched.isdigit():
                    if not (1900 <= int(matched) <= 2100):
                        continue
                skip = False
                for e in entities:
                    if not (match.end() <= e.start or match.start() >= e.end):
                        skip = True
                        break
                if not skip:
                    entities.append(Entity(
                        text=matched, entity_type=etype,
                        start=match.start(), end=match.end(),
                        confidence=conf
                    ))

        return entities

    def _remove_overlaps(self, entities: List[Entity]) -> List[Entity]:
        if not entities:
            return []

        entities.sort(key=lambda x: (x.start, -(x.end - x.start), -x.confidence))

        result = []
        last_end = -1
        last_type = None

        for entity in entities:
            if entity.start >= last_end:
                result.append(entity)
                last_end = entity.end
                last_type = entity.entity_type
            else:
                if result:
                    prev = result[-1]
                    prev_len = prev.end - prev.start
                    curr_len = entity.end - entity.start
                    confidence_diff = entity.confidence - prev.confidence

                    if confidence_diff > 0.10:
                        result[-1] = entity
                        last_end = entity.end
                        last_type = entity.entity_type
                    elif (prev_len <= 2 or prev.entity_type == 'LOC' and
                          (prev.text.startswith('在') or prev.text.startswith('于') or
                           prev.text.startswith('是') or prev.text.startswith('到'))):
                        result[-1] = entity
                        last_end = entity.end
                        last_type = entity.entity_type
                    elif (entity.entity_type == 'PER' and prev.entity_type == 'LOC' and
                          len(entity.text) <= 4 and entity.confidence >= 0.85):
                        result[-1] = entity
                        last_end = entity.end
                        last_type = entity.entity_type
                    elif (entity.entity_type == 'TIME' and prev.entity_type != 'TIME' and
                          entity.confidence >= 0.90):
                        result[-1] = entity
                        last_end = entity.end
                        last_type = entity.entity_type
                    elif curr_len > prev_len * 1.5 and confidence_diff > -0.05:
                        result[-1] = entity
                        last_end = entity.end
                        last_type = entity.entity_type

        return result

    def _merge_adjacent_entities(self, entities: List[Entity], text: str) -> List[Entity]:
        """合并相邻的同类型实体（仅用空格或标点分隔）"""
        if len(entities) < 2:
            return entities

        entities.sort(key=lambda x: x.start)
        merged = []
        i = 0

        while i < len(entities):
            current = entities[i]
            j = i + 1

            while j < len(entities):
                next_ent = entities[j]
                if (next_ent.entity_type == current.entity_type and
                        next_ent.start > current.end and
                        next_ent.start - current.end <= 2):
                    separator = text[current.end:next_ent.start]
                    if separator.strip() in ['', '·', '•', '-', '—', '·']:
                        merged_text = text[current.start:next_ent.end]
                        avg_confidence = (current.confidence + next_ent.confidence) / 2
                        current = Entity(
                            text=merged_text, entity_type=current.entity_type,
                            start=current.start, end=next_ent.end,
                            confidence=avg_confidence
                        )
                        j += 1
                        continue
                break

            merged.append(current)
            i = j

        return merged

    def _post_process_entities(self, entities: List[Entity], text: str) -> List[Entity]:
        """实体后处理：过滤不合理结果"""
        filtered = []
        for e in entities:
            if e.start < 0 or e.end > len(text):
                continue
            if e.end <= e.start:
                continue

            actual_text = text[e.start:e.end]
            if actual_text != e.text:
                e.text = actual_text

            if len(e.text.strip()) == 0:
                continue

            if len(e.text) > 30 and e.entity_type not in ['ORG', 'LOC']:
                continue

            if e.entity_type in ['ORG', 'LOC', 'NOUN']:
                has_chinese = bool(re.search(r'[\u4e00-\u9fa5]', e.text))
                has_english = bool(re.search(r'[a-zA-Z]', e.text))
                if not has_chinese and not has_english and e.entity_type != 'TIME':
                    continue

            if e.confidence < 0.5:
                e.confidence = 0.5 + min(0.4, len(e.text) * 0.015)

            e.confidence = min(0.99, e.confidence)
            filtered.append(e)

        return filtered

    def recognize(self, text: str) -> Dict:
        """
        实体识别主函数

        Args:
            text: 输入文本

        Returns:
            识别结果字典，包含实体列表、统计信息等
        """
        if not text or not text.strip():
            return {
                'entities': [],
                'statistics': {t: 0 for t in self.ENTITY_TYPES.keys()},
                'total_count': 0,
                'highlight_html': '',
                'language': 'chinese'
            }

        lang = self.detect_language(text)
        all_entities = []

        all_entities.extend(self._extract_dict_entities(text))
        all_entities.extend(self._extract_strict_regex_entities(text))
        all_entities.extend(self._extract_jieba_entities(text))
        all_entities.extend(self._extract_person_with_suffix(text))

        if lang == 'english':
            all_entities.extend(self._extract_english_entities(text))

        all_entities = self._post_process_entities(all_entities, text)
        all_entities = self._remove_overlaps(all_entities)
        all_entities = self._merge_adjacent_entities(all_entities, text)
        all_entities = self._post_process_entities(all_entities, text)
        all_entities.sort(key=lambda x: x.start)

        stats = {t: 0 for t in self.ENTITY_TYPES.keys()}
        for entity in all_entities:
            if entity.entity_type in stats:
                stats[entity.entity_type] += 1

        highlight_html = self._generate_highlight_html(text, all_entities)

        return {
            'entities': [
                {
                    'text': e.text,
                    'type': e.entity_type,
                    'type_name': e.type_name,
                    'start': e.start,
                    'end': e.end,
                    'confidence': round(e.confidence, 4),
                    'color': self.ENTITY_TYPES[e.entity_type]['color']
                }
                for e in all_entities
            ],
            'statistics': stats,
            'total_count': len(all_entities),
            'highlight_html': highlight_html,
            'language': lang
        }

    def _generate_highlight_html(self, text: str, entities: List[Entity]) -> str:
        """生成高亮显示的HTML"""
        if not entities:
            return text

        entities_sorted = sorted(entities, key=lambda x: x.start, reverse=True)

        result = text
        for entity in entities_sorted:
            if entity.start < 0 or entity.end > len(result):
                continue
            color = self.ENTITY_TYPES[entity.entity_type]['color']
            type_name = entity.type_name

            before = result[:entity.start]
            entity_text = result[entity.start:entity.end]
            after = result[entity.end:]

            highlight_span = (
                f'<span class="entity-highlight entity-{entity.entity_type.lower()}" '
                f'style="background-color: {color}20; color: {color}; '
                f'padding: 2px 6px; border-radius: 4px; border-bottom: 2px solid {color}; '
                f'font-weight: 500; cursor: pointer;" '
                f'title="{type_name}: {entity.confidence:.0%}">'
                f'{entity_text}<sub style="font-size: 10px; margin-left: 2px;">{type_name}</sub>'
                f'</span>'
            )

            result = before + highlight_span + after

        return result

    def get_entity_type_info(self) -> Dict:
        """获取实体类型信息"""
        return {
            code: {
                'name': info['name'],
                'color': info['color']
            }
            for code, info in self.ENTITY_TYPES.items()
        }
