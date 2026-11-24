"""সরকারি চাকরি শনাক্তকরণ: বাংলা + ইংরেজি কীওয়ার্ড ও ক্লাসিফায়ার।

- শুধু Python স্ট্যান্ডার্ড লাইব্রেরি; কোনো নেটওয়ার্ক বা API লাগে না।
- মূল ফাংশন: is_govt(text, strict=False)
    strict=True  -> শুধু "নিশ্চিত সরকারি" নাম/ডোমেইন মিললে True (বেসরকারি-ট্যাগ করা সাইটে আপগ্রেডের জন্য)
    strict=False -> নিশ্চিত নাম, বা পুরোনো নিয়ম, বা স্কোর >= 2 (এবং কোনো বেসরকারি সংকেত নেই)
- ভুল-মিল এড়াতে:
    * "বেসরকারি", "non-government" আগে মুছে তারপর "সরকারি/government" খোঁজা হয়
      (কারণ "বেসরকারি"-র ভেতরেই "সরকারি" আছে)
    * ছোট ইংরেজি শব্দ (bgb, nbr, wasa ...) শুধু পুরো শব্দ হিসেবে মেলে
    * বাংলা অঙ্ক ইংরেজিতে বদলে (গ্রেড-১০ = grade-10), ZWJ/ZWNJ বাদ
"""
import re
import unicodedata

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def norm(s):
    s = unicodedata.normalize("NFC", s or "")
    s = s.replace("‌", "").replace("‍", "").replace("’", "'").replace("‘", "'")
    return s.translate(_BN_DIGITS).lower()


_ASCII = re.compile(r"[a-z0-9 .,&'()\-/]+")


def _compile(words):
    parts = []
    for w in sorted({norm(x).strip() for x in words if x and x.strip()}, key=len, reverse=True):
        e = re.escape(w)
        if _ASCII.fullmatch(w):  # ইংরেজি: পুরো শব্দ হিসেবে মেলাও
            e = r"(?<![a-z0-9])" + e + r"(?![a-z0-9])"
        parts.append(e)
    return re.compile("|".join(parts)) if parts else re.compile(r"(?!x)x")


def _count(rx, text):
    return len({m.group(0) for m in rx.finditer(text)})


# ============================================================ ১) STRONG
# একটা মিললেই সরকারি (নাম/ডোমেইন যথেষ্ট নির্দিষ্ট)
STRONG = [
    # --- ডোমেইন / পোর্টাল / আইনি পরিচয় ---
    ".gov.bd", "gov.bd", "teletalk", "alljobs.teletalk", "টেলিটক",
    "government of bangladesh", "govt. of bangladesh", "govt of bangladesh",
    "people's republic of bangladesh", "গণপ্রজাতন্ত্রী", "বাংলাদেশ সরকার",
    "bangladesh gazette", "বাংলাদেশ গেজেট", "national pay scale", "জাতীয় বেতন স্কেল",
    "জাতীয় বেতনস্কেল", "public service commission", "সরকারি কর্ম কমিশন", "bpsc", "বিপিএসসি",
    "বিসিএস", "bcs", "পিএসসি", "ntrca", "এনটিআরসিএ", "শিক্ষক নিবন্ধন ও প্রত্যয়ন কর্তৃপক্ষ",
    "সরকারি", "সরকারী", "আধা সরকারি", "আধাসরকারি", "রাষ্ট্রায়ত্ত", "state-owned", "state owned",
    # --- প্রশাসন ---
    "ministry", "মন্ত্রণালয়", "directorate", "অধিদপ্তর", "অধিদফতর", "পরিদপ্তর", "পরিদফতর",
    "bangladesh secretariat", "বাংলাদেশ সচিবালয়", "cabinet division", "মন্ত্রিপরিষদ বিভাগ",
    "prime minister's office", "প্রধানমন্ত্রীর কার্যালয়", "president's office", "রাষ্ট্রপতির কার্যালয়",
    "জনপ্রশাসন", "mopa", "election commission", "নির্বাচন কমিশন", "anti-corruption commission",
    "দুর্নীতি দমন কমিশন", "দুদক", "জাতীয় সংসদ সচিবালয়", "jatiya sangsad",
    "deputy commissioner's office", "dc office", "জেলা প্রশাসক", "জেলা প্রশাসকের কার্যালয়",
    "divisional commissioner", "বিভাগীয় কমিশনার", "district judge", "জেলা জজ",
    "জেলা ও দায়রা জজ", "supreme court", "সুপ্রিম কোর্ট", "হাইকোর্ট", "judge court", "জজ কোর্ট",
    "বিচার বিভাগ", "judicial service", "chief judicial magistrate", "মুখ্য মহানগর ম্যাজিস্ট্রেট",
    "auditor general", "মহা হিসাব নিয়ন্ত্রক", "comptroller and auditor", "হিসাবরক্ষণ অফিস",
    "accounts office", "controller general of accounts",
    # --- কর ও রাজস্ব ---
    "national board of revenue", "nbr", "জাতীয় রাজস্ব বোর্ড", "এনবিআর", "tax commissioner",
    "commissioner of taxes", "deputy commissioner of taxes", "taxes zone", "tax zone",
    "commissioner's office", "কর কমিশনার", "কর কমিশনারের কার্যালয়", "কর অঞ্চল", "কর অঞ্চল-",
    "customs house", "কাস্টম হাউস", "customs, excise", "শুল্ক ও আবগারি", "আবগারি", "vat commissionerate",
    "ভ্যাট কমিশনারেট", "land office", "ভূমি অফিস", "assistant commissioner (land)",
    "সহকারী কমিশনার (ভূমি)", "সহকারী কমিশনার ভূমি", "sub-registrar", "সাব-রেজিস্ট্রার",
    "passport office", "পাসপোর্ট অফিস", "department of immigration", "অভিবাসন ও পাসপোর্ট",
    # --- স্থানীয় সরকার ---
    "upazila nirbahi officer", "উপজেলা নির্বাহী অফিসার", "ইউএনও", "upazila parishad",
    "উপজেলা পরিষদ", "zila parishad", "জেলা পরিষদ", "union parishad", "union council",
    "ইউনিয়ন পরিষদ", "city corporation", "সিটি করপোরেশন", "সিটি কর্পোরেশন", "pourashava",
    "paurashava", "পৌরসভা", "local government", "স্থানীয় সরকার", "lged", "এলজিইডি", "dphe",
    "জনস্বাস্থ্য প্রকৌশল", "wasa", "ওয়াসা", "rajuk", "রাজউক", "চউক", "সিডিএ",
    # --- শিক্ষা ---
    "dshe", "dpe", "banbeis", "bteb", "nctb", "এনসিটিবি", "ugc", "university grants commission",
    "বিশ্ববিদ্যালয় মঞ্জুরী কমিশন", "ইউজিসি", "national university", "জাতীয় বিশ্ববিদ্যালয়",
    "public university", "বিশ্ববিদ্যালয় মঞ্জুরি কমিশন", "bangladesh open university",
    "বাংলাদেশ উন্মুক্ত বিশ্ববিদ্যালয়", "বুয়েট", "buet", "কুয়েট", "kuet", "রুয়েট", "ruet", "চুয়েট",
    "cuet", "শাবিপ্রবি", "sust", "মাদ্রাসা শিক্ষা বোর্ড", "madrasa education board",
    "কারিগরি শিক্ষা বোর্ড", "শিক্ষা বোর্ড", "প্রাথমিক শিক্ষা অধিদপ্তর",
    "directorate of primary education", "মাধ্যমিক ও উচ্চশিক্ষা", "মাধ্যমিক ও উচ্চ শিক্ষা",
    "secondary and higher education", "government college", "govt college", "govt. college",
    "government high school", "govt high school", "govt. high school", "government primary school",
    "govt primary school", "সরকারি প্রাথমিক বিদ্যালয়", "সরকারি কলেজ", "সরকারি মাধ্যমিক বিদ্যালয়",
    "teachers training college", "শিক্ষক প্রশিক্ষণ কলেজ", "polytechnic institute (govt)",
    # --- স্বাস্থ্য ---
    "dghs", "dgfp", "স্বাস্থ্য অধিদপ্তর", "স্বাস্থ্য অধিদফতর", "directorate general of health",
    "civil surgeon", "সিভিল সার্জন", "upazila health complex", "উপজেলা স্বাস্থ্য কমপ্লেক্স",
    "medical college hospital", "মেডিকেল কলেজ হাসপাতাল", "government hospital", "govt hospital",
    "সরকারি হাসপাতাল", "district hospital", "জেলা হাসপাতাল", "sadar hospital", "সদর হাসপাতাল",
    "community clinic", "কমিউনিটি ক্লিনিক", "bsmmu", "বিএসএমএমইউ", "nitor", "nicvd", "ipgmr",
    "dgnm", "নার্সিং ও মিডওয়াইফারি অধিদপ্তর", "nursing institute", "নার্সিং ইনস্টিটিউট",
    "স্বাস্থ্য ও পরিবার কল্যাণ", "health and family welfare", "পরিবার পরিকল্পনা অধিদপ্তর",
    # --- আইনশৃঙ্খলা / প্রতিরক্ষা ---
    "bangladesh police", "বাংলাদেশ পুলিশ", "police", "পুলিশ", "rapid action battalion", "র‍্যাব", "র্যাব", "apbn",
    "ansar & vdp", "ansar and vdp", "ansar-vdp", "ansar vdp", "আনসার ও ভিডিপি", "আনসার-ভিডিপি",
    "আনসার ভিডিপি", "বিজিবি", "bgb", "border guard bangladesh", "বর্ডার গার্ড", "coast guard",
    "কোস্ট গার্ড", "armed forces", "সশস্ত্র বাহিনী", "bangladesh army", "সেনাবাহিনী",
    "bangladesh navy", "নৌবাহিনী", "bangladesh air force", "বিমানবাহিনী", "বিমান বাহিনী",
    "fire service", "ফায়ার সার্ভিস", "civil defence", "সিভিল ডিফেন্স", "dgfi", "ডিজিএফআই",
    "ispr", "আইএসপিআর", "কারা অধিদপ্তর", "কারা অধিদফতর", "directorate of prison",
    "department of narcotics", "মাদকদ্রব্য নিয়ন্ত্রণ অধিদপ্তর", "ordnance factory", "অর্ডন্যান্স ফ্যাক্টরি",
    # --- রাষ্ট্রায়ত্ত ব্যাংক / আর্থিক ---
    "bangladesh bank", "বাংলাদেশ ব্যাংক", "sonali bank", "সোনালী ব্যাংক", "janata bank",
    "জনতা ব্যাংক", "agrani bank", "অগ্রণী ব্যাংক", "rupali bank", "রূপালী ব্যাংক", "bdbl",
    "বিডিবিএল", "bangladesh development bank", "বাংলাদেশ উন্নয়ন ব্যাংক", "krishi bank",
    "কৃষি ব্যাংক", "rajshahi krishi unnayan bank", "রাজশাহী কৃষি উন্নয়ন ব্যাংক", "rakub", "রাকাব",
    "basic bank", "বেসিক ব্যাংক", "probashi kallyan bank", "প্রবাসী কল্যাণ ব্যাংক",
    "karmasangsthan bank", "কর্মসংস্থান ব্যাংক", "ansar vdp unnayan bank", "bhbfc",
    "বাংলাদেশ হাউস বিল্ডিং ফিন্যান্স", "investment corporation of bangladesh",
    "বিনিয়োগ কর্পোরেশন", "sadharan bima corporation", "সাধারণ বীমা কর্পোরেশন",
    "jiban bima corporation", "jibon bima corporation", "জীবন বীমা কর্পোরেশন", "directorate of national savings",
    "সঞ্চয় অধিদপ্তর", "bsec", "বিএসইসি", "idra", "বীমা উন্নয়ন ও নিয়ন্ত্রণ কর্তৃপক্ষ",
    "microcredit regulatory authority", "মাইক্রোক্রেডিট রেগুলেটরি",
    # --- রাষ্ট্রায়ত্ত সংস্থা / ইউটিলিটি / পরিবহন ---
    "bpdb", "বিপিডিবি", "bangladesh power development board", "বিদ্যুৎ উন্নয়ন বোর্ড", "pgcb",
    "পিজিসিবি", "desco", "ডেসকো", "dpdc", "ডিপিডিসি", "nesco", "নেসকো", "wzpdcl", "apscl", "egcb",
    "nwpgcl", "rural electrification board", "পল্লী বিদ্যুৎ", "পল্লীবিদ্যুৎ", "petrobangla",
    "পেট্রোবাংলা", "bangladesh petroleum corporation", "বাংলাদেশ পেট্রোলিয়াম কর্পোরেশন", "titas gas",
    "তিতাস গ্যাস", "bakhrabad", "বাখরাবাদ", "jalalabad gas", "জালালাবাদ গ্যাস", "pashchimanchal gas",
    "পশ্চিমাঞ্চল গ্যাস", "karnaphuli gas", "কর্ণফুলী গ্যাস", "sundarban gas", "সুন্দরবন গ্যাস", "bapex",
    "বাপেক্স", "eastern refinery", "ইস্টার্ন রিফাইনারি", "padma oil", "পদ্মা অয়েল", "meghna petroleum",
    "মেঘনা পেট্রোলিয়াম", "jamuna oil", "যমুনা অয়েল", "btcl", "বিটিসিএল", "btrc", "বিটিআরসি",
    "bangladesh computer council", "বাংলাদেশ কম্পিউটার কাউন্সিল", "ict division", "আইসিটি বিভাগ",
    "biman bangladesh", "বিমান বাংলাদেশ", "civil aviation authority", "বেসামরিক বিমান চলাচল", "caab",
    "brtc", "বিআরটিসি", "biwta", "বিআইডব্লিউটিএ", "bangladesh railway", "বাংলাদেশ রেলওয়ে",
    "chittagong port authority", "chattogram port authority", "চট্টগ্রাম বন্দর", "mongla port",
    "মোংলা বন্দর", "payra port", "পায়রা বন্দর", "bangladesh shipping corporation", "roads and highways",
    "সড়ক ও জনপথ", "bangladesh bridge authority", "সেতু কর্তৃপক্ষ", "bscic", "বিসিক", "bsti",
    "বিএসটিআই", "bcsir", "বিসিএসআইআর", "bjmc", "বিজেএমসি", "bcic", "বিসিআইসি", "bfidc",
    "বিএফআইডিসি", "bsfic", "bmet", "জনশক্তি কর্মসংস্থান ও প্রশিক্ষণ ব্যুরো", "bwdb", "পানি উন্নয়ন বোর্ড",
    "পাউবো", "bangladesh post office", "বাংলাদেশ ডাক", "ডাক অধিদপ্তর", "ডাক বিভাগ", "ডাকঘর",
    "directorate of posts", "bangladesh betar", "বাংলাদেশ বেতার", "bangladesh television",
    "বাংলাদেশ টেলিভিশন", "বিটিভি", "বাংলাদেশ সংবাদ সংস্থা", "bangladesh sangbad sangstha", "bangladesh tea board",
    "বাংলাদেশ চা বোর্ড", "trading corporation of bangladesh", "টিসিবি", "বাংলাদেশ ট্রেডিং কর্পোরেশন",
    # --- কৃষি / মৎস্য / প্রাণিসম্পদ / সমাজকল্যাণ / অন্যান্য সেবা ---
    "department of agricultural extension", "কৃষি সম্প্রসারণ অধিদপ্তর", "brri", "বিজেআরআই", "bjri",
    "bfri", "barc", "department of fisheries", "মৎস্য অধিদপ্তর", "department of livestock",
    "প্রাণিসম্পদ অধিদপ্তর", "forest department", "বন অধিদপ্তর", "বন বিভাগ", "department of environment",
    "পরিবেশ অধিদপ্তর", "department of social services", "সমাজসেবা অধিদপ্তর", "সমাজসেবা কার্যালয়",
    "women and children affairs", "মহিলা ও শিশু বিষয়ক", "মহিলা বিষয়ক অধিদপ্তর",
    "youth development", "যুব উন্নয়ন অধিদপ্তর", "bksp", "বিকেএসপি", "জাতীয় ক্রীড়া পরিষদ",
    "bangla academy", "বাংলা একাডেমি", "shilpakala academy", "শিল্পকলা একাডেমি", "national museum",
    "জাতীয় জাদুঘর", "জাতীয় গ্রন্থাগার", "সরকারি গণগ্রন্থাগার", "islamic foundation", "ইসলামিক ফাউন্ডেশন",
    "ইসলামী ফাউন্ডেশন", "hindu welfare trust", "হিন্দু ধর্মীয় কল্যাণ ট্রাস্ট", "rural development board",
    "পল্লী উন্নয়ন বোর্ড", "বার্ড", "department of disaster management", "দুর্যোগ ব্যবস্থাপনা অধিদপ্তর",
    "directorate of food", "খাদ্য অধিদপ্তর", "খাদ্য অধিদফতর", "a2i", "aspire to innovate",
    "সমবায় অধিদপ্তর", "department of cooperatives",
]

# ============================================================ ২) MEDIUM (+1)
# একা যথেষ্ট নয়; মিলে স্কোর >= 2 হলে সরকারি ধরা হবে
MEDIUM = [
    "commission", "কমিশন", "secretariat", "সচিবালয়", "bureau", "ব্যুরো", "parliament",
    "জাতীয় সংসদ", "polytechnic", "পলিটেকনিক", "medical college", "মেডিকেল কলেজ", "court",
    "আদালত", "municipality", "treasury", "customs", "কাস্টমস", "শুল্ক", "রাজস্ব",
    "income tax", "আয়কর", "upazila", "upazilla", "উপজেলা", "সচিব", "secretary", "magistrate",
    "ম্যাজিস্ট্রেট", "ডিসি অফিস", "পরিসংখ্যান", "statistics", "নিবন্ধক", "registrar",
    "আনসার", "ansar", "vdp", "ভিডিপি", "কারাগার", "jail", "prison", "ফায়ার", "সেনা", "সৈনিক",
    "সিপাহী", "কনস্টেবল", "constable", "sub-inspector", "সাব-ইন্সপেক্টর", "সার্জেন্ট",
    "হাবিলদার", "havildar", "নায়েক", "মুক্তিযোদ্ধা কোটা", "freedom fighter quota", "কোটা সাপেক্ষে",
    "স্মারক নম্বর", "স্মারক নং", "নথি নং", "নিয়োগ কমিটি", "সদস্য সচিব", "রাষ্ট্রপতির আদেশক্রমে",
    "অস্থায়ী জনবল", "রাজস্ব খাত", "রাজস্ব বাজেট", "রাজস্বখাত", "জেলার প্রকৃত স্থায়ী বাসিন্দা",
    "প্রকৃত স্থায়ী বাসিন্দা", "বয়সে শিথিল", "বয়স শিথিল", "প্রতিবন্ধী কোটা", "ক্ষুদ্র নৃ-গোষ্ঠী কোটা",
    "বাংলাদেশের নাগরিক", "টেলিটক সিম", "teletalk sim", "জাতীয় বেতন", "cadre", "ক্যাডার",
    "ননক্যাডার", "নন-ক্যাডার", "non-cadre",
]

# ============================================================ ৩) WEAK (+0.5)
# সাধারণ প্রশাসনিক শব্দ ও পদবী; শিরোনামে একা কিছু প্রমাণ করে না
WEAK = [
    "authority", "কর্তৃপক্ষ", "council", "পরিষদ", "board", "বোর্ড", "division", "বিভাগ", "department",
    "কার্যালয়", "দপ্তর", "দফতর", "district", "জেলা", "hospital", "হাসপাতাল", "college", "কলেজ",
    "university", "বিশ্ববিদ্যালয়", "school", "বিদ্যালয়", "মাদ্রাসা", "madrasa", "অফিস সহকারী",
    "উচ্চমান সহকারী", "উচ্চমান", "নিম্নমান সহকারী", "প্রধান সহকারী", "head assistant",
    "মুদ্রাক্ষরিক", "সাঁট মুদ্রাক্ষরিক", "সাট মুদ্রাক্ষরিক", "সাটলিপিকার", "সাঁটলিপিকার", "stenographer",
    "stenotypist", "steno typist", "কম্পিউটার অপারেটর", "অফিস সহায়ক", "office assistant",
    "এমএলএসএস", "mlss", "দপ্তরী", "পিয়ন", "peon", "নিরাপত্তা প্রহরী", "night guard", "নিশি প্রহরী",
    "পরিচ্ছন্নতা কর্মী", "পরিচ্ছন্নকর্মী", "ঝাড়ুদার", "মালী", "উপসহকারী প্রকৌশলী",
    "sub-assistant engineer", "sub assistant engineer", "সহকারী প্রকৌশলী", "assistant engineer",
    "নির্বাহী প্রকৌশলী", "executive engineer", "তত্ত্বাবধায়ক প্রকৌশলী", "superintending engineer",
    "সহকারী কমিশনার", "assistant commissioner", "সহকারী সচিব", "assistant secretary",
    "সিনিয়র সহকারী সচিব", "যুগ্ম সচিব", "joint secretary", "উপ সচিব", "deputy secretary",
    "অতিরিক্ত সচিব", "additional secretary", "ব্যক্তিগত কর্মকর্তা", "সহকারী পরিচালক", "উপ পরিচালক",
    "assistant director", "deputy director", "হিসাবরক্ষক", "ক্যাশিয়ার", "cashier", "কর পরিদর্শক",
    "tax inspector", "কর সহকারী", "tax assistant", "customs inspector", "পরিদর্শক", "inspector",
    "সহকারী শিক্ষক", "প্রধান শিক্ষক", "সহকারী প্রধান শিক্ষক", "প্রভাষক", "lecturer", "সহকারী অধ্যাপক",
    "সহযোগী অধ্যাপক", "অধ্যাপক", "রেজিস্ট্রার", "পরীক্ষা নিয়ন্ত্রক", "প্রক্টর", "লাইব্রেরিয়ান",
    "চিকিৎসা কর্মকর্তা", "medical officer", "মেডিকেল অফিসার", "সহকারী সার্জন", "স্টাফ নার্স",
    "মিডওয়াইফ", "ফার্মাসিস্ট", "মেডিকেল টেকনোলজিস্ট", "প্রথম শ্রেণি", "দ্বিতীয় শ্রেণি",
    "তৃতীয় শ্রেণি", "চতুর্থ শ্রেণি", "first class", "second class", "third class", "fourth class",
    "application fee", "আবেদন ফি", "ইউনিয়ন ডিজিটাল সেন্টার", "প্রকল্পের মেয়াদ", "শূন্য পদে",
    "সরাসরি নিয়োগ", "অস্থায়ী ভিত্তিতে",
]

# ============================================================ ৪) PRIVATE সংকেত
# থাকলে (এবং STRONG না মিললে) সরকারি ধরা হবে না।
PRIVATE = [
    "ltd", "ltd.", "limited", "pvt", "pvt.", "(pvt)", "(pvt.)", "private", "লিমিটেড", "লিঃ", "লি:",
    "প্রাইভেট", "প্রাঃ", "বেসরকারি", "বেসরকারী", "non-government", "non government", "ngo",
    "এনজিও", "garments", "গার্মেন্টস", "textile", "টেক্সটাইল", "apparel", "knit", "industries",
    "ইন্ডাস্ট্রিজ", "pharmaceuticals", "ফার্মাসিউটিক্যালস", "pharma", "ফার্মা", "software",
    "সফটওয়্যার", "e-commerce", "ecommerce", "ই-কমার্স", "real estate", "রিয়েল এস্টেট", "brac",
    "ব্র্যাক", "grameen", "গ্রামীণ", "kindergarten", "কিন্ডারগার্টেন", "coaching", "কোচিং",
    "english medium", "ইংলিশ মিডিয়াম", "private university", "প্রাইভেট ইউনিভার্সিটি", "বেসরকারি বিশ্ববিদ্যালয়",
    "grameenphone", "গ্রামীণফোন", "banglalink", "বাংলালিংক", "robi axiata", "daraz", "pathao", "foodpanda",
]

# ============================================================ কম্পাইল
_STRONG_RX = _compile(STRONG)
_MEDIUM_RX = _compile(MEDIUM)
_WEAK_RX = _compile(WEAK)
_PRIVATE_RX = _compile(PRIVATE)

# "বেসরকারি"/"non-government"-এর ভেতরে "সরকারি/government" লুকিয়ে আছে; আগে মুছে ফেলি
_NONGOV = re.compile(r"non[\s\-]?gov(?:ernment|t)?\.?|বে[\s\-]?সরকার[িী]")

# গ্রেড-১০, grade 14, ১৬তম গ্রেড (বাংলা অঙ্ক আগেই ইংরেজি হয়ে যায়)
_GRADE_RX = re.compile(
    r"(?:গ্রেড|grade)[\s\-:]*(?:no\.?\s*)?(?:[1-9]|1\d|20)(?!\d)"
    r"|(?<!\d)(?:[1-9]|1\d|20)(?:ম|য়|র্থ|ষ্ঠ|তম|st|nd|rd|th)\s*(?:গ্রেড|grade)"
)

# আগের স্ক্র্যাপারের GOVT_RE-র সাথে সামঞ্জস্য (রিগ্রেশন এড়াতে), তবে বেসরকারি সংকেত থাকলে প্রযোজ্য নয়
_LEGACY_RX = re.compile(
    r"পরিষদ|বিশ্ববিদ্যালয়|(?<![a-z])govt(?![a-z])|(?<![a-z])government(?![a-z])|"
    r"(?<![a-z])department(?![a-z])|(?<![a-z])ministry(?![a-z])|(?<![a-z])railway(?![a-z])|"
    r"(?<![a-z])army(?![a-z])|(?<![a-z])navy(?![a-z])"
)


def analyze(text):
    """(strong:bool, legacy:bool, score:float, private_hits:int) — ডিবাগের জন্যও কাজে লাগে।"""
    t = norm(text)
    priv = _count(_PRIVATE_RX, t)
    c = _NONGOV.sub(" ", t)
    strong = bool(_STRONG_RX.search(c))
    score = _count(_MEDIUM_RX, c) + 0.5 * _count(_WEAK_RX, c) + (1.5 if _GRADE_RX.search(c) else 0)
    legacy = bool(_LEGACY_RX.search(c))
    return strong, legacy, score, priv


def is_govt(text, strict=False):
    strong, legacy, score, priv = analyze(text)
    if strong:
        return True
    if strict or priv:
        return False
    return legacy or score >= 2


def classify(text):
    """'govt' / 'private' / 'unknown' (নিশ্চিত না হলে 'unknown')।"""
    strong, legacy, score, priv = analyze(text)
    if strong:
        return "govt"
    if priv and score < 2:
        return "private"
    if legacy or score >= 2:
        return "govt" if not priv else "unknown"
    return "unknown"
