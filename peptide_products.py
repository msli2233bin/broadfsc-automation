# -*- coding: utf-8 -*-
"""
RTPeptide / rawpeptidemfg 肽产品目录（起始数据集）

说明：
- 所有产品仅供科研使用（Research Use Only），非人用药品。
- 字段用于 Groq 生成 Telegram 推广内容的依据，不含疗效承诺。
- 后续可由报价系统 / RTPeptide 后台导出自动同步扩充。
"""

# 8 大分类（对齐 RTPeptide 站点分类结构）
CATEGORIES = [
    "Weight Management",   # 体重管理
    "Healing & Repair",     # 修复愈合
    "Anti-Aging",           # 抗衰长寿
    "Growth Hormone",       # 生长激素
    "Cognitive & Mood",     # 认知情绪
    "Skin & Beauty",        # 皮肤美容
    "Sexual Health",        # 性健康
    "Sleep & Recovery",     # 睡眠恢复
]

# 产品列表（起始 20 个，覆盖全部分类）
PRODUCTS = [
    {
        "name": "Semaglutide",
        "category": "Weight Management",
        "cas": "910463-68-2",
        "sequence": "HA eg Lin S · K (C18 fatty acid) · A · G · T · FTSDVSSYLEGQAAKEFIAWLVKGR",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "GLP-1 receptor agonist. Studied for appetite regulation and glucose metabolism pathways in preclinical models.",
        "key_points": ["GLP-1 receptor agonist", "Appetite & metabolic research", "≥99% purity"],
    },
    {
        "name": "Tirzepatide",
        "category": "Weight Management",
        "cas": "2023788-19-2",
        "sequence": "GIP/GLP-1 dual agonist, 39-aa linear peptide",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "Dual GIP/GLP-1 receptor agonist. Dual incretin pathway research for metabolic regulation.",
        "key_points": ["Dual GIP/GLP-1", "Dual incretin mechanism", "Metabolic research"],
    },
    {
        "name": "Retatrutide",
        "category": "Weight Management",
        "cas": "2381089-83-2",
        "sequence": "Triple agonist (GLP-1/GIP/glucagon), 39-aa",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Triple hormone receptor agonist (GLP-1/GIP/glucagon). Triple-pathway metabolic research.",
        "key_points": ["Triple agonist", "GLP-1/GIP/glucagon", "Next-gen metabolic research"],
    },
    {
        "name": "BPC-157",
        "category": "Healing & Repair",
        "cas": "137525-51-0",
        "sequence": "GEPPPGKPADDAGLVGPTKKEDGPV",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "Body Protection Compound, 15-aa gastric peptide. Extensively studied for tissue repair and angiogenesis pathways.",
        "key_points": ["15-aa gastric peptide", "Tissue repair research", "Angiogenesis pathways"],
    },
    {
        "name": "TB-500 (Thymosin Beta-4)",
        "category": "Healing & Repair",
        "cas": "77591-33-4",
        "sequence": "Ac-SDKP · 38-aa fragment of Tβ4",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Synthetic fragment of Thymosin Beta-4. Studied for wound healing and cell migration in vitro.",
        "key_points": ["Tβ4 fragment", "Cell migration research", "Wound healing models"],
    },
    {
        "name": "GHK-Cu",
        "category": "Healing & Repair",
        "cas": "49557-75-7",
        "sequence": "Gly-His-Lys + Copper (II)",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "Copper peptide complex. Researched for collagen synthesis and skin tissue regeneration pathways.",
        "key_points": ["Copper peptide", "Collagen synthesis research", "Skin regeneration"],
    },
    {
        "name": "Epitalon (Epithalon)",
        "category": "Anti-Aging",
        "cas": "307297-39-8",
        "sequence": "EDG",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Tetrapeptide. Studied for telomerase activation and circadian rhythm regulation in aging models.",
        "key_points": ["Tetrapeptide", "Telomerase research", "Circadian regulation"],
    },
    {
        "name": "MOTS-c",
        "category": "Anti-Aging",
        "cas": "1627580-89-9",
        "sequence": "16-aa mitochondrial-derived peptide",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Mitochondrial-derived peptide. Researched for metabolic homeostasis and insulin sensitivity pathways.",
        "key_points": ["Mitochondrial peptide", "Metabolic homeostasis", "Insulin sensitivity research"],
    },
    {
        "name": "NAD+",
        "category": "Anti-Aging",
        "cas": "53-84-9",
        "sequence": "N/A (coenzyme)",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "Central cellular coenzyme. Researched for mitochondrial energy metabolism and sirtuin pathway support.",
        "key_points": ["Cellular coenzyme", "Mitochondrial energy", "Sirtuin pathway"],
    },
    {
        "name": "CJC-1295 (no DAC)",
        "category": "Growth Hormone",
        "cas": "863288-34-0",
        "sequence": "30-aa GHRH analog",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "GHRH analog. Studied for sustained GH release pulse patterns in endocrine research.",
        "key_points": ["GHRH analog", "GH pulse research", "Endocrine models"],
    },
    {
        "name": "Ipamorelin",
        "category": "Growth Hormone",
        "cas": "170851-70-4",
        "sequence": "Aib-His-D-2-Nal-D-Phe-Lys-NH2",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Selective GH secretagogue. Researched for GH release without prolactin/cortisol spike.",
        "key_points": ["Selective secretagogue", "Clean GH release", "No cortisol spike"],
    },
    {
        "name": "GHRP-6",
        "category": "Growth Hormone",
        "cas": "87616-84-0",
        "sequence": "H-His-D-Trp-Ala-Trp-D-Phe-Lys-NH2",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Hexapeptide GH secretagogue. Studied for GH stimulation and appetite pathways.",
        "key_points": ["Hexapeptide", "GH stimulation", "Appetite pathway research"],
    },
    {
        "name": "Semax",
        "category": "Cognitive & Mood",
        "cas": "80714-61-4",
        "sequence": "MEHFPGP (ACTH 4-10 analog)",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Synthetic nootropic peptide. Researched for neuroprotection and cognitive function pathways.",
        "key_points": ["Nootropic peptide", "Neuroprotection research", "Cognitive pathways"],
    },
    {
        "name": "Selank",
        "category": "Cognitive & Mood",
        "cas": "129954-34-3",
        "sequence": "Thr-Lys-Pro-Arg-Pro-Gly-Pro (tuftsin analog)",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Anxiolytic peptide. Researched for anxiety regulation and BDNF expression in CNS models.",
        "key_points": ["Anxiolytic peptide", "BDNF research", "CNS regulation"],
    },
    {
        "name": "DSIP",
        "category": "Sleep & Recovery",
        "cas": "62568-57-4",
        "sequence": "WAGGDASGE",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Delta sleep-inducing peptide. Studied for sleep architecture and stress response regulation.",
        "key_points": ["Sleep peptide", "Sleep architecture", "Stress regulation"],
    },
    {
        "name": "Melanotan II",
        "category": "Skin & Beauty",
        "cas": "121062-08-6",
        "sequence": "Ac-Nle-Asp-His-D-Phe-Arg-Trp-Lys-NH2",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Synthetic melanocortin agonist. Researched for pigmentation and photoprotection pathways.",
        "key_points": ["Melanocortin agonist", "Pigmentation research", "Photoprotection"],
    },
    {
        "name": "PT-141 (Bremelanotide)",
        "category": "Sexual Health",
        "cas": "189691-06-3",
        "sequence": "Ac-Nle-cyclo(Asp-His-D-Phe-Arg-Trp-Lys)-OH",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Melanocortin agonist. Researched for central pathways related to sexual function.",
        "key_points": ["Melanocortin agonist", "Central pathway research", "Sexual health models"],
    },
    {
        "name": "KPV",
        "category": "Healing & Repair",
        "cas": "67785-09-1",
        "sequence": "Lys-Pro-Val",
        "purity": "≥99%",
        "form": "Lyophilized powder",
        "research_focus": "Tripeptide (α-MSH fragment). Studied for anti-inflammatory and gut barrier research.",
        "key_points": ["Anti-inflammatory tripeptide", "Gut barrier research", "α-MSH fragment"],
    },
    {
        "name": "LL-37",
        "category": "Healing & Repair",
        "cas": "154947-54-3",
        "sequence": "37-aa cathelicidin antimicrobial peptide",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Human cathelicidin. Researched for antimicrobial and innate immune modulation pathways.",
        "key_points": ["Antimicrobial peptide", "Innate immune research", "Cathelicidin"],
    },
    {
        "name": "AOD-9604",
        "category": "Weight Management",
        "cas": "221231-10-3",
        "sequence": "HGH fragment 176-191",
        "purity": "≥98%",
        "form": "Lyophilized powder",
        "research_focus": "Modified HGH fragment. Studied for lipolytic (fat metabolism) pathways independent of IGF-1.",
        "key_points": ["HGH fragment 176-191", "Lipolytic research", "Fat metabolism"],
    },
]


def get_product_of_day(day_index=None):
    """按天轮换返回当日主推产品。"""
    import datetime
    if day_index is None:
        day_index = datetime.datetime.utcnow().timetuple().tm_yday
    return PRODUCTS[day_index % len(PRODUCTS)]


def products_by_category(cat):
    return [p for p in PRODUCTS if p["category"] == cat]


if __name__ == "__main__":
    print(f"Categories: {len(CATEGORIES)} | Products: {len(PRODUCTS)}")
    for c in CATEGORIES:
        print(f"  {c}: {len(products_by_category(c))} 个")
