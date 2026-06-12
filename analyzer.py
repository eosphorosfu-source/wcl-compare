"""
战斗记录对比分析核心逻辑 (适配 WCL v2 API)
"""
from typing import Dict, List, Tuple
from collections import defaultdict
from dataclasses import dataclass, field

from translation_manager import TranslationManager

# WCL 英文技能/Buff/Boss 名称 → 中文映射
NAME_TRANSLATIONS = {
    # Bosses
    "Val'kyr Twins": "瓦格里双子",
    "Anub'arak": "阿努布雷坎",
    "Lord Jaraxxus": "加拉克苏斯大王",
    "Faction Champions": "阵营冠军",
    "Twin Val'kyr": "瓦格里双子",
    "Icehowl": "冰吼",
    "Northrend Beasts": "诺森德猛兽",
    "Lord Marrowgar": "玛洛加尔领主",
    "Lady Deathwhisper": "亡语者女士",
    "Deathbringer Saurfang": "死亡使者萨鲁法尔",
    "Festergut": "烂肠",
    "Rotface": "腐面",
    "Professor Putricide": "普崔塞德教授",
    "Blood Prince Council": "血王子议会",
    "Blood-Queen Lana'thel": "鲜血女王兰娜瑟尔",
    "Valithria Dreamwalker": "踏梦者瓦莉瑟瑞娅",
    "Sindragosa": "辛达苟萨",
    "The Lich King": "巫妖王",
    "Shadow": "暗影",
    "Discipline": "戒律",
    "Holy": "神圣",
    "Frost": "冰霜",
    "Fire": "火焰",
    "Arcane": "奥术",
    "Retribution": "惩戒",
    "Protection": "防护",
    "Arms": "武器",
    "Fury": "狂怒",
    "Combat": "战斗",
    "Assassination": "刺杀",
    "Subtlety": "敏锐",
    "Beast Mastery": "野兽控制",
    "Marksmanship": "射击",
    "Survival": "生存",
    "Elemental": "元素",
    "Enhancement": "增强",
    "Restoration": "恢复",
    "Balance": "平衡",
    "Feral": "野性",
    "Guardian": "守护",
    "Destruction": "毁灭",
    "Affliction": "痛苦",
    "Demonology": "恶魔学识",
    "Blood": "鲜血",
    "Unholy": "邪恶",
    "Brewmaster": "酒仙",
    "Mistweaver": "织雾",
    "Windwalker": "踏风",
    "Havoc": "浩劫",
    "Vengeance": "复仇",
    "Devastation": "湮灭",
    "Preservation": "恩护",
    "Augmentation": "增辉",
    "Outlaw": "狂徒",
    # Classes
    "Mage": "法师",
    "Warlock": "术士",
    "Priest": "牧师",
    "Paladin": "圣骑士",
    "Druid": "德鲁伊",
    "Rogue": "潜行者",
    "Warrior": "战士",
    "Hunter": "猎人",
    "Shaman": "萨满祭司",
    "DeathKnight": "死亡骑士",
    "Death Knight": "死亡骑士",
    # Spells - Shadow Priest
    "Mind Flay": "精神鞭笞",
    "Vampiric Touch": "吸血鬼之触",
    "Shadow Word: Pain": "暗言术：痛",
    "Shadow Word: Death": "暗言术：灭",
    "Devouring Plague": "噬灵疫病",
    "Improved Devouring Plague": "强化噬灵疫病",
    "Mind Blast": "心灵震爆",
    "Shadowfiend": "暗影恶魔",
    "Shadowfiend Melee": "暗影恶魔攻击",
    "Mind Trauma": "心灵创伤",
    "Shadow Weaving": "暗影交织",
    "Shadow Word: Ruin": "暗言术：渊",
    "Abyssal Collapse": "坍缩深渊",
    "Death's Mercy": "死神慈悲",
    "Surge of Speed": "疾速奔腾",
    "Improved Spirit Tap": "强化精神分流",
    "Speed": "加速",
    "Chakra": "圣言",
    "Dark Essence": "黑暗精粹",
    "Dark Reaping": "黑暗收割",
    "Dispersion": "消散",
    "Psychic Scream": "心灵尖啸",
    "Silence": "沉默",
    "Fade": "渐隐",
    "Power Word: Shield": "真言术：盾",
    "Vampiric Embrace": "吸血鬼的拥抱",
    "Inner Fire": "心灵之火",
    "Power Infusion": "能量灌注",
    "Hymn of Hope": "希望赞歌",
    "Divine Hymn": "神圣赞美诗",
    "Fear Ward": "防护恐惧结界",
    "Shackle Undead": "束缚亡灵",
    "Mass Dispel": "群体驱散",
    "Shadow Protection": "暗影防护",
    "Prayer of Fortitude": "坚韧祷言",
    "Prayer of Spirit": "精神祷言",
    "Renewed Hope": "新生希望",
    "Guarded by the Light": "守护者的力量",
    "Divine Sacrifice": "神圣牺牲",
    "Horn of Winter": "寒冬号角",
    "Leader of the Pack": "兽群领袖",
    "Leader of the Pack(Physical)": "兽群领袖(物理)",
    "Leader of the Pack(Spell)": "兽群领袖(法术)",
    "Totem of Wrath": "天怒图腾",
    "Flametongue Totem": "火舌图腾",
    "Wrath of Air Totem": "空气之怒图腾",
    "Mana Spring Totem": "法力之泉图腾",
    "Heroism": "英勇",
    "Bloodlust": "嗜血",
    "Battle Shout": "战斗怒吼",
    "Commanding Shout": "命令怒吼",
    "Blessing of Kings": "王者祝福",
    "Greater Blessing of Kings": "强效王者祝福",
    "Blessing of Might": "力量祝福",
    "Greater Blessing of Might": "强效力量祝福",
    "Blessing of Wisdom": "智慧祝福",
    "Greater Blessing of Wisdom": "强效智慧祝福",
    "Mark of the Wild": "野性印记",
    "Gift of the Wild": "野性赐福",
    "Arcane Brilliance": "奥术光辉",
    "Arcane Intellect": "奥术智慧",
    "Prayer of Shadow Protection": "暗影防护祷言",
    "Lightweave": "亮纹",
    "Black Magic": "黑魔法",
    "Berserking": "狂暴",
    "Hyperspeed Acceleration": "超级加速",
    "Greatness": "伟大",
    "Emerald Vigor": "翡翠活力",
    "Speed of Light": "光速",
    "Essence of the Blood Queen": "鲜血女王精华",
    "Swarming Shadows": "蜂拥暗影",
    "Frostbolt": "寒冰箭",
    "Frostfire Bolt": "霜火之箭",
    "Deep Freeze": "深度冻结",
    "Waterbolt": "水箭",
    "Mirror Image": "镜像",
    "Icy Veins": "冰冷血脉",
    "Summon Water Elemental": "召唤水元素",
    "Rune Weapon": "符文武器",
    "Death Coil": "死亡缠绕",
    "Scourge Strike": "天灾打击",
    "Obliterate": "湮灭",
    "Frost Strike": "冰霜打击",
    "Howling Blast": "凛风冲击",
    "Icy Touch": "冰触",
    "Plague Strike": "瘟疫打击",
    "Blood Strike": "鲜血打击",
    "Heart Strike": "心脏打击",
    "Death Strike": "灵界打击",
    "Pestilence": "传染",
    "Blood Boil": "血液沸腾",
    "Dancing Rune Weapon": "符文刃舞",
    "Ghoul": "食尸鬼",
    "Raise Dead": "亡者复生",
    "Army of the Dead": "亡者大军",
    "Anti-Magic Shell": "反魔法护罩",
    "Icebound Fortitude": "冰封之韧",
    "Vampiric Blood": "吸血鬼之血",
    "Unholy Frenzy": "邪恶狂热",
    "Bone Shield": "白骨之盾",
    "Hysteria": "狂热",
    # Buffs / Debuffs
    "Ancestral Fortitude": "先祖坚韧",
    "Demonic Pact": "恶魔契约",
    "Diplomacy": "狮心",
    "Divine Guardian": "神圣守护者",
    "Earthliving": "大地生命",
    "Flask of the Frost Wyrm": "冰霜巨龙合剂",
    "Moonkin Aura": "枭兽光环",
    "Nitro Boosts": "硝基加速",
    "Rejuvenation": "回春术",
    "Shadowy Insight": "暗影洞察",
    "Well Fed": "进食充分",
    "Wild Growth": "野性成长",
    "Exhaustion": "精疲力竭",
    "Powering Up": "能量强化",
    "Weakened Soul": "虚弱灵魂",
    "Greater Blessing of Kings": "强效王者祝福",
    "Renewed Hope": "新生希望",
    "Guarded by the Light": "守护者的力量",
    "Illustration of the Dragon Soul": "龙魂图典",
    "Unstable Currents": "不稳定电流",
    "Light Essence": "光明精粹",
    # Mage
    "Arcane Blast": "奥术冲击",
    "Arcane Missiles": "奥术飞弹",
    "Arcane Power": "奥术强化",
    "Living Bomb": "活动炸弹",
    "Hot Streak": "炽热连击",
    "Brain Freeze": "思维冷却",
    "Fingers of Frost": "寒冰指",
    "Missile Barrage": "飞弹速射",
    "Combustion": "燃烧",
    "Evocation": "唤醒",
    "Ice Barrier": "寒冰护体",
    "Mage Armor": "法师护甲",
    "Molten Armor": "熔岩护甲",
    "Ice Armor": "冰甲术",
    "Presence of Mind": "气定神闲",
    "Ice Lance": "冰枪术",
    "Scorch": "灼烧",
    "Fireball": "火球术",
    "Pyroblast": "炎爆术",
    "Flamestrike": "烈焰风暴",
    "Blizzard": "暴风雪",
    "Cone of Cold": "冰锥术",
    "Frost Nova": "冰霜新星",
    "Polymorph": "变形术",
    "Blink": "闪现术",
    "Focus Magic": "专注魔法",
    "Slow Fall": "缓落术",
    "Invisibility": "隐形术",
    "Counterspell": "法术反制",
    "Spellsteal": "法术窃取",
    "Mana Shield": "法力护盾",
    "Frost Ward": "冰霜防护结界",
    "Fire Ward": "火焰防护结界",
    "Dampen Magic": "魔法抑制",
    "Amplify Magic": "魔法增效",
    "Ritual of Refreshment": "餐桌仪式",
    "Arcane Explosion": "魔爆术",
    "Blast Wave": "冲击波",
    "Dragon's Breath": "龙息术",
    "Slow": "减速",
    "Remove Curse": "解除诅咒",
    "Portal": "传送门",
    # Shaman
    "Windfury Totem": "风怒图腾",
    "Strength of Earth Totem": "大地之力图腾",
    "Earth Shield": "大地之盾",
    "Riptide": "激流",
    "Chain Heal": "治疗链",
    "Healing Wave": "治疗波",
    "Lesser Healing Wave": "次级治疗波",
    "Ancestral Healing": "先祖治疗",
    # Druid
    "Innervate": "激活",
    "Rebirth": "复生",
    "Tranquility": "宁静",
    "Barkskin": "树皮术",
    "Survival Instincts": "生存本能",
    "Frenzied Regeneration": "狂暴回复",
    "Nature's Grasp": "自然之握",
    "Thorns": "荆棘术",
    # Paladin
    "Hand of Sacrifice": "牺牲之手",
    "Hand of Protection": "保护之手",
    "Hand of Salvation": "拯救之手",
    "Beacon of Light": "圣光道标",
    "Sacred Shield": "神圣护盾",
    "Avenging Wrath": "复仇之怒",
    "Divine Plea": "神圣恳求",
    "Judgement of Wisdom": "智慧审判",
    "Judgement of Light": "光明审判",
    "Seal of Vengeance": "复仇圣印",
    "Seal of Corruption": "腐蚀圣印",
    "Seal of Righteousness": "正义圣印",
    "Seal of Wisdom": "智慧圣印",
    "Seal of Light": "光明圣印",
    "Divine Protection": "圣佑术",
    "Lay on Hands": "圣疗术",
    # Warrior
    "Demoralizing Shout": "挫志怒吼",
    "Sunder Armor": "破甲攻击",
    "Thunder Clap": "雷霆一击",
    "Heroic Strike": "英勇打击",
    "Cleave": "顺劈斩",
    "Whirlwind": "旋风斩",
    "Mortal Strike": "致死打击",
    "Bloodthirst": "嗜血",
    "Rampage": "暴怒",
    "Shield Wall": "盾墙",
    "Last Stand": "破釜沉舟",
    "Recklessness": "鲁莽",
    "Berserker Rage": "狂暴之怒",
    "Commanding Presence": "命令怒吼",
    # Hunter
    "Aspect of the Hawk": "雄鹰守护",
    "Aspect of the Dragonhawk": "龙鹰守护",
    "Aspect of the Viper": "蝰蛇守护",
    "Aspect of the Wild": "野性守护",
    "Aspect of the Pack": "豹群守护",
    "Trueshot Aura": "强击光环",
    "Hunter's Mark": "猎人印记",
    "Serpent Sting": "毒蛇钉刺",
    "Explosive Shot": "爆炸射击",
    "Steady Shot": "稳固射击",
    "Aimed Shot": "瞄准射击",
    "Chimera Shot": "奇美拉射击",
    "Kill Shot": "杀戮射击",
    "Multi-Shot": "多重射击",
    "Volley": "乱射",
    "Rapid Fire": "急速射击",
    "Readiness": "准备就绪",
    "Feign Death": "假死",
    "Misdirection": "误导",
    # Rogue
    "Tricks of the Trade": "嫁祸诀窍",
    "Slice and Dice": "切割",
    "Adrenaline Rush": "冲动",
    "Blade Flurry": "剑刃乱舞",
    "Killing Spree": "杀戮盛筵",
    "Shadow Dance": "暗影之舞",
    "Preparation": "伺机待发",
    "Vanish": "消失",
    "Cloak of Shadows": "暗影斗篷",
    "Evasion": "闪避",
    "Sprint": "疾跑",
    "Deadly Poison": "致命毒药",
    "Wound Poison": "致伤毒药",
    "Instant Poison": "速效毒药",
    "Crippling Poison": "减速毒药",
    # Priest
    "Prayer of Mending": "愈合祷言",
    "Circle of Healing": "治疗之环",
    "Guardian Spirit": "守护之魂",
    "Pain Suppression": "痛苦压制",
    "Penance": "苦修",
    "Lightwell": "光明之泉",
    "Desperate Prayer": "绝望祷言",
    "Mind Soothe": "安抚心灵",
    "Levitate": "漂浮术",
    "Resurrection": "复活术",
    "Symbol of Hope": "希望符记",
    # DK
    "Path of Frost": "冰霜之路",
    "Anti-Magic Zone": "反魔法领域",
    "Ghoul Frenzy": "食尸鬼狂乱",
    "Death Grip": "死亡之握",
    "Chains of Ice": "寒冰锁链",
    "Strangulate": "绞袭",
    "Mind Freeze": "心灵冰冻",
    "Rune Strike": "符文打击",
    # Warlock
    "Soulstone Resurrection": "灵魂石复活",
    "Unending Breath": "无尽呼吸",
    "Detect Invisibility": "侦测隐形",
    "Ritual of Summoning": "召唤仪式",
    "Shadow Ward": "暗影防护",
    "Demonic Embrace": "恶魔之拥",
    # General
    "Heroism": "英勇",
    "Bloodlust": "嗜血",
    "Sated": "心满意足",
    "Exhaustion": "精疲力竭",
    "Temporal Displacement": "时空错位",
    # === 大量常见 Buff/Debuff 补充 ===
    # Mage
    "Clearcasting": "节能施法",
    "Arcane Potency": "奥术潜能",
    "Arcane Instability": "奥术动荡",
    "Incanter's Absorption": "咒术吸收",
    "Slow": "减速",
    "Polymorph": "变形术",
    "Spellsteal": "法术窃取",
    "Counterspell": "法术反制",
    "Invisibility": "隐形术",
    "Slow Fall": "缓落术",
    "Mana Shield": "法力护盾",
    "Fire Ward": "火焰防护结界",
    "Frost Ward": "冰霜防护结界",
    "Dampen Magic": "魔法抑制",
    "Amplify Magic": "魔法增效",
    "Ritual of Refreshment": "餐桌仪式",
    "Flamestrike": "烈焰风暴",
    "Cone of Cold": "冰锥术",
    "Frost Nova": "冰霜新星",
    "Blink": "闪现术",
    "Focus Magic": "专注魔法",
    "Master of Elements": "元素大师",
    "Impact": "冲击",
    "Ignite": "点燃",
    "Pyroblast!": "炎爆术!",
    # Priest
    "Divine Aegis": "神圣庇护",
    "Borrowed Time": "争分夺秒",
    "Grace": "恩典",
    "Inner Focus": "心灵专注",
    "Inspiration": "灵感",
    "Shadowform": "暗影形态",
    "Misery": "悲惨",
    "Surge of Light": "圣光涌动",
    "Serendipity": "圣光之触",
    "Empowered Renew": "强效恢复",
    "Test of Faith": "信仰试炼",
    "Body and Soul": "身轻体健",
    "Divine Spirit": "神圣之灵",
    "Abolish Disease": "驱除疾病",
    "Cure Disease": "治愈疾病",
    "Power Word: Fortitude": "真言术：韧",
    "Fear Ward": "防护恐惧结界",
    "Prayer of Fortitude": "坚韧祷言",
    # Warlock
    "Fel Armor": "魔甲术",
    "Demonic Armor": "恶魔护甲",
    "Soul Link": "灵魂链接",
    "Molten Core": "熔火之心",
    "Decimation": "屠戮",
    "Eradication": "根除",
    "Demonic Empowerment": "恶魔增效",
    "Haunt": "鬼影缠身",
    "Unstable Affliction": "痛苦无常",
    "Siphon Life": "生命虹吸",
    "Backdraft": "反冲",
    "Soul Fire": "灵魂之火",
    "Shadow Embrace": "暗影之拥",
    "Demonic Circle: Summon": "恶魔召唤法阵",
    "Demonic Circle: Teleport": "恶魔传送法阵",
    "Howl of Terror": "恐惧嚎叫",
    "Fear": "恐惧术",
    "Banish": "放逐术",
    "Enslave Demon": "奴役恶魔",
    "Create Soulstone": "制造灵魂石",
    "Create Healthstone": "制造治疗石",
    "Create Firestone": "制造火焰石",
    "Create Spellstone": "制造法术石",
    "Ritual of Souls": "灵魂仪式",
    "Soulshatter": "灵魂碎裂",
    "Curse of Agony": "痛苦诅咒",
    "Curse of Doom": "厄运诅咒",
    "Curse of Elements": "元素诅咒",
    "Curse of Tongues": "语言诅咒",
    "Curse of Weakness": "虚弱诅咒",
    "Seed of Corruption": "腐蚀之种",
    "Immolate": "献祭",
    "Corruption": "腐蚀术",
    "Drain Soul": "吸取灵魂",
    "Drain Life": "吸取生命",
    "Drain Mana": "吸取法力",
    "Shadowburn": "暗影灼烧",
    "Shadowfury": "暗影之怒",
    "Chaos Bolt": "混乱之箭",
    "Incinerate": "烧尽",
    "Conflagrate": "焚烧",
    # Druid
    "Lifebloom": "生命绽放",
    "Regrowth": "愈合",
    "Swiftmend": "迅捷治愈",
    "Nourish": "滋养",
    "Abolish Poison": "驱毒术",
    "Cure Poison": "消毒术",
    "Remove Curse": "解除诅咒",
    "Tree of Life": "生命之树",
    "Moonkin Form": "枭兽形态",
    "Cat Form": "猎豹形态",
    "Bear Form": "熊形态",
    "Dire Bear Form": "巨熊形态",
    "Travel Form": "旅行形态",
    "Aquatic Form": "水栖形态",
    "Flight Form": "飞行形态",
    "Swift Flight Form": "迅捷飞行形态",
    "Prowl": "潜行",
    "Dash": "急奔",
    "Tiger's Fury": "猛虎之怒",
    "Savage Roar": "野蛮咆哮",
    "Berserk": "狂暴",
    "Mangle": "裂伤",
    "Shred": "撕碎",
    "Rake": "斜掠",
    "Rip": "割裂",
    "Ferocious Bite": "凶猛撕咬",
    "Swipe (Cat)": "横扫(猎豹)",
    "Swipe (Bear)": "横扫(熊)",
    "Lacerate": "割伤",
    "Maul": "重殴",
    "Growl": "低吼",
    "Demoralizing Roar": "挫志咆哮",
    "Faerie Fire": "精灵之火",
    "Faerie Fire (Feral)": "精灵之火(野性)",
    "Insect Swarm": "虫群",
    "Moonfire": "月火术",
    "Starfire": "星火术",
    "Wrath": "愤怒",
    "Hurricane": "飓风",
    "Typhoon": "台风",
    "Starfall": "星辰坠落",
    "Force of Nature": "自然之力",
    # Paladin
    "Divine Shield": "圣盾术",
    "Hand of Reckoning": "清算之手",
    "Judgement": "审判",
    "Judgement of Justice": "公正审判",
    "Seal of Command": "命令圣印",
    "Righteous Fury": "正义之怒",
    "Flash of Light": "圣光闪现",
    "Holy Light": "圣光术",
    "Holy Shock": "神圣震击",
    "Cleanse": "清洁术",
    "Blessing of Sanctuary": "庇护祝福",
    "Greater Blessing of Sanctuary": "强效庇护祝福",
    "Blessing of Sacrifice": "牺牲祝福",
    "Concentration Aura": "专注光环",
    "Devotion Aura": "虔诚光环",
    "Retribution Aura": "惩罚光环",
    "Shadow Resistance Aura": "暗影抗性光环",
    "Frost Resistance Aura": "冰霜抗性光环",
    "Fire Resistance Aura": "火焰抗性光环",
    "Crusader Aura": "十字军光环",
    # Shaman
    "Windfury": "风怒",
    "Windfury Weapon": "风怒武器",
    "Flametongue Weapon": "火舌武器",
    "Frostbrand Weapon": "冰封武器",
    "Rockbiter Weapon": "石化武器",
    "Earthliving Weapon": "大地生命武器",
    "Lightning Shield": "闪电护盾",
    "Water Shield": "水之护盾",
    "Tidal Waves": "潮汐奔涌",
    "Earth Shock": "地震术",
    "Flame Shock": "烈焰震击",
    "Frost Shock": "冰霜震击",
    "Stormstrike": "风暴打击",
    "Lava Lash": "熔岩猛击",
    "Shamanistic Rage": "萨满之怒",
    "Feral Spirit": "野性之魂",
    "Fire Elemental Totem": "火元素图腾",
    "Magma Totem": "熔岩图腾",
    "Searing Totem": "灼热图腾",
    "Healing Stream Totem": "治疗之泉图腾",
    "Mana Tide Totem": "法力之潮图腾",
    "Tremor Totem": "战栗图腾",
    "Grounding Totem": "根基图腾",
    "Earthbind Totem": "地缚图腾",
    "Stoneskin Totem": "石肤图腾",
    "Windwall Totem": "风墙图腾",
    "Sentry Totem": "岗哨图腾",
    "Nature Resistance Totem": "自然抗性图腾",
    "Fire Resistance Totem": "火焰抗性图腾",
    "Frost Resistance Totem": "冰霜抗性图腾",
    # Hunter
    "Aspect of the Cheetah": "猎豹守护",
    "Scorpid Sting": "毒蝎钉刺",
    "Viper Sting": "蝰蛇钉刺",
    "Wyvern Sting": "翼龙钉刺",
    "Deterrence": "威慑",
    "Disengage": "后跳",
    "Mend Pet": "治疗宠物",
    "Revive Pet": "复活宠物",
    "Call Pet": "召唤宠物",
    "Dismiss Pet": "解散宠物",
    "Eagle Eye": "鹰眼术",
    "Beast Lore": "野兽知识",
    "Eyes of the Beast": "野兽之眼",
    "Master's Call": "主人的召唤",
    "Bestial Wrath": "狂野怒火",
    "The Beast Within": "野兽之心",
    "Intimidation": "胁迫",
    "Spirit Bond": "灵魂联结",
    "Ferocious Inspiration": "凶猛灵感",
    "Cobra Strikes": "眼镜蛇打击",
    "Kindred Spirits": "志趣相投",
    "Cobra Shot": "眼镜蛇射击",
    "Lock and Load": "荷枪实弹",
    "Trap Mastery": "陷阱掌握",
    "Hunting Party": "狩猎小队",
    "Sniper Training": "狙击训练",
    "Explosive Trap": "爆炸陷阱",
    "Immolation Trap": "献祭陷阱",
    "Freezing Trap": "冰冻陷阱",
    "Frost Trap": "冰霜陷阱",
    "Snake Trap": "毒蛇陷阱",
    "Black Arrow": "黑箭",
    "Counterattack": "反击",
    "Wing Clip": "摔绊",
    "Concussive Shot": "震荡射击",
    "Scatter Shot": "驱散射击",
    "Silencing Shot": "沉默射击",
    "Auto Shot": "自动射击",
    "Raptor Strike": "猛禽一击",
    "Mongoose Bite": "猫鼬撕咬",
    # Rogue
    "Killing Spree (Teleport)": "杀戮盛筵(传送)",
    "Shadowstep": "暗影步",
    "Ambush": "伏击",
    "Backstab": "背刺",
    "Mutilate": "毁伤",
    "Envenom": "毒伤",
    "Eviscerate": "刺骨",
    "Expose Armor": "破甲",
    "Garrote": "锁喉",
    "Cheap Shot": "偷袭",
    "Kidney Shot": "肾击",
    "Blind": "致盲",
    "Sap": "闷棍",
    "Gouge": "凿击",
    "Kick": "脚踢",
    "Shiv": "毒刃",
    "Fan of Knives": "刀扇",
    "Feint": "佯攻",
    # Warrior
    "Shield Block": "盾牌格挡",
    "Shield Slam": "盾牌猛击",
    "Devastate": "毁灭打击",
    "Revenge": "复仇",
    "Taunt": "嘲讽",
    "Mocking Blow": "惩戒痛击",
    "Challenging Shout": "挑战怒吼",
    "Intervene": "援护",
    "Interception": "拦截",
    "Charge": "冲锋",
    "Hamstring": "断筋",
    "Piercing Howl": "刺耳怒吼",
    "Victory Rush": "乘胜追击",
    "Execute": "斩杀",
    "Slam": "猛击",
    "Overpower": "压制",
    "Rend": "撕裂",
    "Spell Reflection": "法术反射",
    "Enraged Regeneration": "狂怒回复",
    "Death Wish": "死亡之愿",
    # DK
    "Unholy Presence": "邪恶灵气",
    "Frost Presence": "冰霜灵气",
    "Blood Presence": "鲜血灵气",
    "Bone Shield": "白骨之盾",
    "Icebound Fortitude": "冰封之韧",
    "Vampiric Blood": "吸血鬼之血",
    "Unholy Frenzy": "邪恶狂热",
    "Anti-Magic Shell": "反魔法护罩",
    "Army of the Dead": "亡者大军",
    "Raise Dead": "亡者复生",
    "Death and Decay": "枯萎凋零",
    "Plague Strike": "瘟疫打击",
    "Icy Touch": "冰触",
    "Blood Strike": "鲜血打击",
    "Heart Strike": "心脏打击",
    "Scourge Strike": "天灾打击",
    "Obliterate": "湮灭",
    "Frost Strike": "冰霜打击",
    "Howling Blast": "凛风冲击",
    "Death Coil": "死亡缠绕",
    "Ghoul": "食尸鬼",
    "Summon Gargoyle": "召唤石像鬼",
    "Dancing Rune Weapon": "符文刃舞",
    "Hysteria": "狂热",
    "Army of the Dead Ghoul": "亡者大军食尸鬼",
    # General / Consumables / Trinkets / Raid
    "Flame Cap": "烈焰菇",
    "Nightmare Seed": "噩梦藤种子",
    "Ironshield Potion": "铁盾药水",
    "Destruction Potion": "毁灭药水",
    "Haste Potion": "加速药水",
    "Fel Mana Potion": "魔能法力药水",
    "Super Mana Potion": "超级法力药水",
    "Super Healing Potion": "超级治疗药水",
    "Demonic Rune": "恶魔符文",
    "Dark Rune": "黑暗符文",
    "Mana Emerald": "法力翡翠",
    "Mana Ruby": "法力红宝石",
    "Mana Sapphire": "法力蓝宝石",
    "Mana Citrine": "法力黄水晶",
    "Mana Jade": "法力翡翠(低)",
    "Mana Agate": "法力玛瑙",
    "Healing Potion Injector": "治疗药水注射器",
    "Mana Potion Injector": "法力药水注射器",
    "Thistle Tea": "荆棘茶",
    "Gift of Arthas": "阿尔萨斯的礼物",
    "Juju Power": "诅咒之力",
    "Juju Might": "诅咒之威",
    "Elixir of Major Agility": "特效敏捷药剂",
    "Elixir of Major Strength": "特效力量药剂",
    "Elixir of Major Fortitude": "特效坚韧药剂",
    "Elixir of Major Shadow Power": "特效暗影之力药剂",
    "Elixir of Major Firepower": "特效火力药剂",
    "Elixir of Major Frost Power": "特效冰霜之力药剂",
    "Elixir of Major Defense": "特效防御药剂",
    "Elixir of the Mongoose": "猫鼬药剂",
    "Elixir of Giants": "巨人药剂",
    "Scroll of Stamina": "耐力卷轴",
    "Scroll of Strength": "力量卷轴",
    "Scroll of Agility": "敏捷卷轴",
    "Scroll of Intellect": "智力卷轴",
    "Scroll of Spirit": "精神卷轴",
    "Scroll of Protection": "保护卷轴",
    "Drums of Battle": "战斗之鼓",
    "Drums of Restoration": "恢复之鼓",
    "Drums of War": "战争之鼓",
    "Drums of Speed": "速度之鼓",
    "Drums of Panic": "恐慌之鼓",
    "Replenishment": "补满",
    "Judgements of the Wise": "睿智审判",
    "Mana Tide": "法力之潮",
    "Rapture": "狂喜",
    "Revitalize": "新生",
    "Improved Soul Leech": "强化灵魂吸取",
    "Enduring Winter": "凛冽寒冬",
    "Strength of Earth": "大地之力",
    "Unleashed Rage": "释放怒火",
    "Abomination's Might": "憎恶之力",
    "Arcane Empowerment": "奥术增效",
    "Sanctified Retribution": "圣洁惩戒",
    "Swift Retribution": "迅捷惩戒",
    "Elemental Oath": "元素誓言",
    "Wrath of Air": "空气之怒",
    "Improved Icy Talons": "强化冰冷之爪",
    "Honor Among Thieves": "盗贼的尊严",
    # Encounter / Special
    "Power of the Titans": "泰坦之力",
    "Essence of the Red": "红色精华",
    "Fire Resistance": "火焰抗性",
    "Frost Resistance": "冰霜抗性",
    "Nature Resistance": "自然抗性",
    "Shadow Resistance": "暗影抗性",
    "Arcane Resistance": "奥术抗性",
    "Sprint": "疾跑",
    "Stealth": "潜行",
    "Vanish": "消失",
    "Evasion": "闪避",
    "Cloak of Shadows": "暗影斗篷",
    "Blind": "致盲",
    "Distract": "扰乱",
    "Shiv": "毒刃",
    "Kick": "脚踢",
    "Feint": "佯攻",
    "Fan of Knives": "刀扇",
    "Deadly Throw": "致命投掷",
    "Expose Armor": "破甲",
    "Garrote": "锁喉",
    "Rupture": "割裂",
    "Slice and Dice": "切割",
    "Adrenaline Rush": "冲动",
    "Blade Flurry": "剑刃乱舞",
    "Killing Spree": "杀戮盛筵",
    "Shadow Dance": "暗影之舞",
    "Preparation": "伺机待发",
    "Premeditation": "预谋",
    "Ambush": "伏击",
    "Backstab": "背刺",
    "Mutilate": "毁伤",
    "Envenom": "毒伤",
    "Eviscerate": "刺骨",
    "Cheap Shot": "偷袭",
    "Kidney Shot": "肾击",
    "Sap": "闷棍",
    "Gouge": "凿击",
    "Dismantle": "拆卸",
    "Tricks of the Trade": "嫁祸诀窍",
    "Deadly Poison": "致命毒药",
    "Wound Poison": "致伤毒药",
    "Instant Poison": "速效毒药",
    "Crippling Poison": "减速毒药",
    "Anesthetic Poison": "麻醉毒药",
    "Mind-Numbing Poison": "麻痹毒药",
    # Warrior
    "Battle Stance": "战斗姿态",
    "Defensive Stance": "防御姿态",
    "Berserker Stance": "狂暴姿态",
    "Tactical Mastery": "战术掌握",
    "Second Wind": "复苏之风",
    "Blood Craze": "血之狂热",
    "Impale": "穿刺",
    "Deep Wounds": "重伤",
    "Mortal Strike": "致死打击",
    "Overpower": "压制",
    "Revenge": "复仇",
    "Shield Slam": "盾牌猛击",
    "Devastate": "毁灭打击",
    "Sunder Armor": "破甲攻击",
    "Thunder Clap": "雷霆一击",
    "Demoralizing Shout": "挫志怒吼",
    "Commanding Shout": "命令怒吼",
    "Battle Shout": "战斗怒吼",
    "Heroic Strike": "英勇打击",
    "Cleave": "顺劈斩",
    "Whirlwind": "旋风斩",
    "Rampage": "暴怒",
    "Shield Wall": "盾墙",
    "Last Stand": "破釜沉舟",
    "Recklessness": "鲁莽",
    "Berserker Rage": "狂暴之怒",
    "Death Wish": "死亡之愿",
    "Enraged Regeneration": "狂怒回复",
    "Spell Reflection": "法术反射",
    "Intervene": "援护",
    "Interception": "拦截",
    "Charge": "冲锋",
    "Hamstring": "断筋",
    "Piercing Howl": "刺耳怒吼",
    "Victory Rush": "乘胜追击",
    "Execute": "斩杀",
    "Slam": "猛击",
    "Rend": "撕裂",
    "Mocking Blow": "惩戒痛击",
    "Taunt": "嘲讽",
    "Challenging Shout": "挑战怒吼",
    "Shield Block": "盾牌格挡",
    "Titan's Grip": "泰坦之握",
    "Single-Minded Fury": "一心狂怒",
    # Paladin
    "Beacon of Light": "圣光道标",
    "Sacred Shield": "神圣护盾",
    "Avenging Wrath": "复仇之怒",
    "Divine Plea": "神圣恳求",
    "Divine Protection": "圣佑术",
    "Lay on Hands": "圣疗术",
    "Hand of Sacrifice": "牺牲之手",
    "Hand of Protection": "保护之手",
    "Hand of Salvation": "拯救之手",
    "Hand of Reckoning": "清算之手",
    "Seal of Vengeance": "复仇圣印",
    "Seal of Corruption": "腐蚀圣印",
    "Seal of Righteousness": "正义圣印",
    "Seal of Wisdom": "智慧圣印",
    "Seal of Light": "光明圣印",
    "Seal of Command": "命令圣印",
    "Seal of Justice": "公正圣印",
    "Judgement": "审判",
    "Judgement of Wisdom": "智慧审判",
    "Judgement of Light": "光明审判",
    "Judgement of Justice": "公正审判",
    "Righteous Fury": "正义之怒",
    "Consecration": "奉献",
    "Holy Wrath": "神圣愤怒",
    "Exorcism": "驱邪术",
    "Holy Shock": "神圣震击",
    "Flash of Light": "圣光闪现",
    "Holy Light": "圣光术",
    "Cleanse": "清洁术",
    "Blessing of Might": "力量祝福",
    "Greater Blessing of Might": "强效力量祝福",
    "Blessing of Wisdom": "智慧祝福",
    "Greater Blessing of Wisdom": "强效智慧祝福",
    "Blessing of Kings": "王者祝福",
    "Greater Blessing of Kings": "强效王者祝福",
    "Blessing of Sanctuary": "庇护祝福",
    "Greater Blessing of Sanctuary": "强效庇护祝福",
    "Concentration Aura": "专注光环",
    "Devotion Aura": "虔诚光环",
    "Retribution Aura": "惩罚光环",
    "Crusader Aura": "十字军光环",
    "Shadow Resistance Aura": "暗影抗性光环",
    "Frost Resistance Aura": "冰霜抗性光环",
    "Fire Resistance Aura": "火焰抗性光环",
    # Hunter
    "Aspect of the Hawk": "雄鹰守护",
    "Aspect of the Dragonhawk": "龙鹰守护",
    "Aspect of the Viper": "蝰蛇守护",
    "Aspect of the Wild": "野性守护",
    "Aspect of the Pack": "豹群守护",
    "Aspect of the Cheetah": "猎豹守护",
    "Trueshot Aura": "强击光环",
    "Hunter's Mark": "猎人印记",
    "Serpent Sting": "毒蛇钉刺",
    "Explosive Shot": "爆炸射击",
    "Steady Shot": "稳固射击",
    "Aimed Shot": "瞄准射击",
    "Chimera Shot": "奇美拉射击",
    "Kill Shot": "杀戮射击",
    "Multi-Shot": "多重射击",
    "Volley": "乱射",
    "Rapid Fire": "急速射击",
    "Readiness": "准备就绪",
    "Feign Death": "假死",
    "Misdirection": "误导",
    "Deterrence": "威慑",
    "Disengage": "后跳",
    "Mend Pet": "治疗宠物",
    "Revive Pet": "复活宠物",
    "Call Pet": "召唤宠物",
    "Dismiss Pet": "解散宠物",
    "Eagle Eye": "鹰眼术",
    "Beast Lore": "野兽知识",
    "Eyes of the Beast": "野兽之眼",
    "Master's Call": "主人的召唤",
    "Bestial Wrath": "狂野怒火",
    "The Beast Within": "野兽之心",
    "Intimidation": "胁迫",
    "Spirit Bond": "灵魂联结",
    "Ferocious Inspiration": "凶猛灵感",
    "Cobra Strikes": "眼镜蛇打击",
    "Kindred Spirits": "志趣相投",
    "Cobra Shot": "眼镜蛇射击",
    "Lock and Load": "荷枪实弹",
    "Trap Mastery": "陷阱掌握",
    "Hunting Party": "狩猎小队",
    "Sniper Training": "狙击训练",
    "Explosive Trap": "爆炸陷阱",
    "Immolation Trap": "献祭陷阱",
    "Freezing Trap": "冰冻陷阱",
    "Frost Trap": "冰霜陷阱",
    "Snake Trap": "毒蛇陷阱",
    "Black Arrow": "黑箭",
    "Counterattack": "反击",
    "Wing Clip": "摔绊",
    "Concussive Shot": "震荡射击",
    "Scatter Shot": "驱散射击",
    "Silencing Shot": "沉默射击",
    "Arcane Shot": "奥术射击",
    "Auto Shot": "自动射击",
    "Raptor Strike": "猛禽一击",
    "Mongoose Bite": "猫鼬撕咬",
    # Shaman
    "Windfury Totem": "风怒图腾",
    "Strength of Earth Totem": "大地之力图腾",
    "Flametongue Totem": "火舌图腾",
    "Totem of Wrath": "天怒图腾",
    "Wrath of Air Totem": "空气之怒图腾",
    "Mana Spring Totem": "法力之泉图腾",
    "Healing Stream Totem": "治疗之泉图腾",
    "Mana Tide Totem": "法力之潮图腾",
    "Tremor Totem": "战栗图腾",
    "Grounding Totem": "根基图腾",
    "Earthbind Totem": "地缚图腾",
    "Stoneskin Totem": "石肤图腾",
    "Searing Totem": "灼热图腾",
    "Magma Totem": "熔岩图腾",
    "Fire Elemental Totem": "火元素图腾",
    "Frost Resistance Totem": "冰霜抗性图腾",
    "Fire Resistance Totem": "火焰抗性图腾",
    "Nature Resistance Totem": "自然抗性图腾",
    "Windwall Totem": "风墙图腾",
    "Sentry Totem": "岗哨图腾",
    "Earth Shield": "大地之盾",
    "Riptide": "激流",
    "Chain Heal": "治疗链",
    "Healing Wave": "治疗波",
    "Lesser Healing Wave": "次级治疗波",
    "Ancestral Healing": "先祖治疗",
    "Ancestral Fortitude": "先祖坚韧",
    "Lightning Shield": "闪电护盾",
    "Water Shield": "水之护盾",
    "Tidal Waves": "潮汐奔涌",
    "Earth Shock": "地震术",
    "Flame Shock": "烈焰震击",
    "Frost Shock": "冰霜震击",
    "Stormstrike": "风暴打击",
    "Lava Lash": "熔岩猛击",
    "Shamanistic Rage": "萨满之怒",
    "Feral Spirit": "野性之魂",
    "Windfury Weapon": "风怒武器",
    "Flametongue Weapon": "火舌武器",
    "Frostbrand Weapon": "冰封武器",
    "Rockbiter Weapon": "石化武器",
    "Earthliving Weapon": "大地生命武器",
    "Windfury": "风怒",
    "Heroism": "英勇",
    "Bloodlust": "嗜血",
    # Druid
    "Innervate": "激活",
    "Rebirth": "复生",
    "Tranquility": "宁静",
    "Barkskin": "树皮术",
    "Survival Instincts": "生存本能",
    "Frenzied Regeneration": "狂暴回复",
    "Nature's Grasp": "自然之握",
    "Thorns": "荆棘术",
    "Mark of the Wild": "野性印记",
    "Gift of the Wild": "野性赐福",
    "Abolish Poison": "驱毒术",
    "Cure Poison": "消毒术",
    "Remove Curse": "解除诅咒",
    "Tree of Life": "生命之树",
    "Moonkin Form": "枭兽形态",
    "Cat Form": "猎豹形态",
    "Bear Form": "熊形态",
    "Dire Bear Form": "巨熊形态",
    "Travel Form": "旅行形态",
    "Aquatic Form": "水栖形态",
    "Flight Form": "飞行形态",
    "Swift Flight Form": "迅捷飞行形态",
    "Prowl": "潜行",
    "Dash": "急奔",
    "Tiger's Fury": "猛虎之怒",
    "Savage Roar": "野蛮咆哮",
    "Berserk": "狂暴",
    "Mangle": "裂伤",
    "Shred": "撕碎",
    "Rake": "斜掠",
    "Rip": "割裂",
    "Ferocious Bite": "凶猛撕咬",
    "Swipe (Cat)": "横扫(猎豹)",
    "Swipe (Bear)": "横扫(熊)",
    "Lacerate": "割伤",
    "Maul": "重殴",
    "Growl": "低吼",
    "Demoralizing Roar": "挫志咆哮",
    "Faerie Fire": "精灵之火",
    "Faerie Fire (Feral)": "精灵之火(野性)",
    "Insect Swarm": "虫群",
    "Moonfire": "月火术",
    "Starfire": "星火术",
    "Wrath": "愤怒",
    "Hurricane": "飓风",
    "Typhoon": "台风",
    "Starfall": "星辰坠落",
    "Force of Nature": "自然之力",
    "Lifebloom": "生命绽放",
    "Regrowth": "愈合",
    "Swiftmend": "迅捷治愈",
    "Nourish": "滋养",
    "Wild Growth": "野性成长",
    "Rejuvenation": "回春术",
    "Leader of the Pack": "兽群领袖",
    "Leader of the Pack(Physical)": "兽群领袖(物理)",
    "Leader of the Pack(Spell)": "兽群领袖(法术)",
    "Moonkin Aura": "枭兽光环",
    # Warlock
    "Soulstone Resurrection": "灵魂石复活",
    "Unending Breath": "无尽呼吸",
    "Detect Invisibility": "侦测隐形",
    "Ritual of Summoning": "召唤仪式",
    "Shadow Ward": "暗影防护",
    "Demonic Embrace": "恶魔之拥",
    "Fel Armor": "魔甲术",
    "Demonic Armor": "恶魔护甲",
    "Soul Link": "灵魂链接",
    "Molten Core": "熔火之心",
    "Decimation": "屠戮",
    "Eradication": "根除",
    "Demonic Empowerment": "恶魔增效",
    "Haunt": "鬼影缠身",
    "Unstable Affliction": "痛苦无常",
    "Siphon Life": "生命虹吸",
    "Backdraft": "反冲",
    "Soul Fire": "灵魂之火",
    "Shadow Embrace": "暗影之拥",
    "Demonic Circle: Summon": "恶魔召唤法阵",
    "Demonic Circle: Teleport": "恶魔传送法阵",
    "Howl of Terror": "恐惧嚎叫",
    "Fear": "恐惧术",
    "Banish": "放逐术",
    "Enslave Demon": "奴役恶魔",
    "Create Soulstone": "制造灵魂石",
    "Create Healthstone": "制造治疗石",
    "Create Firestone": "制造火焰石",
    "Create Spellstone": "制造法术石",
    "Ritual of Souls": "灵魂仪式",
    "Soulshatter": "灵魂碎裂",
    "Curse of Agony": "痛苦诅咒",
    "Curse of Doom": "厄运诅咒",
    "Curse of Elements": "元素诅咒",
    "Curse of Tongues": "语言诅咒",
    "Curse of Weakness": "虚弱诅咒",
    "Seed of Corruption": "腐蚀之种",
    "Immolate": "献祭",
    "Corruption": "腐蚀术",
    "Drain Soul": "吸取灵魂",
    "Drain Life": "吸取生命",
    "Drain Mana": "吸取法力",
    "Shadowburn": "暗影灼烧",
    "Shadowfury": "暗影之怒",
    "Chaos Bolt": "混乱之箭",
    "Incinerate": "烧尽",
    "Conflagrate": "焚烧",
    "Death Coil": "死亡缠绕",
    # Priest
    "Prayer of Mending": "愈合祷言",
    "Circle of Healing": "治疗之环",
    "Guardian Spirit": "守护之魂",
    "Pain Suppression": "痛苦压制",
    "Penance": "苦修",
    "Lightwell": "光明之泉",
    "Desperate Prayer": "绝望祷言",
    "Mind Soothe": "安抚心灵",
    "Levitate": "漂浮术",
    "Resurrection": "复活术",
    "Symbol of Hope": "希望符记",
    "Divine Aegis": "神圣庇护",
    "Borrowed Time": "争分夺秒",
    "Grace": "恩典",
    "Inner Focus": "心灵专注",
    "Inspiration": "灵感",
    "Shadowform": "暗影形态",
    "Misery": "悲惨",
    "Surge of Light": "圣光涌动",
    "Serendipity": "圣光之触",
    "Empowered Renew": "强效恢复",
    "Test of Faith": "信仰试炼",
    "Body and Soul": "身轻体健",
    "Divine Spirit": "神圣之灵",
    "Abolish Disease": "驱除疾病",
    "Cure Disease": "治愈疾病",
    "Power Word: Fortitude": "真言术：韧",
    "Power Word: Shield": "真言术：盾",
    "Fear Ward": "防护恐惧结界",
    "Prayer of Fortitude": "坚韧祷言",
    "Prayer of Spirit": "精神祷言",
    "Prayer of Shadow Protection": "暗影防护祷言",
    "Shadow Protection": "暗影防护",
    "Renewed Hope": "新生希望",
    "Hymn of Hope": "希望赞歌",
    "Divine Hymn": "神圣赞美诗",
    "Shackle Undead": "束缚亡灵",
    "Mass Dispel": "群体驱散",
    # Mage
    "Frostbolt": "寒冰箭",
    "Frostfire Bolt": "霜火之箭",
    "Deep Freeze": "深度冻结",
    "Waterbolt": "水箭",
    "Mirror Image": "镜像",
    "Icy Veins": "冰冷血脉",
    "Summon Water Elemental": "召唤水元素",
    "Arcane Blast": "奥术冲击",
    "Arcane Missiles": "奥术飞弹",
    "Arcane Power": "奥术强化",
    "Living Bomb": "活动炸弹",
    "Hot Streak": "炽热连击",
    "Brain Freeze": "思维冷却",
    "Fingers of Frost": "寒冰指",
    "Missile Barrage": "飞弹速射",
    "Combustion": "燃烧",
    "Evocation": "唤醒",
    "Ice Barrier": "寒冰护体",
    "Mage Armor": "法师护甲",
    "Molten Armor": "熔岩护甲",
    "Ice Armor": "冰甲术",
    "Presence of Mind": "气定神闲",
    "Ice Lance": "冰枪术",
    "Scorch": "灼烧",
    "Fireball": "火球术",
    "Pyroblast": "炎爆术",
    "Flamestrike": "烈焰风暴",
    "Blizzard": "暴风雪",
    "Cone of Cold": "冰锥术",
    "Frost Nova": "冰霜新星",
    "Blink": "闪现术",
    "Focus Magic": "专注魔法",
    "Master of Elements": "元素大师",
    "Impact": "冲击",
    "Ignite": "点燃",
    "Pyroblast!": "炎爆术!",
    "Clearcasting": "节能施法",
    "Arcane Potency": "奥术潜能",
    "Arcane Instability": "奥术动荡",
    "Incanter's Absorption": "咒术吸收",
    "Slow": "减速",
    "Polymorph": "变形术",
    "Spellsteal": "法术窃取",
    "Counterspell": "法术反制",
    "Invisibility": "隐形术",
    "Slow Fall": "缓落术",
    "Mana Shield": "法力护盾",
    "Fire Ward": "火焰防护结界",
    "Frost Ward": "冰霜防护结界",
    "Dampen Magic": "魔法抑制",
    "Amplify Magic": "魔法增效",
    "Ritual of Refreshment": "餐桌仪式",
    # DK
    "Path of Frost": "冰霜之路",
    "Anti-Magic Zone": "反魔法领域",
    "Ghoul Frenzy": "食尸鬼狂乱",
    "Death Grip": "死亡之握",
    "Chains of Ice": "寒冰锁链",
    "Strangulate": "绞袭",
    "Mind Freeze": "心灵冰冻",
    "Rune Strike": "符文打击",
    "Unholy Presence": "邪恶灵气",
    "Frost Presence": "冰霜灵气",
    "Blood Presence": "鲜血灵气",
    "Bone Shield": "白骨之盾",
    "Icebound Fortitude": "冰封之韧",
    "Vampiric Blood": "吸血鬼之血",
    "Unholy Frenzy": "邪恶狂热",
    "Anti-Magic Shell": "反魔法护罩",
    "Army of the Dead": "亡者大军",
    "Raise Dead": "亡者复生",
    "Death and Decay": "枯萎凋零",
    "Plague Strike": "瘟疫打击",
    "Icy Touch": "冰触",
    "Blood Strike": "鲜血打击",
    "Heart Strike": "心脏打击",
    "Scourge Strike": "天灾打击",
    "Obliterate": "湮灭",
    "Frost Strike": "冰霜打击",
    "Howling Blast": "凛风冲击",
    "Death Coil": "死亡缠绕",
    "Ghoul": "食尸鬼",
    "Summon Gargoyle": "召唤石像鬼",
    "Dancing Rune Weapon": "符文刃舞",
    "Hysteria": "狂热",
    "Army of the Dead Ghoul": "亡者大军食尸鬼",
    "Rune Weapon": "符文武器",
    # Consumables / Trinkets / Raid / Misc
    "Flame Cap": "烈焰菇",
    "Nightmare Seed": "噩梦藤种子",
    "Ironshield Potion": "铁盾药水",
    "Destruction Potion": "毁灭药水",
    "Haste Potion": "加速药水",
    "Fel Mana Potion": "魔能法力药水",
    "Super Mana Potion": "超级法力药水",
    "Super Healing Potion": "超级治疗药水",
    "Demonic Rune": "恶魔符文",
    "Dark Rune": "黑暗符文",
    "Mana Emerald": "法力翡翠",
    "Mana Ruby": "法力红宝石",
    "Mana Sapphire": "法力蓝宝石",
    "Mana Citrine": "法力黄水晶",
    "Mana Jade": "法力翡翠(低)",
    "Mana Agate": "法力玛瑙",
    "Healing Potion Injector": "治疗药水注射器",
    "Mana Potion Injector": "法力药水注射器",
    "Thistle Tea": "荆棘茶",
    "Gift of Arthas": "阿尔萨斯的礼物",
    "Juju Power": "诅咒之力",
    "Juju Might": "诅咒之威",
    "Elixir of Major Agility": "特效敏捷药剂",
    "Elixir of Major Strength": "特效力量药剂",
    "Elixir of Major Fortitude": "特效坚韧药剂",
    "Elixir of Major Shadow Power": "特效暗影之力药剂",
    "Elixir of Major Firepower": "特效火力药剂",
    "Elixir of Major Frost Power": "特效冰霜之力药剂",
    "Elixir of Major Defense": "特效防御药剂",
    "Elixir of the Mongoose": "猫鼬药剂",
    "Elixir of Giants": "巨人药剂",
    "Scroll of Stamina": "耐力卷轴",
    "Scroll of Strength": "力量卷轴",
    "Scroll of Agility": "敏捷卷轴",
    "Scroll of Intellect": "智力卷轴",
    "Scroll of Spirit": "精神卷轴",
    "Scroll of Protection": "保护卷轴",
    "Drums of Battle": "战斗之鼓",
    "Drums of Restoration": "恢复之鼓",
    "Drums of War": "战争之鼓",
    "Drums of Speed": "速度之鼓",
    "Drums of Panic": "恐慌之鼓",
    "Replenishment": "补满",
    "Judgements of the Wise": "睿智审判",
    "Mana Tide": "法力之潮",
    "Rapture": "狂喜",
    "Revitalize": "新生",
    "Improved Soul Leech": "强化灵魂吸取",
    "Enduring Winter": "凛冽寒冬",
    "Strength of Earth": "大地之力",
    "Unleashed Rage": "释放怒火",
    "Abomination's Might": "憎恶之力",
    "Arcane Empowerment": "奥术增效",
    "Sanctified Retribution": "圣洁惩戒",
    "Swift Retribution": "迅捷惩戒",
    "Elemental Oath": "元素誓言",
    "Wrath of Air": "空气之怒",
    "Improved Icy Talons": "强化冰冷之爪",
    "Honor Among Thieves": "盗贼的尊严",
    "Power of the Titans": "泰坦之力",
    "Essence of the Red": "红色精华",
    "Fire Resistance": "火焰抗性",
    "Frost Resistance": "冰霜抗性",
    "Nature Resistance": "自然抗性",
    "Shadow Resistance": "暗影抗性",
    "Arcane Resistance": "奥术抗性",
    "Lightweave": "亮纹",
    "Black Magic": "黑魔法",
    "Berserking": "狂暴",
    "Hyperspeed Acceleration": "超级加速",
    "Greatness": "伟大",
    "Emerald Vigor": "翡翠活力",
    "Speed of Light": "光速",
    "Essence of the Blood Queen": "鲜血女王精华",
    "Swarming Shadows": "蜂拥暗影",
    "Horn of Winter": "寒冬号角",
    "Guarded by the Light": "守护者的力量",
    "Divine Sacrifice": "神圣牺牲",
    "Illustration of the Dragon Soul": "龙魂图典",
    "Unstable Currents": "不稳定电流",
    "Light Essence": "光明精粹",
    "Well Fed": "进食充分",
    "Sated": "心满意足",
    "Exhaustion": "精疲力竭",
    "Temporal Displacement": "时空错位",
    # Trinket procs / buffs
    "Dying Curse": "垂死诅咒",
    "Nexus Residue": "能量残滓",
    "Eye of the Broodmother": " Broodmother之眼",
    "Extract of Necromantic Power": "亡灵能量精华",
    "Majestic Dragon Figurine": "巨龙塑像",
    "Je'Tze's Bell": "吉泽的铃铛",
    "Flare of the Heavens": "天堂烈焰",
    "Show of Faith": "信仰的证明",
    "Pandora's Plea": "潘多拉的恳求",
    "Meteorite Crystal": "陨星水晶",
    "Althor's Abacus": "阿尔索的算盘",
    "Sliver of Pure Ice": "纯净冰片",
    "Talisman of Resurgence": "复苏饰物",
    "Solace of the Defeated": "战败者的慰藉",
    "Solace of the Fallen": "堕落者的慰藉",
    "Reign of the Unliving": "亡者统治",
    "Reign of the Dead": "亡者统治",
    "Muradin's Spyglass": "穆拉丁的望远镜",
    "Dislodged Foreign Object": "被摘除的外物",
    "Phylactery of the Nameless Lich": "无名巫妖的护匣",
    "Charred Twilight Scale": "焦黑暮光龙鳞",
    "Sharpened Twilight Scale": "锋利暮光龙鳞",
    "Whispering Fanged Skull": "低语尖牙颅骨",
    "Deathbringer's Will": "死神意志",
    "Death's Choice": "死亡的选择",
    "Death's Verdict": "死亡的裁决",
    "Tiny Abomination in a Jar": "瓶中的小憎恶",
    "Heroic Tiny Abomination in a Jar": "英雄瓶中的小憎恶",
    "Bryntroll, the Bone Arbiter": "白骨仲裁者",
    "Shadowmourne": "影之哀伤",
    "Val'anyr, Hammer of Ancient Kings": "远古王者之锤",
    "Nibelung": "尼伯龙根",
    "Trauma": "创伤",
    "Cryptmaker": "掘墓者",
    "Black Bruise": "黑疽",
    "Heartpierce": "穿心者",
    "Heaven's Fall, Kryss of a Thousand Lies": "天堂陨落",
    "Corp'rethar Ceremonial Crown": "科雷萨仪式冠冕",
    "Cultist's Bloodsoaked Spaulders": "血浸肩甲",
    "Belt of the Merciless Killer": "无情杀手腰带",
    "Gangrenous Leggings": "坏疽腿铠",
    "Boots of Unnatural Growth": "畸变长靴",
    "Anub'ar Stalker's Gloves": "阿努巴尔猎手手套",
    "Band of the Bone Colossus": "巨骨指环",
    "Necklace of the Valiant": "勇者项链",
    "Ring of Rapid Ascent": "急速飞升指环",
    "Waistband of Despair": "绝望腰带",
    "Landsoul's Horned Greathelm": "兰索的巨盔",
    "Saurfang's Cold-Forged Band": "萨鲁法尔的寒铸指环",
    "Rot-Resistant Breastplate": "防腐胸甲",
    "Gloves of the Lifeless Touch": "死亡之触手套",
    "Polar Bear Claw Bracers": "北极熊爪护腕",
    "Snowstorm Helm": "雪风头盔",
    "Sanctified": "圣洁",
    "Heroic": "英雄",
    "Ashen Band of Endless Destruction": "灰烬指环·无尽毁灭",
    "Ashen Band of Unmatched Destruction": "灰烬指环·无双毁灭",
    "Ashen Band of Endless Courage": "灰烬指环·无尽勇气",
    "Ashen Band of Unmatched Courage": "灰烬指环·无双勇气",
    "Ashen Band of Endless Wisdom": "灰烬指环·无尽智慧",
    "Ashen Band of Unmatched Wisdom": "灰烬指环·无双智慧",
    "Ashen Band of Endless Vengeance": "灰烬指环·无尽复仇",
    "Ashen Band of Unmatched Vengeance": "灰烬指环·无双复仇",
    "Corroded Skeleton Key": "锈蚀骷髅钥匙",
    "Sindragosa's Flawless Fang": "辛达苟萨的 flawless 毒牙",
    "Juggernaut's Vitality": "主宰之力",
    "Satrina's Impeding Scarab": "萨崔娜的阻碍圣甲虫",
    "Corpse Tongue Coin": "尸舌硬币",
    "The Arbiter's Muse": "仲裁者的灵感",
    "Crypt Fiend Slayer": "地穴恶魔杀手",
    "Deathwhisper's Cache": "亡语者的宝箱",
    # Ring / neck procs
    "Aura of the Blue Dragon": "蓝龙光环",
    "Darkmoon Card: Greatness": "暗月卡牌：伟大",
    "Darkmoon Card: Death": "暗月卡牌：死亡",
    "Darkmoon Card: Berserker!": "暗月卡牌：狂暴！",
    "Darkmoon Card: Illusion": "暗月卡牌：幻象",
    "Death Knight's Anguish": "死亡骑士的苦难",
    "Mark of the Champion": "勇士印记",
    "Mark of the Defiler": "污染者印记",
    "Bando's Timer": "班多计时器",
    "Band of the Eternal Champion": "永恒勇士指环",
    "Band of the Eternal Defender": "永恒防御者指环",
    "Band of the Eternal Sage": "永恒先知指环",
    "Band of the Eternal Restorer": "永恒恢复者指环",
    # Weapon enchants / procs
    "Berserking": "狂暴",
    "Executioner": "处刑者",
    "Mongoose": "猫鼬",
    "Battlemaster": "战斗大师",
    "Spellsurge": "法术涌动",
    "Soulfrost": "灵魂冰霜",
    "Sunfire": "太阳之火",
    "Deathfrost": "死亡冰霜",
    "Greater Rune of Warding": "强效结界符文",
    "Greater Rune of Shielding": "强效护盾符文",
    # Set bonuses / tier
    "Item - Mage T10 2P Bonus": "法师T10 2件套",
    "Item - Mage T10 4P Bonus": "法师T10 4件套",
    "Item - Priest T10 2P Bonus": "牧师T10 2件套",
    "Item - Priest T10 4P Bonus": "牧师T10 4件套",
    "Item - Warlock T10 2P Bonus": "术士T10 2件套",
    "Item - Warlock T10 4P Bonus": "术士T10 4件套",
    "Item - Druid T10 2P Bonus": "德鲁伊T10 2件套",
    "Item - Druid T10 4P Bonus": "德鲁伊T10 4件套",
    "Item - Rogue T10 2P Bonus": "潜行者T10 2件套",
    "Item - Rogue T10 4P Bonus": "潜行者T10 4件套",
    "Item - Hunter T10 2P Bonus": "猎人T10 2件套",
    "Item - Hunter T10 4P Bonus": "猎人T10 4件套",
    "Item - Warrior T10 2P Bonus": "战士T10 2件套",
    "Item - Warrior T10 4P Bonus": "战士T10 4件套",
    "Item - Paladin T10 2P Bonus": "圣骑士T10 2件套",
    "Item - Paladin T10 4P Bonus": "圣骑士T10 4件套",
    "Item - Shaman T10 2P Bonus": "萨满T10 2件套",
    "Item - Shaman T10 4P Bonus": "萨满T10 4件套",
    "Item - Death Knight T10 2P Bonus": "死亡骑士T10 2件套",
    "Item - Death Knight T10 4P Bonus": "死亡骑士T10 4件套",
    "Item - Paladin T8 2P Bonus": "圣骑士T8 2件套",
    "Item - Paladin T8 4P Bonus": "圣骑士T8 4件套",
    "Item - Priest T8 2P Bonus": "牧师T8 2件套",
    "Item - Priest T8 4P Bonus": "牧师T8 4件套",
    "Item - Druid T8 2P Bonus": "德鲁伊T8 2件套",
    "Item - Druid T8 4P Bonus": "德鲁伊T8 4件套",
    "Item - Mage T8 2P Bonus": "法师T8 2件套",
    "Item - Mage T8 4P Bonus": "法师T8 4件套",
    "Item - Warlock T8 2P Bonus": "术士T8 2件套",
    "Item - Warlock T8 4P Bonus": "术士T8 4件套",
    "Item - Rogue T8 2P Bonus": "潜行者T8 2件套",
    "Item - Rogue T8 4P Bonus": "潜行者T8 4件套",
    "Item - Hunter T8 2P Bonus": "猎人T8 2件套",
    "Item - Hunter T8 4P Bonus": "猎人T8 4件套",
    "Item - Warrior T8 2P Bonus": "战士T8 2件套",
    "Item - Warrior T8 4P Bonus": "战士T8 4件套",
    "Item - Shaman T8 2P Bonus": "萨满T8 2件套",
    "Item - Shaman T8 4P Bonus": "萨满T8 4件套",
    "Item - Death Knight T8 2P Bonus": "死亡骑士T8 2件套",
    "Item - Death Knight T8 4P Bonus": "死亡骑士T8 4件套",
    "Item - Paladin T9 2P Bonus": "圣骑士T9 2件套",
    "Item - Paladin T9 4P Bonus": "圣骑士T9 4件套",
    "Item - Priest T9 2P Bonus": "牧师T9 2件套",
    "Item - Priest T9 4P Bonus": "牧师T9 4件套",
    "Item - Druid T9 2P Bonus": "德鲁伊T9 2件套",
    "Item - Druid T9 4P Bonus": "德鲁伊T9 4件套",
    "Item - Mage T9 2P Bonus": "法师T9 2件套",
    "Item - Mage T9 4P Bonus": "法师T9 4件套",
    "Item - Warlock T9 2P Bonus": "术士T9 2件套",
    "Item - Warlock T9 4P Bonus": "术士T9 4件套",
    "Item - Rogue T9 2P Bonus": "潜行者T9 2件套",
    "Item - Rogue T9 4P Bonus": "潜行者T9 4件套",
    "Item - Hunter T9 2P Bonus": "猎人T9 2件套",
    "Item - Hunter T9 4P Bonus": "猎人T9 4件套",
    "Item - Warrior T9 2P Bonus": "战士T9 2件套",
    "Item - Warrior T9 4P Bonus": "战士T9 4件套",
    "Item - Shaman T9 2P Bonus": "萨满T9 2件套",
    "Item - Shaman T9 4P Bonus": "萨满T9 4件套",
    "Item - Death Knight T9 2P Bonus": "死亡骑士T9 2件套",
    "Item - Death Knight T9 4P Bonus": "死亡骑士T9 4件套",
    # ICC buffs / special
    "Strengthened": "强化",
    "Hellscream's Warsong": "地狱咆哮的战歌",
    "Strength of Wrynn": "乌瑞恩之力",
    "Essence of the Blood Queen": "鲜血女王精华",
    "Swarming Shadows": "蜂拥暗影",
    "Pact of the Darkfallen": "堕落者契约",
    "Essence of the Vampyr Queen": "吸血鬼女王精华",
    "Bloodbolt Splash": "血箭溅射",
    "Frenzied Bloodthirst": "狂热血欲",
    "Essence of the Vampyr": "吸血鬼精华",
    "Insanity": "疯狂",
    "Gaseous Bloat": "气体膨胀",
    "Mutated Infection": "变异感染",
    "Unbound Plague": "解离瘟疫",
    "Ooze Variable": "软泥怪变量",
    "Gas Variable": "气体变量",
    "Vile Gas": "恶臭气体",
    "Malleable Goo": "可塑黏液",
    "Choking Gas": "窒息气体",
    "Regurgitated Ooze": "反刍软泥",
    "Volatile Ooze Adhesive": "不稳定软泥附着",
    "Gaseous Bloat Adhesive": "气体膨胀附着",
    "Slime Spray": "粘液喷射",
    "Mutated Slash": "变异劈砍",
    "Acidic Spew": "酸性喷吐",
    "Slime Puddle": "软泥水坑",
    "Icy Grip": "寒冰之握",
    "Boiling Blood": "沸血",
    "Rune of Blood": "鲜血符文",
    "Falling Rubble": "落石",
    "Stormhammer": "风暴之锤",
    "Searing Flame": "灼热烈焰",
    "Burning Pitch": "燃烧沥青",
    "Impaled": "穿刺",
    "Snobolled!": "雪球！",
    "Fire Bomb": "火焰炸弹",
    "Paralytic Toxin": "麻痹毒素",
    "Burning Bile": "燃烧胆汁",
    "Acid-Drenched Mandibles": "酸液浸透的巨颚",
    "Arctic Breath": "极寒吐息",
    "Ferocious Butt": "凶猛冲撞",
    "Massive Crash": "巨力冲击",
    "Staggered Daze": "蹒跚眩晕",
    "Frost Burn": "霜冻灼烧",
    "Mystic Buffet": "秘法打击",
    "Blistering Cold": "酷寒",
    "Frost Beacon": "冰霜信标",
    "Instability": "不稳定",
    "Chilled to the Bone": "寒彻骨髓",
    "Frost Aura": "冰霜光环",
    "Defile": "亵渎",
    "Harvest Soul": "收割灵魂",
    "Infest": "寄生",
    "Necrotic Plague": "死疽瘟疫",
    "Shadow Trap": "暗影陷阱",
    "Soul Reaper": "灵魂收割者",
    "Summon Shadow Trap": "召唤暗影陷阱",
    "Summon Val'kyr": "召唤瓦格里",
    "Summon Ice Sphere": "召唤冰球",
    "Raging Spirit": "暴怒的灵魂",
    "Ice Pulse": "寒冰脉冲",
    "Ice Burst": "寒冰爆裂",
    "Fury of Frostmourne": "霜之哀伤之怒",
    "Remorseless Winter": "冷酷寒冬",
    "Pain and Suffering": "痛苦与折磨",
    "Quake": "地震",
    "Blood Nova": "血之新星",
    "Blood Beast": "血兽",
    "Rune of Death": "死亡符文",
    "Frostbolt Volley": "寒冰箭齐射",
    "Death and Decay": "枯萎凋零",
    "Touch of Insignificance": "无足轻重之触",
    "Gut Spray": "内脏喷射",
    "Necrotic Strike": "死疽打击",
    "Dominate Mind": "支配心智",
    "Dark Evangelism": "黑暗福音",
    "Dark Archangel": "黑暗大天使",
    "Empowered Darkness": "强化暗影",
    "Empowered Light": "强化光明",
    "Surge of Darkness": "黑暗涌动",
    "Surge of Light": "圣光涌动",
    "Shield of the Occult": "神秘护盾",
    "Vengeful Shade": "复仇之魂",
    "Dark Reckoning": "黑暗清算",
    "Spirit Alarm": "灵魂警报",
    "Coldflame": "冷焰",
    "Bone Slice": "白骨切割",
    "Bone Storm": "白骨风暴",
    "Impaled": "穿刺",
    "Gaseous Spores": "气体孢子",
    "Inoculated": "接种",
    "Gastric Bloat": "胃胀",
    "Gas Spore": "气体孢子",
    "Vile Gas": "恶臭气体",
    "Pungent Blight": "刺鼻疫气",
    "Gastric Explosion": "胃爆",
    "Mortal Wound": "致命创伤",
    "Frenzied": "狂乱",
    "Enrage": "激怒",
    "Web Wrap": "蛛网缠绕",
    "Necrotic Wound": "坏死创伤",
    "Death Plague": "死亡瘟疫",
    "Siphon Essence": "吸取精华",
    "Decimate": "屠戮",
    "Terrifying Roar": "恐怖咆哮",
    "Fearsome Roar": "可怕咆哮",
    "Ferocious Roar": "凶猛咆哮",
    "Impaling Spine": "穿刺脊刺",
    "Burning Adrenaline": "燃烧刺激",
    "Tenebron": "塔尼布隆",
    "Shadron": "沙德隆",
    "Vesperon": "维斯匹隆",
    "Power Spark": "能量火花",
    "Static Field": "静电场",
    "Vortex": "漩涡",
    "Surge of Power": "能量涌动",
    "Arcane Overload": "奥术超载",
    "Hated": "憎恨",
    "Touch of Jaraxxus": "加拉克苏斯之触",
    "Mistress' Kiss": "女主人之吻",
    "Fel Fireball": "邪焰火球",
    "Fel Lightning": "邪能闪电",
    "Legion Flame": "军团烈焰",
    "Fel Inferno": "邪能地狱火",
    "Incinerate Flesh": "焚烧血肉",
    "Burning Inferno": "燃烧地狱火",
    "Nether Power": "虚空之力",
    "Nether Portal": "虚空之门",
    "Infernal Eruption": "地狱火喷发",
    "Touch of Light": "光明之触",
    "Touch of Darkness": "黑暗之触",
    "Light Vortex": "光明漩涡",
    "Dark Vortex": "黑暗漩涡",
    "Twin's Pact": "双子契约",
    "Surge of Acceleration": "加速涌动",
    "Shield of Darkness": "黑暗护盾",
    "Shield of Lights": "光明护盾",
    "Empowered Darkness": "强化黑暗",
    "Empowered Light": "强化光明",
    "Light Bomb": "光明炸弹",
    "Dark Bomb": "黑暗炸弹",
    "Dark Essence": "黑暗精粹",
    "Light Essence": "光明精粹",
    "Ball Lightning": "闪电球",
    "Storm Cloud": "风暴之云",
    "Static Disruption": "静电干扰",
    "Scorch": "灼烧",
    "Flash Freeze": "极速冻结",
    "Frozen": "冰冻",
    "Biting Cold": "刺骨严寒",
    "Arctic Cold": "极寒",
    "Permafrost": "永冻",
    "Toasty Fire": "温暖之火",
    "Storm Cloud": "风暴之云",
    "Watery Grave": "水之墓穴",
    "Tidal Wave": "潮汐之波",
    "Frostbolt": "寒冰箭",
    "Frost Nova": "冰霜新星",
    "Deep Freeze": "深度冻结",
    # Consumables / foods / flasks
    "Flask of the North": "北方合剂",
    "Flask of Endless Rage": "无尽怒气合剂",
    "Flask of the Frost Wyrm": "冰霜巨龙合剂",
    "Flask of Stoneblood": "石血合剂",
    "Flask of Pure Mojo": "纯净魔精合剂",
    "Flask of Distilled Wisdom": "精炼智慧合剂",
    "Flask of Supreme Power": "超级能量合剂",
    "Flask of Chromatic Resistance": "多重抗性合剂",
    "Elixir of Lightning Speed": "闪电速度药剂",
    "Elixir of Mighty Agility": "强效敏捷药剂",
    "Elixir of Mighty Strength": "强效力量药剂",
    "Elixir of Mighty Fortitude": "强效坚韧药剂",
    "Elixir of Mighty Thoughts": "强效思维药剂",
    "Elixir of Mighty Mageblood": "强效魔血药剂",
    "Elixir of Accuracy": "精准药剂",
    "Elixir of Armor Piercing": "破甲药剂",
    "Elixir of Deadly Strikes": "致命打击药剂",
    "Elixir of Expertise": "专长药剂",
    "Elixir of Lightning Speed": "闪电速度药剂",
    "Elixir of Protection": "防护药剂",
    "Elixir of Water Walking": "水上行走药剂",
    "Elixir of Minor Fortitude": "初级坚韧药剂",
    "Fish Feast": "鱼肉筵席",
    "Great Feast": "盛宴",
    "Blackened Dragonfin": "熏龙鱼",
    "Dragonfin Filet": "龙鱼片",
    "Firecracker Salmon": "爆竹鲑鱼",
    "Spicy Fried Herring": "香辣炸鲱鱼",
    "Spicy Blue Nettlefish": "香辣蓝网鱼",
    "Rhinolicious Wyrmsteak": "犀牛肉排",
    "Mega Mammoth Meal": "巨型猛犸肉餐",
    "Tender Shoveltusk Steak": "嫩铲齿鹿排",
    "Poached Northern Sculpin": "水煮北地鲂鱼",
    "Spicy Smoke Phoenix": "烟熏火鸡",
    "Cuttlesteak": "乌贼排",
    "Blackened Worg Steak": "熏狼排",
    "Hearty Rhino": "犀牛大餐",
    "Snapper Extreme": "极限鲷鱼",
    "Mighty Rhino Dogs": "巨型热狗",
    "Imperial Manta Steak": "帝王鳐排",
    "Worg Tartare": "狼肉塔塔",
    "Gigantic Feast": "巨型盛宴",
    "Small Feast": "小型盛宴",
    "Northern Spices": "北地香料",
    # Engineering items
    "Hyperspeed Acceleration": "超级加速",
    "Nitro Boosts": "硝基加速",
    "Hand-Mounted Pyro Rocket": "手部火箭发射器",
    "Hyperspeed Accelerators": "超级加速器",
    "Frag Belt": "破片腰带",
    "Sonic Booster": "音波增压器",
    "Noise Machine": "噪音机",
    "Gnomish Lightning Generator": "侏儒闪电发生器",
    "Gnomish X-Ray Specs": "侏儒X光眼镜",
    "Flexweave Underlay": "弹性编织衬底",
    "Springy Arachnoweave": "弹力蛛网",
    "Mind Amplification Dish": "心灵放大碟",
    "Nitro Boosts": "硝基加速",
    "Grounded Plasma Shield": "接地等离子护盾",
    "Quickflip Deflection Plates": "快速翻转偏转板",
    "Reticulated Armor Webbing": "网状护甲织带",
    "Spinal Healing Injector": "脊柱治疗注射器",
    "Mana Injector Kit": "法力注射器套件",
    # Gems / sockets
    "Chaotic Skyflare Diamond": "混乱天焰钻石",
    "Relentless Earthsiege Diamond": "残酷大地侵攻钻石",
    "Ember Skyflare Diamond": "余烬天焰钻石",
    "Insightful Earthsiege Diamond": "洞察大地侵攻钻石",
    "Tireless Skyflare Diamond": "不倦天焰钻石",
    "Beaming Earthsiege Diamond": "灿烂大地侵攻钻石",
    "Bracing Earthsiege Diamond": "稳固大地侵攻钻石",
    "Forlorn Skyflare Diamond": "孤寂天焰钻石",
    "Impassive Skyflare Diamond": "冷漠天焰钻石",
    "Revitalizing Skyflare Diamond": "复苏天焰钻石",
    "Persistent Earthshatter Diamond": "持久大地碎裂钻石",
    "Thundering Skyflare Diamond": "雷鸣天焰钻石",
    "Destructive Skyflare Diamond": "毁灭天焰钻石",
    "Enigmatic Skyflare Diamond": "神秘天焰钻石",
    "Swift Skyflare Diamond": "迅捷天焰钻石",
    "Runed Dragon's Eye": "符文龙眼石",
    "Bold Dragon's Eye": "明亮龙眼石",
    "Delicate Dragon's Eye": "精致龙眼石",
    "Brilliant Dragon's Eye": "辉煌龙眼石",
    "Subtle Dragon's Eye": "精妙龙眼石",
    "Flashing Dragon's Eye": "闪光龙眼石",
    "Fractured Dragon's Eye": "断裂龙眼石",
    "Precise Dragon's Eye": "精确龙眼石",
    "Solid Dragon's Eye": "坚硬龙眼石",
    "Sparkling Dragon's Eye": "火花龙眼石",
    "Lustrous Dragon's Eye": "光泽龙眼石",
    "Mystic Dragon's Eye": "秘法龙眼石",
    "Quick Dragon's Eye": "急速龙眼石",
    "Smooth Dragon's Eye": "平滑龙眼石",
    "Rigid Dragon's Eye": "刚硬龙眼石",
    "Thick Dragon's Eye": "厚重龙眼石",
    "Sovereign Dragon's Eye": "至高龙眼石",
    # Misc procs / buffs
    "Blood Fury": "血性狂暴",
    "Berserking": "狂暴",
    "Cannibalize": "食尸",
    "Will to Survive": "生存意志",
    "Every Man for Himself": "自利",
    "Escape Artist": "逃脱大师",
    "Gift of the Naaru": "纳鲁的赐福",
    "Shadowmeld": "影遁",
    "War Stomp": "战争践踏",
    "Arcane Torrent": "奥术洪流",
    "Mana Tap": "法力分流",
    "Rocket Barrage": "火箭弹幕",
    "Rocket Jump": "火箭跳跃",
    "Pack Hobgoblin": "打包地精",
    "Better Living Through Chemistry": "化学让生活更美好",
    "Time is Money": "时间就是金钱",
    "Rocket Boots Xtreme": "超级火箭靴",
    "Rocket Boots Xtreme Lite": "超级火箭靴精简版",
    "Parachute Cloak": "降落伞披风",
    "Nigh-Invulnerability Belt": "近似无敌腰带",
    "Goblin Rocket Launcher": "地精火箭发射器",
    "Gnomish Poultryizer": "侏儒变鸡器",
    "Super Sapper Charge": "超级工兵炸药",
    "Global Thermal Sapper Charge": "全球热力工兵炸药",
    "The Bigger One": "更大一号",
    "Adamantite Grenade": "精金手雷",
    "Fel Iron Bomb": "魔铁炸弹",
    "Arcane Bomb": "奥术炸弹",
    "Dark Iron Bomb": "黑铁炸弹",
    "Hi-Explosive Bomb": "高爆炸弹",
    "The Mortar: Reloaded": "迫击炮：重装版",
    "Goblin Mortar": "地精迫击炮",
    "Large Seaforium Charge": "大型爆盐炸弹",
    "Small Seaforium Charge": "小型爆盐炸弹",
    "Powerful Seaforium Charge": "强效爆盐炸弹",
    "Elemental Seaforium Charge": "元素爆盐炸弹",
    # PVP / arena
    "Arena Preparation": "竞技场准备",
    "Preparation": "伺机待发",
    "Readiness": "准备就绪",
    "Cold Blood": "冷血",
    "Prey on the Weak": "欺凌弱小",
    "Preparation": "准备就绪",
    "Blade Twisting": "剑刃扭转",
    "Deadened Nerves": "麻木神经",
    "Cheat Death": "装死",
    "Waylay": "埋伏",
    "Turn the Tables": "扭转局势",
    "Slaughter from the Shadows": "暗影杀戮",
    "Shadow Dance": "暗影之舞",
    "Filthy Tricks": "卑鄙伎俩",
    "Savage Combat": "野蛮战斗",
    "Combat Potency": "战斗潜能",
    "Surprise Attacks": "突袭",
    "Nerves of Steel": "钢铁神经",
    "Vitality": "活力",
    "Aggression": "侵略",
    "Dual Wield Specialization": "双武器专精",
    "Sword Specialization": "剑类武器专精",
    "Fist Weapon Specialization": "拳套武器专精",
    "Mace Specialization": "锤类武器专精",
    "Blade Flurry": "剑刃乱舞",
    "Adrenaline Rush": "冲动",
    "Killing Spree": "杀戮盛筵",
    "Riposte": "还击",
    "Reinforced Leather": "强化皮革",
    "Deflection": "偏斜",
    "Lightning Reflexes": "闪电反射",
    "Close Quarters Combat": "近身格斗",
    "Improved Sinister Strike": "强化邪恶攻击",
    "Endurance": "耐久",
    "Improved Sprint": "强化疾跑",
    "Improved Evasion": "强化闪避",
    "Heightened Senses": "强化感知",
    "Improved Kick": "强化脚踢",
    "Fleet Footed": "轻快步法",
    "Quick Recovery": "快速恢复",
    "Ghostly Strike": "鬼魅攻击",
    "Serrated Blades": "锯齿利刃",
    "Setup": "调整",
    "Initiative": "先发制人",
    "Elusiveness": "飘忽不定",
    "Dirty Deeds": "卑劣手段",
    "Hemorrhage": "出血",
    "Master of Subtlety": "敏锐大师",
    "Sinister Calling": "邪恶召唤",
    "Shadowstep": "暗影步",
    "Premeditation": "预谋",
    "Honor Among Thieves": "盗贼的尊严",
    "Slaughter from the Shadows": "暗影杀戮",
    "Filthy Tricks": "卑鄙伎俩",
    "Cheat Death": "装死",
    "Waylay": "埋伏",
    "Turn the Tables": "扭转局势",
    "Deadened Nerves": "麻木神经",
}


_translation_manager = TranslationManager(built_in_translations=NAME_TRANSLATIONS)


def translate_name(name: str, spell_id: int = None) -> str:
    """将 WCL 英文名称翻译为中文"""
    if not name:
        return name
    return _translation_manager.translate(name, spell_id=spell_id)


@dataclass
class FightInfo:
    """战斗信息"""
    report_code: str
    fight_id: int
    encounter_id: int
    encounter_name: str
    kill: bool
    duration_ms: int
    difficulty: int
    start_time: int
    end_time: int


@dataclass
class PlayerCompareData:
    """单个玩家在两次战斗中的对比数据"""
    name: str
    class_name: str
    spec: str

    # 战斗A数据
    dps_a: float = 0.0
    damage_a: int = 0
    ilvl_a: float = 0.0
    active_time_a: int = 0
    casts_a: List[Dict] = field(default_factory=list)
    buffs_a: List[Dict] = field(default_factory=list)
    debuffs_a: List[Dict] = field(default_factory=list)
    damage_breakdown_a: List[Dict] = field(default_factory=list)

    # 战斗B数据
    dps_b: float = 0.0
    damage_b: int = 0
    ilvl_b: float = 0.0
    active_time_b: int = 0
    casts_b: List[Dict] = field(default_factory=list)
    buffs_b: List[Dict] = field(default_factory=list)
    debuffs_b: List[Dict] = field(default_factory=list)
    damage_breakdown_b: List[Dict] = field(default_factory=list)

    @property
    def dps_delta(self) -> float:
        return self.dps_b - self.dps_a

    @property
    def dps_delta_pct(self) -> float:
        if self.dps_a == 0:
            return 0.0
        return (self.dps_delta / self.dps_a) * 100

    @property
    def ilvl_delta(self) -> float:
        return self.ilvl_b - self.ilvl_a


def compute_buff_uptime(raw_events: List[Dict], fight_duration_ms: int) -> List[Dict]:
    """
    从原始 Buff 事件计算覆盖率
    事件类型: applybuff, removebuff, refreshbuff
    """
    # 按 buff name 分组跟踪
    buff_states = {}  # name -> {active: bool, last_apply: int, total_ms: int, uses: int}

    for event in raw_events:
        etype = event.get("type", "")
        ability = event.get("ability", {})
        spell_id = ability.get("guid")
        name = translate_name(ability.get("name", "Unknown"), spell_id=spell_id)
        ts = event.get("timestamp", 0)

        if name not in buff_states:
            buff_states[name] = {"active": False, "last_apply": 0, "total_ms": 0, "uses": 0}

        state = buff_states[name]

        if etype == "applybuff":
            if not state["active"]:
                state["active"] = True
                state["last_apply"] = ts
                state["uses"] += 1
        elif etype == "removebuff":
            if state["active"]:
                state["total_ms"] += ts - state["last_apply"]
                state["active"] = False
        elif etype == "refreshbuff":
            # 刷新时，如果已经激活，累积已用时间，重置起点
            if state["active"]:
                state["total_ms"] += ts - state["last_apply"]
                state["last_apply"] = ts
            else:
                # 罕见情况：刷新时 buff 未标记为激活
                state["active"] = True
                state["last_apply"] = ts
                state["uses"] += 1

    # 战斗结束时还在生效的 buff，算到战斗结束
    results = []
    for name, state in buff_states.items():
        if state["active"]:
            # 这里无法知道确切的战斗结束时间，用最后一个事件时间近似
            # 但更好的做法是在调用处传入 end_time
            pass
        if state["total_ms"] > 0 or state["uses"] > 0:
            uptime_pct = (state["total_ms"] / max(fight_duration_ms, 1)) * 100
            results.append({
                "name": name,
                "uptime": min(uptime_pct, 100.0),
                "uses": state["uses"],
                "icon": ""
            })

    # 按覆盖率排序
    results.sort(key=lambda x: x["uptime"], reverse=True)
    return results


class FightComparator:
    """战斗对比器"""

    def __init__(self, client):
        self.client = client

    def fetch_fight_data(self, report_code: str, fight_id: int,
                         target_player: str = None) -> Tuple[FightInfo, Dict[int, Dict]]:
        """
        获取一次战斗的完整数据 (v2 GraphQL API)
        """
        # 获取报告基本信息
        report = self.client.get_report(report_code)
        fight = next((f for f in report["fights"] if f["id"] == fight_id), None)
        if not fight:
            raise ValueError(f"战斗 ID {fight_id} 不存在于报告 {report_code} 中")

        start_time = fight["startTime"]
        end_time = fight["endTime"]
        duration_ms = end_time - start_time

        fight_info = FightInfo(
            report_code=report_code,
            fight_id=fight_id,
            encounter_id=fight.get("encounterID", 0),
            encounter_name=translate_name(fight["name"]),
            kill=fight["kill"],
            duration_ms=duration_ms,
            difficulty=fight["difficulty"],
            start_time=start_time,
            end_time=end_time
        )

        # 获取全团伤害排行表（同时获取玩家基本信息）
        damage_entries = self.client.get_damage_table(report_code, fight_id)
        players = {}
        for entry in damage_entries:
            pid = entry.get("id")
            if not pid:
                continue
            # 从 icon 字段解析专精，如 "Mage-Frost" -> "Frost"
            icon = entry.get("icon", "")
            spec_name = icon.split("-")[-1] if "-" in icon else icon
            # 计算 DPS（perSecondAmount 可能为 None）
            dps = entry.get("perSecondAmount")
            if dps is None:
                active_time = entry.get("activeTime", 0)
                total = entry.get("total", 0)
                dps = total / (active_time / 1000) if active_time > 0 else 0
            players[pid] = {
                "id": pid,
                "name": entry.get("name", ""),
                "class_name": entry.get("type", "Unknown"),
                "spec": spec_name,
                "ilvl": entry.get("itemLevel", 0),
                "dps": dps,
                "total_damage": entry.get("total", 0),
                "active_time": entry.get("activeTime", 0),
            }

        # 确定目标玩家
        target_pid = None
        if target_player:
            for pid, pdata in players.items():
                if target_player.lower() in pdata["name"].lower():
                    target_pid = pid
                    break
            if not target_pid:
                available = ", ".join([p["name"] for p in players.values()])
                raise ValueError(f"找不到玩家 '{target_player}'。可选玩家: {available}")

        # 获取目标玩家的详细数据
        for pid in list(players.keys()):
            if target_pid and pid != target_pid:
                players[pid]["casts"] = []
                players[pid]["buffs"] = []
                players[pid]["debuffs"] = []
                continue

            pname = players[pid]["name"]

            # 施法记录
            try:
                print(f"  获取 {pname}(ID:{pid}) 的施法记录...")
                players[pid]["casts"] = self.client.get_casts(report_code, fight_id, pid)
            except Exception as e:
                print(f"  Warning: 获取施法记录失败 {pname}: {e}")
                players[pid]["casts"] = []

            def process_auras(raw, dur_ms, fight_start):
                for aura in raw:
                    spell_id = aura.get("guid")
                    aura["name"] = translate_name(aura.get("name", ""), spell_id=spell_id)
                    aura["uptime"] = (aura.get("totalUptime", 0) / dur_ms) * 100 if dur_ms > 0 else 0
                    aura["uses"] = aura.get("totalUses", 0)
                    # bands转为相对于战斗开始时间的百分比，用于时间轴图示
                    bands = []
                    for band in aura.get("bands", []):
                        s = band.get("startTime", 0)
                        e = band.get("endTime", 0)
                        sp = ((s - fight_start) / dur_ms) * 100 if dur_ms > 0 else 0
                        ep = ((e - fight_start) / dur_ms) * 100 if dur_ms > 0 else 0
                        bands.append((max(0, sp), min(100, ep)))
                    aura["bands_pct"] = bands
                return raw

            # Buff覆盖
            try:
                print(f"  获取 {pname}(ID:{pid}) 的 Buff 记录...")
                raw_buffs = self.client.get_buffs(report_code, fight_id, pid)
                players[pid]["buffs"] = process_auras(raw_buffs, duration_ms, start_time)
            except Exception as e:
                print(f"  Warning: 获取 Buff 记录失败 {pname}: {e}")
                players[pid]["buffs"] = []

            # Debuff覆盖
            try:
                print(f"  获取 {pname}(ID:{pid}) 的 Debuff 记录...")
                raw_debuffs = self.client.get_debuffs(report_code, fight_id, pid)
                players[pid]["debuffs"] = process_auras(raw_debuffs, duration_ms, start_time)
            except Exception as e:
                print(f"  Warning: 获取 Debuff 记录失败 {pname}: {e}")
                players[pid]["debuffs"] = []

            # 详细伤害统计（sourceid 单独查询）
            try:
                print(f"  获取 {pname}(ID:{pid}) 的详细伤害统计...")
                abilities = self.client.get_damage_table(report_code, fight_id, source_id=pid)
                print(f"  技能数量: {len(abilities)}")
                if abilities:
                    first = abilities[0]
                    print(f"  字段: {list(first.keys())}")
                    print(f"  示例: {first.get('name')} total={first.get('total')} hits={first.get('hitCount', 0)}")
                players[pid]["damage_breakdown"] = abilities
            except Exception as e:
                print(f"  Warning: 获取详细伤害统计失败 {pname}: {e}")
                players[pid]["damage_breakdown"] = []

        return fight_info, players

    def _aggregate_damage_events(self, events: List[Dict]) -> List[Dict]:
        """从原始伤害事件中聚合各技能的详细统计"""
        stats = {}  # name -> {total, hits, crits, ticks, amount_sum, amount_min, amount_max}
        
        for event in events:
            ability = event.get("ability", {})
            name = ability.get("name", "Unknown")
            hit_type = event.get("hitType", 1)
            amount = event.get("amount", 0)
            is_tick = event.get("tick", False)
            
            if name not in stats:
                stats[name] = {
                    "name": name,
                    "total": 0,
                    "hits": 0,
                    "crits": 0,
                    "ticks": 0,
                    "amount_sum": 0,
                    "amount_min": amount if amount > 0 else 0,
                    "amount_max": amount if amount > 0 else 0,
                }
            
            s = stats[name]
            s["total"] += amount
            s["amount_sum"] += amount
            if amount > 0:
                s["amount_min"] = min(s["amount_min"], amount) if s["amount_min"] > 0 else amount
                s["amount_max"] = max(s["amount_max"], amount)
            
            if is_tick:
                s["ticks"] += 1
            elif hit_type == 2:  # crit
                s["crits"] += 1
            else:
                s["hits"] += 1
        
        # 转换为标准格式
        result = []
        for name, s in stats.items():
            total_hits = s["hits"] + s["crits"] + s["ticks"]
            avg_hit = s["amount_sum"] / max(total_hits, 1)
            result.append({
                "name": name,
                "total": s["total"],
                "hitCount": s["hits"],
                "critHitCount": s["crits"],
                "tickCount": s["ticks"],
                "numberOfHits": s["hits"],
                "numberOfCrits": s["crits"],
                "numberOfTicks": s["ticks"],
                "averageHit": avg_hit,
                "meanHit": avg_hit,
                "hitMin": s["amount_min"],
                "hitMax": s["amount_max"],
            })
        
        # 按总伤害排序
        result.sort(key=lambda x: x["total"], reverse=True)
        return result

    def compare_fights(self, report_a: str, fight_a: int,
                       report_b: str, fight_b: int,
                       target_player: str = None) -> Dict:
        """
        对比两次战斗
        """
        print(f"获取战斗 A: {report_a} #{fight_a}...")
        info_a, players_a = self.fetch_fight_data(report_a, fight_a, target_player)

        print(f"获取战斗 B: {report_b} #{fight_b}...")
        info_b, players_b = self.fetch_fight_data(report_b, fight_b, target_player)

        comparison = {
            "fight_a": {
                "report": report_a,
                "id": fight_a,
                "name": info_a.encounter_name,
                "kill": info_a.kill,
                "duration_sec": info_a.duration_ms / 1000,
                "difficulty": info_a.difficulty
            },
            "fight_b": {
                "report": report_b,
                "id": fight_b,
                "name": info_b.encounter_name,
                "kill": info_b.kill,
                "duration_sec": info_b.duration_ms / 1000,
                "difficulty": info_b.difficulty
            },
            "players": []
        }

        # 找到共同的玩家
        all_names_a = {p["name"]: pid for pid, p in players_a.items()}
        all_names_b = {p["name"]: pid for pid, p in players_b.items()}

        common_names = set(all_names_a.keys()) & set(all_names_b.keys())
        print(f"  共同玩家 ({len(common_names)}人): {', '.join(sorted(common_names))}")

        if target_player:
            matched = {n for n in common_names
                      if target_player.lower() in n.lower()}
            print(f"  锁定玩家: {', '.join(matched) if matched else '无匹配'}")
            common_names = matched

        for name in sorted(common_names):
            pa = players_a[all_names_a[name]]
            pb = players_b[all_names_b[name]]

            pdata = PlayerCompareData(
                name=name,
                class_name=pa["class_name"],
                spec=pa["spec"],
                dps_a=pa.get("dps", 0),
                damage_a=pa.get("total_damage", 0),
                ilvl_a=pa.get("ilvl", 0),
                active_time_a=pa.get("active_time", 0),
                casts_a=pa.get("casts", []),
                buffs_a=pa.get("buffs", []),
                debuffs_a=pa.get("debuffs", []),
                damage_breakdown_a=pa.get("damage_breakdown", []),
                dps_b=pb.get("dps", 0),
                damage_b=pb.get("total_damage", 0),
                ilvl_b=pb.get("ilvl", 0),
                active_time_b=pb.get("active_time", 0),
                casts_b=pb.get("casts", []),
                buffs_b=pb.get("buffs", []),
                debuffs_b=pb.get("debuffs", []),
                damage_breakdown_b=pb.get("damage_breakdown", [])
            )
            comparison["players"].append(pdata)

        comparison["players"].sort(
            key=lambda p: abs(p.dps_delta),
            reverse=True
        )

        return comparison

    def analyze_casts(self, pdata: PlayerCompareData) -> Dict:
        """分析施法变化"""
        def count_casts(casts: List[Dict], duration_sec: float) -> Dict:
            # 分别统计两种事件：
            # - "begincast"(SPELL_CAST_START): 读条/引导开始，每个施法只触发一次
            # - "cast"(SPELL_CAST_SUCCESS): 施法成功/引导 tick，可能一个引导技能触发多次
            begin_counts = defaultdict(int)
            cast_counts = defaultdict(int)
            has_begincast = set()

            for cast in casts:
                etype = cast.get("type", "")
                # 缺少 type 字段的旧格式/模拟数据，按普通 cast 处理
                if etype == "":
                    etype = "cast"
                if etype not in ("cast", "begincast"):
                    continue
                ability = cast.get("ability", {})
                spell_id = ability.get("guid")
                name = translate_name(ability.get("name", "Unknown"), spell_id=spell_id)
                if etype == "begincast":
                    begin_counts[name] += 1
                    has_begincast.add(name)
                else:
                    cast_counts[name] += 1

            result = {}
            all_names = set(begin_counts.keys()) | set(cast_counts.keys())
            for name in all_names:
                # 如果某技能出现过 begincast，说明它是读条或引导技能，
                # 用 begincast 计数可以避免引导技能按 tick 被重复统计。
                # 对于顺发技能（只有 cast 事件），则使用 cast 计数。
                if name in has_begincast:
                    count = begin_counts[name]
                else:
                    count = cast_counts[name]
                result[name] = {
                    "count": count,
                    "cpm": round(count / (duration_sec / 60), 2) if duration_sec > 0 else 0
                }
            return result

        def extract_uses(entries: List[Dict]) -> Dict[str, int]:
            """从 WCL 伤害表条目中提取每个技能的施法次数 uses，合并同名条目取最大值"""
            uses = defaultdict(int)
            for entry in entries:
                spell_id = entry.get("guid")
                name = translate_name(entry.get("name", "Unknown"), spell_id=spell_id)
                value = entry.get("uses", 0)
                if value > uses[name]:
                    uses[name] = value
            return dict(uses)

        duration_a = pdata.active_time_a / 1000 if pdata.active_time_a > 0 else 1
        duration_b = pdata.active_time_b / 1000 if pdata.active_time_b > 0 else 1

        casts_a = count_casts(pdata.casts_a, duration_a)
        casts_b = count_casts(pdata.casts_b, duration_b)

        # 用 WCL 伤害表里的 uses 字段修正施法次数。
        # 某些技能（如法师深度冻结）每次实际施法会在事件里产生多个 cast 事件，
        # 但 WCL 伤害表的 uses 是权威施法次数。
        uses_a = extract_uses(pdata.damage_breakdown_a)
        uses_b = extract_uses(pdata.damage_breakdown_b)

        for name, data in casts_a.items():
            if name in uses_a and uses_a[name] > 0:
                data["count"] = uses_a[name]
                data["cpm"] = round(uses_a[name] / (duration_a / 60), 2) if duration_a > 0 else 0
        for name, data in casts_b.items():
            if name in uses_b and uses_b[name] > 0:
                data["count"] = uses_b[name]
                data["cpm"] = round(uses_b[name] / (duration_b / 60), 2) if duration_b > 0 else 0

        all_abilities = set(casts_a.keys()) | set(casts_b.keys())

        changes = []
        for ability in sorted(all_abilities):
            ca = casts_a.get(ability, {"count": 0, "cpm": 0})
            cb = casts_b.get(ability, {"count": 0, "cpm": 0})

            if ca["count"] == 0 and cb["count"] == 0:
                continue

            changes.append({
                "ability": ability,
                "count_a": ca["count"],
                "count_b": cb["count"],
                "count_delta": cb["count"] - ca["count"],
                "cpm_a": ca["cpm"],
                "cpm_b": cb["cpm"],
                "cpm_delta": round(cb["cpm"] - ca["cpm"], 2)
            })

        changes.sort(key=lambda x: abs(x["count_delta"]), reverse=True)
        return {
            "total_casts_a": sum(ca["count"] for ca in casts_a.values()),
            "total_casts_b": sum(cb["count"] for cb in casts_b.values()),
            "abilities": changes
        }

    def _analyze_aura_category(self, auras_a: List[Dict], auras_b: List[Dict]) -> List[Dict]:
        """分析一类光环（buffs或debuffs）的对比数据，保留bands用于时间轴"""
        dict_a = {b["name"]: b for b in auras_a}
        dict_b = {b["name"]: b for b in auras_b}
        all_names = set(dict_a.keys()) | set(dict_b.keys())

        changes = []
        for name in sorted(all_names):
            ba = dict_a.get(name, {"uptime": 0, "uses": 0, "bands_pct": []})
            bb = dict_b.get(name, {"uptime": 0, "uses": 0, "bands_pct": []})

            uptime_a = round(ba.get("uptime", 0), 1)
            uptime_b = round(bb.get("uptime", 0), 1)
            changes.append({
                "name": name,
                "uptime_a": uptime_a,
                "uptime_b": uptime_b,
                "uptime_delta": round(uptime_b - uptime_a, 1),
                "uses_a": ba.get("uses", 0),
                "uses_b": bb.get("uses", 0),
                "bands_a": ba.get("bands_pct", []),
                "bands_b": bb.get("bands_pct", []),
                "icon_a": ba.get("abilityIcon", ""),
                "icon_b": bb.get("abilityIcon", ""),
            })

        # 按名称排序
        changes.sort(key=lambda x: x["name"])
        return changes

    def analyze_buffs(self, pdata: PlayerCompareData) -> Dict:
        """分析增益覆盖变化，包含buffs和debuffs，保留bands用于时间轴"""
        return {
            "buffs": self._analyze_aura_category(pdata.buffs_a, pdata.buffs_b),
            "debuffs": self._analyze_aura_category(pdata.debuffs_a, pdata.debuffs_b),
        }

    def analyze_damage_breakdown(self, pdata: PlayerCompareData) -> Dict:
        """分析伤害构成变化（含单次伤害、暴击率、命中次数）"""
        def extract_damage(data: List[Dict]) -> Dict:
            result = {}
            for entry in data:
                spell_id = entry.get("guid")
                name = translate_name(entry.get("name", "Unknown"), spell_id=spell_id)
                total = entry.get("total", 0) or entry.get("totalReduced", 0)
                hits = entry.get("hitCount", 0) or entry.get("numberOfHits", 0)
                # DOT 暴击次数需要合并 critHitCount + critTickCount
                crits = (entry.get("critHitCount", 0) or entry.get("numberOfCrits", 0))
                crits += (entry.get("critTickCount", 0) or entry.get("numberOfCritTicks", 0))
                ticks = entry.get("tickCount", 0) or entry.get("numberOfTicks", 0)
                misses = entry.get("missCount", 0) or entry.get("numberOfMisses", 0)
                avg_hit = entry.get("averageHit", 0) or entry.get("meanHit", 0)
                if avg_hit == 0 and (hits + ticks) > 0:
                    avg_hit = total / max(hits + ticks, 1)

                if name in result:
                    # 同名条目合并（WCL 可能同时返回英文+中文版本）
                    existing = result[name]
                    existing["total"] += total
                    existing["hits"] += hits
                    existing["crits"] += crits
                    existing["ticks"] += ticks
                    existing["misses"] += misses
                    total_hits = existing["hits"] + existing["ticks"]
                    existing["avg_hit"] = existing["total"] / max(total_hits, 1)
                    existing["hit_min"] = min(existing["hit_min"], entry.get("hitMin", 0) or entry.get("minHit", 0) or float('inf'))
                    existing["hit_max"] = max(existing["hit_max"], entry.get("hitMax", 0) or entry.get("maxHit", 0))
                    existing["crit_min"] = min(existing["crit_min"], entry.get("critMin", 0) or entry.get("minCrit", 0) or float('inf'))
                    existing["crit_max"] = max(existing["crit_max"], entry.get("critMax", 0) or entry.get("maxCrit", 0))
                else:
                    result[name] = {
                        "total": total,
                        "hits": hits,
                        "crits": crits,
                        "ticks": ticks,
                        "misses": misses,
                        "avg_hit": avg_hit,
                        "hit_min": entry.get("hitMin", 0) or entry.get("minHit", 0),
                        "hit_max": entry.get("hitMax", 0) or entry.get("maxHit", 0),
                        "crit_min": entry.get("critMin", 0) or entry.get("minCrit", 0),
                        "crit_max": entry.get("critMax", 0) or entry.get("maxCrit", 0),
                    }
            return result

        dmg_a = extract_damage(pdata.damage_breakdown_a)
        dmg_b = extract_damage(pdata.damage_breakdown_b)

        total_a = sum(d["total"] for d in dmg_a.values()) or 1
        total_b = sum(d["total"] for d in dmg_b.values()) or 1

        all_abilities = set(dmg_a.keys()) | set(dmg_b.keys())

        changes = []
        for ability in sorted(all_abilities):
            da = dmg_a.get(ability, {"total": 0, "hits": 0, "crits": 0, "ticks": 0, "misses": 0, "avg_hit": 0, "avg_crit": 0, "hit_min": 0, "hit_max": 0, "crit_min": 0, "crit_max": 0})
            db = dmg_b.get(ability, {"total": 0, "hits": 0, "crits": 0, "ticks": 0, "misses": 0, "avg_hit": 0, "avg_crit": 0, "hit_min": 0, "hit_max": 0, "crit_min": 0, "crit_max": 0})

            pct_a = (da["total"] / total_a) * 100
            pct_b = (db["total"] / total_b) * 100

            # 计算平均每次伤害的变化
            avg_hit_delta = db["avg_hit"] - da["avg_hit"]
            avg_hit_delta_pct = (avg_hit_delta / max(da["avg_hit"], 1)) * 100 if da["avg_hit"] > 0 else 0

            # 暴击率
            total_hits_a = da["hits"] + da["ticks"]
            total_hits_b = db["hits"] + db["ticks"]
            crit_rate_a = round((da["crits"] / max(total_hits_a, 1)) * 100, 1) if total_hits_a > 0 else 0
            crit_rate_b = round((db["crits"] / max(total_hits_b, 1)) * 100, 1) if total_hits_b > 0 else 0

            changes.append({
                "ability": ability,
                "damage_a": da["total"],
                "damage_b": db["total"],
                "damage_delta": db["total"] - da["total"],
                "pct_a": round(pct_a, 1),
                "pct_b": round(pct_b, 1),
                "pct_delta": round(pct_b - pct_a, 1),
                # 命中次数
                "hits_a": da["hits"],
                "hits_b": db["hits"],
                "ticks_a": da["ticks"],
                "ticks_b": db["ticks"],
                "total_hits_a": total_hits_a,
                "total_hits_b": total_hits_b,
                # 平均每次伤害
                "avg_hit_a": round(da["avg_hit"], 0),
                "avg_hit_b": round(db["avg_hit"], 0),
                "avg_hit_delta": round(avg_hit_delta, 0),
                "avg_hit_delta_pct": round(avg_hit_delta_pct, 1),
                # 暴击率
                "crit_rate_a": crit_rate_a,
                "crit_rate_b": crit_rate_b,
                "crit_rate_delta": round(crit_rate_b - crit_rate_a, 1),
                # 暴击伤害范围（如有数据）
                "crit_min_a": da["crit_min"],
                "crit_max_a": da["crit_max"],
                "crit_min_b": db["crit_min"],
                "crit_max_b": db["crit_max"],
            })

        changes.sort(key=lambda x: abs(x["damage_delta"]), reverse=True)
        return {"abilities": changes}
