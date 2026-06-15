#!/usr/bin/env python3
"""One-shot: create remaining 红楼梦 character pages from audit/seed backlog."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHAR_DIR = ROOT / "src/content/characters/红楼梦"

CHARACTERS: dict[str, dict] = {
    "门子": {
        "name": "门子", "gender": "男", "faction": "应天府", "first_appear": "第4回",
        "status": "配角", "tags": ["清客", "护官符"], "weight": 42,
        "summary": "原葫芦庙小沙弥，后充贾雨村门子；第4回献护官符、共谋葫芦案，终被远充。",
        "relations": [{"target": "贾雨村", "type": "主仆", "role": "旧识"}],
        "性格": "世故圆滑、谙熟官场", "喜好": ["护官符", "葫芦庙旧事"],
        "identity": "应天府衙门子，本是葫芦庙小沙弥，火后蓄发充役。",
        "plots": ["第4回：献本省护官符，劝雨村徇情了结薛蟠案。"],
    },
    "警幻仙子": {
        "name": "警幻仙子", "gender": "女", "faction": "太虚幻境", "first_appear": "第5回",
        "status": "重要", "tags": ["神话", "太虚幻境"], "weight": 55,
        "summary": "太虚幻境司主；第5回引宝玉阅金陵十二钗册、演红楼梦曲。",
        "relations": [{"target": "贾宝玉", "type": "师徒", "role": "引梦"}],
        "性格": "仙风道骨、警悟世人", "喜好": ["太虚幻境", "薄命册"],
        "identity": "太虚幻境离恨天之上、灌愁海之中，司「情」之仙。",
        "plots": ["第5回：接宝玉入幻，示十二钗正册、副册、又副册及《红楼梦》曲。"],
    },
    "贾璜": {
        "name": "贾璜", "aliases": ["璜大奶奶"], "gender": "男", "faction": "金陵贾氏",
        "first_appear": "第10回", "status": "配角", "tags": ["族亲"], "weight": 28,
        "summary": "金陵贾氏远房「玉」字辈，妻金氏；第10回金荣学房之争，靠宁荣接济度日。",
        "relations": [
            {"target": "贾珍", "type": "同僚", "role": "族亲"},
            {"target": "金荣", "type": "同僚", "role": "姑侄"},
        ],
        "性格": "势薄族亲、仰仗资助", "喜好": ["请安", "奉承凤姐"],
        "identity": "贾家玉字辈远房，产业微薄，常至宁荣请安。",
        "plots": ["第10回：金荣与秦钟争闹，璜大奶奶欲找珍大奶奶评理。"],
    },
    "云光": {
        "name": "云光", "aliases": ["长安守备"], "gender": "男", "faction": "长安",
        "first_appear": "第15回", "status": "配角", "tags": ["官员"], "weight": 30,
        "summary": "长安守备，与贾珍往来；第15–16回张金哥案中受凤姐三千两，退前聘。",
        "relations": [{"target": "王熙凤", "type": "同僚", "role": "受贿"}],
        "性格": "贪财畏势", "喜好": ["官场应酬"],
        "identity": "长安府守备，张金哥原聘之家。",
        "plots": ["第16回：凤姐得云光回信，守备忍气吞声受前聘之物；金哥自缢，守备之子投河。"],
    },
    "石呆子": {
        "name": "石呆子", "gender": "男", "faction": "都中", "first_appear": "第48回",
        "status": "配角", "tags": ["平民"], "weight": 32,
        "summary": "都中古扇藏家，家贫守扇；第48回贾赦托贾雨村夺扇，石呆子下狱身亡。",
        "relations": [{"target": "贾赦", "type": "敌对", "role": "夺扇"}],
        "性格": "清贫守扇、不肯出让", "喜好": ["古扇收藏"],
        "identity": "都中穷民，蓄二十把古扇，为贾赦所觊觎。",
        "plots": ["第48回：雨村讹诈，石呆子下狱，扇归贾赦。"],
    },
    "张三": {
        "name": "张三", "gender": "男", "faction": "都中", "first_appear": "第86回",
        "status": "配角", "tags": ["平民"], "weight": 24,
        "summary": "酒店中被薛蟠误伤者；第86回起薛蟠刑部案牵连人物。",
        "relations": [{"target": "薛蟠", "type": "敌对", "role": "误伤"}],
        "性格": "酒肆行人", "喜好": [],
        "identity": "都中酒肆中人，薛蟠案原告相关。",
        "plots": ["第86回：薛蟠打死张三，发刑部问拟。"],
    },
    "吴良": {
        "name": "吴良", "gender": "男", "faction": "都中", "first_appear": "第86回",
        "status": "配角", "tags": ["酒保"], "weight": 22,
        "summary": "当槽酒保，薛蟠案人证；第86回刑部审理张三案时作证。",
        "relations": [{"target": "薛蟠", "type": "同僚", "role": "见证"}],
        "性格": "当槽酒保", "喜好": [],
        "identity": "酒店当槽酒保。",
        "plots": ["第86回：薛蟠案中人证。"],
    },
    "神瑛侍者": {
        "name": "神瑛侍者", "gender": "男", "faction": "赤瑕宫", "first_appear": "第1回",
        "status": "重要", "tags": ["神话", "石头"], "weight": 50,
        "summary": "赤瑕宫侍者，石头/通灵宝玉前世；第1回下凡历劫，与绛珠还泪神话相系。",
        "relations": [
            {"target": "绛珠仙子", "type": "情人", "role": "还泪"},
            {"target": "贾宝玉", "type": "朋友", "role": "前身"},
        ],
        "性格": "凡心既炽、欲历红尘", "喜好": ["赤瑕宫", "通灵"],
        "identity": "赤瑕宫神瑛侍者，后投胎为宝玉口衔之玉。",
        "plots": ["第1回：与绛珠仙子神话并提，石头下凡历劫。"],
    },
    "渺渺真人": {
        "name": "渺渺真人", "gender": "男", "faction": "太虚幻境", "first_appear": "第1回",
        "status": "配角", "tags": ["神话", "道士"], "weight": 38,
        "summary": "与茫茫大士同现大荒山，点化顽石；第1回引石头入红尘之议。",
        "relations": [{"target": "茫茫大士", "type": "朋友", "role": "同游"}],
        "性格": "仙风道骨", "喜好": ["点化顽石"],
        "identity": "骨骼不凡之仙真，与茫茫大士偕行。",
        "plots": ["第1回：至青埂峰下与僧道谈红尘，顽石求下凡。"],
    },
    "茫茫大士": {
        "name": "茫茫大士", "gender": "男", "faction": "太虚幻境", "first_appear": "第1回",
        "status": "配角", "tags": ["神话", "和尚"], "weight": 38,
        "summary": "与渺渺真人同现，携通灵入红尘；后化癞头和尚还玉。",
        "relations": [{"target": "渺渺真人", "type": "朋友", "role": "同游"}],
        "性格": "憨笑点化", "喜好": ["携石入世"],
        "identity": "丰神迥异之僧，与渺渺真人一对。",
        "plots": ["第1回：点化顽石；后文化癞头和尚还玉。"],
    },
    "绛珠仙子": {
        "name": "绛珠仙子", "gender": "女", "faction": "太虚幻境", "first_appear": "第1回",
        "status": "重要", "tags": ["神话", "还泪"], "weight": 48,
        "summary": "三生石畔绛珠草，受神瑛甘露之恩，誓还泪于人间；黛玉神话前身。",
        "relations": [
            {"target": "神瑛侍者", "type": "情人", "role": "还泪"},
            {"target": "林黛玉", "type": "朋友", "role": "化身"},
        ],
        "性格": "情痴还泪", "喜好": ["三生石", "甘露"],
        "identity": "西方灵河岸上三生石畔之绛珠仙草化身。",
        "plots": ["第1回：还泪神话，与神瑛侍者并提。"],
    },
    "锦乡侯": {
        "name": "锦乡侯", "gender": "男", "faction": "王府", "first_appear": "第71回",
        "status": "配角", "tags": ["侯爵", "四王八公"], "weight": 35,
        "summary": "四王八公之一；第71回贾母八旬寿宴，其诰命与临昌伯诰命陪席。",
        "relations": [{"target": "贾母", "type": "同僚", "role": "寿宴"}],
        "性格": "世袭侯爵", "喜好": ["寿宴应酬"],
        "identity": "锦乡侯，与贾家世交。",
        "plots": ["第71回：贾母寿宴，锦乡侯诰命陪客。"],
    },
    "镇国公": {
        "name": "镇国公", "gender": "男", "faction": "王府", "first_appear": "第13回",
        "status": "配角", "tags": ["公爵", "四王八公"], "weight": 35,
        "summary": "四王八公之一；第13回可卿丧仪，镇国公、理国公等皆祭。",
        "relations": [{"target": "秦可卿", "type": "朋友", "role": "路祭"}],
        "性格": "世袭国公", "喜好": ["丧祭"],
        "identity": "镇国公，与宁荣同列「四王八公」。",
        "plots": ["第13回：可卿大丧，各王公皆送祭。"],
    },
    "东平郡王": {
        "name": "东平郡王", "gender": "男", "faction": "王府", "first_appear": "第14回",
        "status": "配角", "tags": ["郡王", "四王八公"], "weight": 34,
        "summary": "四王八公之一；第14回可卿路祭，与北静、南安、西宁诸王同列。",
        "relations": [
            {"target": "北静王", "type": "同僚", "role": "王府"},
            {"target": "南安郡王", "type": "同僚", "role": "王府"},
        ],
        "性格": "郡王仪从", "喜好": ["路祭"],
        "identity": "东平郡王，四王八公之一。",
        "plots": ["第14回：可卿路祭，诸王齐至。"],
    },
    "守备": {
        "name": "守备", "aliases": ["长安守备"], "gender": "男", "faction": "长安",
        "first_appear": "第16回", "status": "配角", "tags": ["官员"], "weight": 26,
        "summary": "张金哥原聘之父（与云光同案）；第16回受凤姐之贿退聘，致金哥自缢。",
        "relations": [
            {"target": "张金哥", "type": "父子", "role": "退聘"},
            {"target": "王熙凤", "type": "同僚", "role": "受贿"},
        ],
        "性格": "爱势贪财", "喜好": [],
        "identity": "长安守备，张金哥之父。",
        "plots": ["第16回：忍气吞声受前聘之物；女儿自缢，其子投河。"],
    },
    "贾源": {
        "name": "贾源", "aliases": ["荣国公"], "gender": "男", "faction": "荣国府",
        "first_appear": "第2回", "status": "配角", "tags": ["始祖", "荣国公"], "weight": 40,
        "summary": "荣国公，宁荣二公之弟；封赠荣国公，荣府始祖，已故。",
        "relations": [
            {"target": "贾演", "type": "兄弟", "role": "宁荣"},
            {"target": "贾代善", "type": "父子", "role": "世袭"},
        ],
        "性格": "开国元勋", "喜好": [],
        "identity": "荣国公贾源，宁国公贾演之弟，荣府始祖。",
        "plots": ["第2回：冷子兴演说荣宁由来，源、演兄弟并提。"],
    },
    "贾演": {
        "name": "贾演", "aliases": ["宁国公"], "gender": "男", "faction": "宁国府",
        "first_appear": "第2回", "status": "配角", "tags": ["始祖", "宁国公"], "weight": 40,
        "summary": "宁国公，宁荣二公之兄；封赠宁国公，宁府始祖，已故。",
        "relations": [{"target": "贾源", "type": "兄弟", "role": "宁荣"}],
        "性格": "开国元勋", "喜好": [],
        "identity": "宁国公贾演，荣国公贾源之兄，宁府始祖。",
        "plots": ["第2回：冷子兴演说，演、源并提；第4回护官符「宁国荣国二公之后」。"],
    },
    "贾代善": {
        "name": "贾代善", "gender": "男", "faction": "荣国府", "first_appear": "第2回",
        "status": "配角", "tags": ["荣国公", "已故"], "weight": 38,
        "summary": "贾母之夫，袭荣国公；已故，贾母称「老太爷」。",
        "relations": [
            {"target": "贾母", "type": "夫妻"},
            {"target": "贾源", "type": "父子", "role": "世袭"},
        ],
        "性格": "荣公遗风", "喜好": [],
        "identity": "荣国公贾代善，贾母之夫，贾赦、贾政之父。",
        "plots": ["第2回：冷子兴提及代善；后文贾母屡称「你爷爷」「老太爷」。"],
    },
    "贾敏": {
        "name": "贾敏", "gender": "女", "faction": "荣国府", "first_appear": "第2回",
        "status": "重要", "tags": ["小姐", "已故"], "weight": 45,
        "summary": "贾母幼女，林黛玉之母，林如海之妻；第2回已亡，黛玉依外家。",
        "relations": [
            {"target": "贾母", "type": "母子"},
            {"target": "林黛玉", "type": "母子"},
            {"target": "贾政", "type": "兄弟", "role": "兄妹"},
            {"target": "王夫人", "type": "朋友", "role": "小姑嫂"},
        ],
        "性格": "千金小姐、早亡", "喜好": [],
        "identity": "荣国府贾敏，贾母之女，黛玉之母。",
        "plots": ["第2回：林如海荐雨村，言贾敏为内兄之妹；第3回黛玉入府。"],
    },
    "贾敷": {
        "name": "贾敷", "gender": "男", "faction": "宁国府", "first_appear": "第2回",
        "status": "配角", "tags": ["族亲", "已故"], "weight": 24,
        "summary": "贾珍之兄，早亡；其子贾蓉为珍之侄继嗣。",
        "relations": [
            {"target": "贾珍", "type": "兄弟"},
            {"target": "贾蓉", "type": "父子", "role": "早亡"},
        ],
        "性格": "早亡", "喜好": [],
        "identity": "宁国府贾敷，贾珍之兄，蓉之父（早亡）。",
        "plots": ["第2回：冷子兴演说，敷早亡，珍继宁国府。"],
    },
    "卜世仁": {
        "name": "卜世仁", "aliases": ["卜老"], "gender": "男", "faction": "都中",
        "first_appear": "第24回", "status": "配角", "tags": ["市井"], "weight": 26,
        "summary": "卜老世仁，卜银姐之舅；第24回贾芸求赊冰片麝香，被其奚落。",
        "relations": [{"target": "贾芸", "type": "同僚", "role": "赊欠"}],
        "性格": "市侩吝啬", "喜好": ["香料铺"],
        "identity": "都中药店主人，贾芸母舅。",
        "plots": ["第24回：贾芸求赊，世仁推托。"],
    },
    "忠顺亲王": {
        "name": "忠顺亲王", "gender": "男", "faction": "王府", "first_appear": "第33回",
        "status": "重要", "tags": ["亲王"], "weight": 42,
        "summary": "忠顺府亲王爷；第33–34回因琪官事索人，贾政笞宝玉。",
        "relations": [{"target": "贾宝玉", "type": "敌对", "role": "索琪官"}],
        "性格": "王府威严", "喜好": ["优伶琪官"],
        "identity": "忠顺亲王府，与贾府素无来往。",
        "plots": ["第33回：长史官来索琪官；贾政怒打宝玉。"],
    },
    "戴权": {
        "name": "戴权", "gender": "男", "faction": "大明宫", "first_appear": "第13回",
        "status": "配角", "tags": ["太监", "钦天监"], "weight": 32,
        "summary": "大明宫太监、掌宫内仪礼司正堂；第13回可卿丧，代贾珍求义冢。",
        "relations": [{"target": "贾珍", "type": "同僚", "role": "内侍"}],
        "性格": "内官仪礼", "喜好": ["钦天监"],
        "identity": "掌宫内仪礼司正堂之太监。",
        "plots": ["第13回：可卿丧仪，戴权传旨，赐义冢。"],
    },
    "林四娘": {
        "name": "林四娘", "gender": "女", "faction": "青州", "first_appear": "第78回",
        "status": "配角", "tags": ["诗典", "姽婳"], "weight": 30,
        "summary": "青州恒王武库官姬，起义兵殉国；第78回宝玉作《姽婳词》吊之。",
        "relations": [{"target": "贾宝玉", "type": "朋友", "role": "吊唁"}],
        "性格": "巾帼英烈", "喜好": ["诗剑"],
        "identity": "青州恒王武库官林四娘，起义兵殉国。",
        "plots": ["第78回：宝玉《姽婳词》吊林四娘。"],
    },
    "香怜": {
        "name": "香怜", "gender": "男", "faction": "贾府家塾", "first_appear": "第9回",
        "status": "配角", "tags": ["学童"], "weight": 22,
        "summary": "贾府家塾学童；第9回与玉爱等同塾，金荣、秦钟之争相关。",
        "relations": [{"target": "玉爱", "type": "朋友", "role": "同窗"}],
        "性格": "学童", "喜好": ["家塾"],
        "identity": "贾府家塾附学童子。",
        "plots": ["第9回：与玉爱等同在塾中，金荣秦钟之争。"],
    },
    "玉爱": {
        "name": "玉爱", "gender": "男", "faction": "贾府家塾", "first_appear": "第9回",
        "status": "配角", "tags": ["学童"], "weight": 22,
        "summary": "贾府家塾学童；第9回与香怜等同塾。",
        "relations": [{"target": "香怜", "type": "朋友", "role": "同窗"}],
        "性格": "学童", "喜好": ["家塾"],
        "identity": "贾府家塾附学童子。",
        "plots": ["第9回：与香怜等同在塾中。"],
    },
    "茄官": {
        "name": "茄官", "gender": "女", "faction": "梨香院", "first_appear": "第58回",
        "status": "配角", "tags": ["戏官", "丫鬟"], "weight": 26,
        "summary": "梨香院十二个女伶之一；第58回遣发时与芳官等同列。",
        "relations": [{"target": "芳官", "type": "朋友", "role": "戏班"}],
        "性格": "小戏官", "喜好": ["梨香院"],
        "identity": "梨香院女伶，后随众戏官遣散或留用。",
        "plots": ["第58回：老太妃薨，议遣发女伶，茄官等同列。"],
    },
    "赵亦华": {
        "name": "赵亦华", "gender": "男", "faction": "都中", "first_appear": "第52回",
        "status": "配角", "tags": ["清客"], "weight": 24,
        "summary": "清客；第52回与单聘仁等同席，陪贾政清客。",
        "relations": [{"target": "单聘仁", "type": "朋友", "role": "清客"}],
        "性格": "清客陪席", "喜好": ["应酬"],
        "identity": "贾家清客之一。",
        "plots": ["第52回：与单聘仁等清客同列。"],
    },
    "钱槐": {
        "name": "钱槐", "gender": "男", "faction": "赵姨娘房", "first_appear": "第60回",
        "status": "配角", "tags": ["小厮", "赵姨娘"], "weight": 26,
        "summary": "赵姨娘内侄；第60回唆使作歹，与赵姨娘、贾环一党。",
        "relations": [
            {"target": "赵姨娘", "type": "主仆", "role": "内侄"},
            {"target": "贾环", "type": "朋友", "role": "唆使"},
        ],
        "性格": "唆使作歹", "喜好": ["赵姨娘房"],
        "identity": "赵姨娘之内侄，荣府小厮。",
        "plots": ["第60回：与赵姨娘、贾环相关作歹。"],
    },
    "王成": {
        "name": "王成", "gender": "男", "faction": "乡野", "first_appear": "第6回",
        "status": "配角", "tags": ["亲家"], "weight": 28,
        "summary": "王狗儿之父，刘姥姥亲家；第6回已死，狗儿家道中落。",
        "relations": [
            {"target": "王狗儿", "type": "父子"},
            {"target": "刘姥姥", "type": "同僚", "role": "亲家"},
        ],
        "性格": "乡绅之后", "喜好": [],
        "identity": "王狗儿之父，与刘家为亲家，已故。",
        "plots": ["第6回：刘姥姥进荣府，言王成与狗儿家世。"],
    },
    "甄应嘉": {
        "name": "甄应嘉", "gender": "男", "faction": "江南甄家", "first_appear": "第114回",
        "status": "配角", "tags": ["官员", "甄家"], "weight": 32,
        "summary": "江南甄家袭职，与贾家世交；第114回蒙恩复职，与贾家命运呼应。",
        "relations": [{"target": "贾政", "type": "朋友", "role": "世交"}],
        "性格": "世宦之家", "喜好": [],
        "identity": "江南甄家，与贾家「真」「假」对照。",
        "plots": ["第114回：甄应嘉蒙恩，与贾家败落对照。"],
    },
    "引泉": {
        "name": "引泉", "gender": "男", "faction": "荣国府", "first_appear": "第24回",
        "status": "配角", "tags": ["小厮"], "weight": 22,
        "summary": "宝玉小厮；第24回与扫花、挑云等在檐上掏雀儿。",
        "relations": [{"target": "贾宝玉", "type": "主仆", "role": "小厮"}],
        "性格": "淘气小厮", "喜好": ["掏雀儿"],
        "identity": "宝玉跟班小厮，与扫花、挑云同列。",
        "plots": ["第24回：与扫花、挑云等掏雀儿。"],
    },
    "挑云": {
        "name": "挑云", "gender": "男", "faction": "荣国府", "first_appear": "第24回",
        "status": "配角", "tags": ["小厮"], "weight": 22,
        "summary": "宝玉小厮；第24回与引泉、扫花等同在书房外当差。",
        "relations": [{"target": "贾宝玉", "type": "主仆", "role": "小厮"}],
        "性格": "淘气小厮", "喜好": ["掏雀儿"],
        "identity": "宝玉跟班小厮。",
        "plots": ["第24回：与引泉、扫花等同列。"],
    },
    "珍珠": {
        "name": "珍珠", "gender": "女", "faction": "贾母房", "first_appear": "第3回",
        "status": "配角", "tags": ["丫鬟"], "weight": 30,
        "summary": "贾母大丫鬟；第29回清虚观等随侍，与鸳鸯、鹦鹉、琥珀同列。",
        "relations": [{"target": "贾母", "type": "主仆"}],
        "性格": "大丫鬟", "喜好": ["贾母房"],
        "identity": "贾母房中丫鬟，与鸳鸯、鹦鹉、琥珀同列。",
        "plots": ["第29回：清虚观，贾母丫头珍珠等同随。"],
    },
    "鹦哥": {
        "name": "鹦哥", "gender": "女", "faction": "贾母房", "first_appear": "第3回",
        "status": "配角", "tags": ["丫鬟"], "weight": 28,
        "summary": "贾母丫鬟；第29回与鸳鸯、珍珠、琥珀同列随侍。",
        "relations": [{"target": "贾母", "type": "主仆"}],
        "性格": "随侍丫鬟", "喜好": ["贾母房"],
        "identity": "贾母房中丫鬟。",
        "plots": ["第29回：清虚观随贾母，鹦哥等同列。"],
    },
    "色空和尚": {
        "name": "色空和尚", "aliases": ["好了歌僧"], "gender": "男", "faction": "太虚幻境",
        "first_appear": "第1回", "status": "配角", "tags": ["神话", "僧"], "weight": 36,
        "summary": "《好了歌》作诵者；第1回点化甄士隐，与《好了歌注》相配。",
        "relations": [{"target": "甄士隐", "type": "师徒", "role": "点化"}],
        "性格": "疯跛僧、点化世人", "喜好": ["好了歌"],
        "identity": "作《好了歌》之僧，程高本或统称「僧」。",
        "plots": ["第1回：甄士隐闻《好了歌》而悟。"],
    },
    "葫芦僧": {
        "name": "葫芦僧", "aliases": ["癞头和尚"], "gender": "男", "faction": "葫芦庙",
        "first_appear": "第1回", "status": "配角", "tags": ["神话", "僧"], "weight": 34,
        "summary": "葫芦庙癞头和尚，与跛足道人同现；第4回回目「葫芦僧乱判」指门子旧身。",
        "relations": [{"target": "门子", "type": "朋友", "role": "前身"}],
        "性格": "疯僧点化", "喜好": ["葫芦庙"],
        "identity": "葫芦庙僧，与跛足道人一对；门子原为葫芦庙沙弥。",
        "plots": ["第1回：与跛足道人同现；第4回葫芦案。"],
    },
}


def _lines_relations(rels: list[dict]) -> list[str]:
    if not rels:
        return ["relations: []"]
    out = ["relations:"]
    for r in rels:
        out.append(f"- target: {r['target']}")
        out.append(f"  type: {r['type']}")
        if role := r.get("role"):
            out.append(f"  role: {role}")
    return out


def render_md(cid: str, spec: dict) -> str:
    tags = spec.get("tags", [])
    hobbies = spec.get("喜好", [])
    plots = spec.get("plots", [])

    lines: list[str] = ["---", f"id: {cid}", "type: character", f"name: {spec['name']}"]
    if aliases := spec.get("aliases"):
        lines.append("aliases:")
        for a in aliases:
            lines.append(f"- {a}")
    lines.extend([
        f"gender: {spec.get('gender', '未知')}",
        "book: 红楼梦",
        f"faction: {spec.get('faction', '')}",
        f"first_appear: {spec.get('first_appear', '')}",
        f"status: {spec.get('status', '配角')}",
        "tags:",
    ])
    for t in tags:
        lines.append(f"- {t}")
    lines.extend(_lines_relations(spec.get("relations", [])))
    lines.extend([
        f"summary: {spec['summary']}",
        f"weight: {spec.get('weight', 25)}",
        f"性格: {spec.get('性格', '')}",
    ])
    if hobbies:
        lines.append("喜好:")
        for h in hobbies:
            lines.append(f"- {h}")
    else:
        lines.append("喜好: []")
    lines.append("---")
    lines.append("## 身份")
    lines.append("")
    lines.append(spec.get("identity", spec["summary"]))
    lines.append("")
    lines.append("## 关键情节")
    lines.append("")
    for p in plots:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## 评析")
    lines.append("")
    lines.append(spec.get("评析", "程高本正文可核；情节见上引回目。"))
    lines.append("")
    lines.append("## 相关")
    lines.append("")
    lines.append(spec.get("related", "见上引回目。"))
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    created = []
    for cid, spec in CHARACTERS.items():
        path = CHAR_DIR / f"{cid}.md"
        path.write_text(render_md(cid, spec), encoding="utf-8")
        created.append(cid)
    print(f"Wrote {len(created)} character pages")


if __name__ == "__main__":
    main()
