"""
Universal Multi-Genre Blueprint Generator Module
Dynamically constructs a 4-Part, 12-Chapter Master Outline tailored to ANY book genre.
"""

class BookBlueprint:
    def __init__(self, title: str, genre: str = "auto", domain: str = ""):
        self.title = title
        self.genre = self._detect_genre(genre, title)
        self.domain = domain or title
        self.parts = self._generate_blueprint()

    def _detect_genre(self, genre: str, title: str) -> str:
        g = genre.lower().strip()
        if g in ["tamil_historical", "historical_tamil", "வரலாறு", "வரலாற்று_நாவல்"]:
            return "tamil_historical"
        if g in ["tamil_kavithai", "kavithai", "கவிதை", "கவிதைகள்"]:
            return "tamil_kavithai"
        if g in ["tamil_thirukkural", "thirukkural", "திருக்குறள்"]:
            return "tamil_thirukkural"
        if g in ["tamil_fiction", "tamil_novel", "தமிழ்_நாவல்", "தமிழ்"]:
            return "tamil_fiction"
        if g in ["fiction", "sci-fi", "fantasy", "mystery", "thriller", "romance"]:
            return "fiction"
        if g in ["business", "leadership", "finance", "strategy"]:
            return "business"
        if g in ["self-help", "productivity", "mindset", "wellness"]:
            return "self-help"
        if g in ["technical", "software", "engineering", "data"]:
            return "technical"
        if g in ["non-fiction", "history", "science", "biography"]:
            return "non-fiction"

        # Auto-detect from title keywords
        t = title.lower()
        if any(w in t for w in ["சோழன்", "பாண்டியன்", "சேரன்", "பொன்னியின்", "வேள்பாரி", "வரலாறு", "காவியம்", "தஞ்சாவூர்"]):
            return "tamil_historical"
        if any(w in t for w in ["கவிதை", "கவிதைகள்", "காவியம்", "பாடல்"]):
            return "tamil_kavithai"
        if any(w in t for w in ["திருக்குறள்", "குறள்", "வள்ளுவர்"]):
            return "tamil_thirukkural"
        if any(w in t for w in ["novel", "chronicles", "shadow", "kingdom", "galaxy", "detective", "curse", "love", "blood", "game"]):
            return "fiction"
        if any(w in t for w in ["leadership", "business", "startup", "scale", "ceo", "management", "strategy", "revenue", "profit"]):
            return "business"
        if any(w in t for w in ["habit", "mindset", "success", "think", "discipline", "life", "guide to", "mastery", "happiness"]):
            return "self-help"
        if any(w in t for w in ["java", "python", "code", "system", "architecture", "ai-native", "cloud", "kafka", "oracle", "react", "angular"]):
            return "technical"

        return "non-fiction"

    def _generate_blueprint(self):
        if self.genre == "tamil_historical":
            return self._generate_tamil_historical_blueprint()
        elif self.genre == "tamil_kavithai":
            return self._generate_tamil_kavithai_blueprint()
        elif self.genre == "tamil_thirukkural":
            return self._generate_tamil_thirukkural_blueprint()
        elif self.genre == "tamil_fiction":
            return self._generate_tamil_fiction_blueprint()
        elif self.genre == "fiction":
            return self._generate_fiction_blueprint()
        elif self.genre == "business":
            return self._generate_business_blueprint()
        elif self.genre == "self-help":
            return self._generate_self_help_blueprint()
        elif self.genre == "technical":
            return self._generate_technical_blueprint()
        else:
            return self._generate_non_fiction_blueprint()

    def _generate_tamil_historical_blueprint(self):
        return [
            {
                "part": "பாகம் I: சோழ மண்டலச் சூழ்ச்சிகள் (Part I: The Chola Realm Secrets)",
                "chapters": [
                    { "number": 1, "title": "அத்தியாயம் 1: புயலுக்கு முன் அமைதி (The Quiet Before the Storm)", "focus": f"{self.domain} சாம்ராஜ்யத்தின் பின்னணி, இளவரசனின் அறிமுகம் மற்றும் முதல் சதி." },
                    { "number": 2, "title": "அத்தியாயம் 2: தூதுவனின் பயணம் (The Messenger's Journey)", "focus": "காவிரி ஆற்றங்கரைப் பயணம், ஒற்றர்களின் நடமாட்டம் மற்றும் இரகசியத் தகவல்." },
                    { "number": 3, "title": "அத்தியாயம் 3: அந்தப்புரத்து இரகசியங்கள் (Secrets of the Palace)", "focus": "அரண்மனை அரசியல், சோழ-பாண்டிய வீராங்கனைகள் மற்றும் பழங்காலச் சூழ்ச்சி." }
                ]
            },
            {
                "part": "பாகம் II: வாள்முனைக் கதைகள் (Part II: Tales of the Blade)",
                "chapters": [
                    { "number": 4, "title": "அத்தியாயம் 4: கடற்படைப் போர் (The Naval Fleet Battle)", "focus": "ஈழப் போர்முனை, சோழக் கடற்படையின் வீரம் மற்றும் எதிரிகளின் தந்திரம்." },
                    { "number": 5, "title": "அத்தியாயம் 5: துரோகத்தின் நிழல் (Shadow of Betrayal)", "focus": "உடன் இருந்தவரின் துரோகம், நாயகனின் வீழ்ச்சி மற்றும் புதிய சபதம்." },
                    { "number": 6, "title": "அத்தியாயம் 6: காடுகளின் இரகசியம் (The Secrets of the Jungle)", "focus": "தஞ்சை மாளிகை ரகசிய வழி, வேளீர் குலத் தலைவர்கள் மற்றும் இரகசியக் கூட்டணி." }
                ]
            },
            {
                "part": "பாகம் III: புயலின் நடுவே (Part III: In the Eye of the Storm)",
                "chapters": [
                    { "number": 7, "title": "அத்தியாயம் 7: கோட்டை முற்றுகை (Siege of the Fortress)", "focus": "மதுரைக் கோட்டை முற்றுகை, தற்காப்பு வியூகங்கள் மற்றும் நேரடி வாட்போர்." },
                    { "number": 8, "title": "அத்தியாயம் 8: சிம்மாசனப் போராட்டம் (Battle for the Throne)", "focus": "மகுடத்திற்கான போராட்டம், தியாகம் மற்றும் உண்மை வெளிப்படுதல்." },
                    { "number": 9, "title": "அத்தியாயம் 9: காதல் நெஞ்சம் (Heart of Devotion)", "focus": "போர்க்களத்தில் காதல், உணர்ச்சிப் போராட்டங்கள் மற்றும் பிரிவின் தவிப்பு." }
                ]
            },
            {
                "part": "பாகம் IV: வெற்றித் திலகம் (Part IV: Crown of Triumph)",
                "chapters": [
                    { "number": 10, "title": "அத்தியாயம் 10: இறுதிப் போர்முனை (The Final Battlefield)", "focus": "முழுமையான போர்க் களம், வியூகங்களின் வெற்றி மற்றும் எதிரியின் வீழ்ச்சி." },
                    { "number": 11, "title": "அத்தியாயம் 11: தியாகத்தின் சிகரம் (Summit of Sacrifice)", "focus": "அரியணையைத் துறத்தல், தியாகத்தின் உயர்வு மற்றும் நீதியின் வெற்றி." },
                    { "number": 12, "title": "அத்தியாயம் 12: புதிய உதயம் (A New Dawn)", "focus": "சோழ நாடங்கும் அமைதி, காவியத்தின் முடிவு மற்றும் காலத்தை வென்ற புகழாரம்." }
                ]
            }
        ]

    def _generate_tamil_kavithai_blueprint(self):
        return [
            {
                "part": "பாகம் I: இயற்கையும் காதலும் (Part I: Nature & Eternal Love)",
                "chapters": [
                    { "number": 1, "title": "அத்தியாயம் 1: பொன்மாலை பொழுது (Golden Sunset)", "focus": "இயற்கையின் எழில், மாலைக் காற்றின் மென்மை மற்றும் காதல் கவிதைகள்." },
                    { "number": 2, "title": "அத்தியாயம் 2: மழையும் மனமும் (Rain & The Soul)", "focus": "மழைத்துளிகளின் இசை, பிரிவின் ஏக்கம் மற்றும் கவித்துவ நயம்." },
                    { "number": 3, "title": "அத்தியாயம் 3: நிலவின் மொழி (Language of the Moon)", "focus": "இரவின் அமைதி, நிலவொளியில் பிறந்த கவிதைகள்." }
                ]
            },
            {
                "part": "பாகம் II: சமூகமும் சிந்தனையும் (Part II: Society & Thoughts)",
                "chapters": [
                    { "number": 4, "title": "அத்தியாயம் 4: மானுடம் பாடுவோம் (Singing for Humanity)", "focus": "சமூக சமத்துவம், மனித நேயம் மற்றும் புரட்சிச் சிந்தனைகள்." },
                    { "number": 5, "title": "அத்தியாயம் 5: உழைப்பின் உயர்வு (Dignity of Labor)", "focus": "பாட்டாளி வர்க்கக் கவிதைகள், உழைப்பின் கௌரவம்." },
                    { "number": 6, "title": "அத்தியாயம் 6: தமிழ் எங்கள் மூச்சு (Tamil is Our Breath)", "focus": "தமிழ் மொழியின் இன்பம், செம்மொழிப் பெருமை மற்றும் தாய்மொழிப் பற்று." }
                ]
            },
            {
                "part": "பாகம் III: தத்துவமும் ஆன்மீகமும் (Part III: Philosophy & Spirituality)",
                "chapters": [
                    { "number": 7, "title": "அத்தியாயம் 7: அகத்தின் அழகு (Beauty of the Inner Soul)", "focus": "மன அமைதி, தியானம் மற்றும் வாழ்க்கைத் தத்துவம்." },
                    { "number": 8, "title": "அத்தியாயம் 8: காலப் பெருவெளி (Cosmic Space of Time)", "focus": "காலத்தின் நகர்வு, நிலையாமை மற்றும் பிறவித் தத்துவம்." },
                    { "number": 9, "title": "அத்தியாயம் 9: ஞானத்தின் ஒளி (Light of Wisdom)", "focus": "மெய்ஞானக் கவிதைகள், சித்தர்கள் வாக்கு மற்றும் வாழ்வியல் நெறி." }
                ]
            },
            {
                "part": "பாகம் IV: புதிய உதயம் (Part IV: A New Sunrise)",
                "chapters": [
                    { "number": 10, "title": "அத்தியாயம் 10: விடியலின் கீதம் (Song of Dawn)", "focus": "நம்பிக்கைக் கவிதைகள், புதிய லட்சியங்கள் மற்றும் வெற்றிப் பாதை." },
                    { "number": 11, "title": "அத்தியாயம் 11: இளமையின் வேகம் (Youth & Energy)", "focus": "இளைஞர்களுக்கான எழுச்சிப் பாடல்கள் மற்றும் சாதனைகள்." },
                    { "number": 12, "title": "அத்தியாயம் 12: அமரக் கவிதைகள் (Immortal Verses)", "focus": "காலத்தை வென்ற கவிதைத் தொகுப்பின் முடிவு மற்றும் வாழ்த்து." }
                ]
            }
        ]

    def _generate_tamil_thirukkural_blueprint(self):
        return [
            {
                "part": "பாகம் I: அறத்துப்பால் - அறத்தின் நெறி (Part I: Virtue & Ethics)",
                "chapters": [
                    { "number": 1, "title": "அத்தியாயம் 1: கடவுள் வாழ்த்தும் வான்சிறப்பும் (Invocations)", "focus": "அகர முதல எழுத்தெல்லாம் மற்றும் மழை வளம் பற்றிய தெளிவுரை." },
                    { "number": 2, "title": "அத்தியாயம் 2: அறன் வலியுறுத்தல் (Power of Righteousness)", "focus": "மனத்துக்கண் மாசிலன் ஆதல் மற்றும் அறத்தின் மேன்மை." },
                    { "number": 3, "title": "அத்தியாயம் 3: இல்வாழ்க்கையும் அன்படைமையும் (Family & Love)", "focus": "அன்பும் அறனும் உடைத்தாயின் இல்வாழ்க்கை பண்பும் பயனும் அது." }
                ]
            },
            {
                "part": "பாகம் II: பொருட்பால் - அரசும் ஆளுமையும் (Part II: Governance & Wealth)",
                "chapters": [
                    { "number": 4, "title": "அத்தியாயம் 4: கல்வி மற்றும் கல்லாமை (Education & Knowledge)", "focus": "கற்க கசடறக் கற்பவை கற்றபின் நிற்க அதற்குத் தக." },
                    { "number": 5, "title": "அத்தியாயம் 5: ஆள்வினை உடைமை (Leadership & Perseverance)", "focus": "தெய்வத்தான் ஆகாது எனினும் முயற்சிதன் மெய்வருத்தக் கூலி தரும்." },
                    { "number": 6, "title": "அத்தியாயம் 6: நட்பு மற்றும் அமைச்சு (Friendship & Administration)", "focus": "செயற்கரிய செய்வார் பெரியர் மற்றும் நல்லமைச்சு நெறிகள்." }
                ]
            },
            {
                "part": "பாகம் III: காமத்துப்பால் - இன்பத்துப்பால் (Part III: Love & Emotions)",
                "chapters": [
                    { "number": 7, "title": "அத்தியாயம் 7: தகையணங்குறுத்தல் (Beauty of Affection)", "focus": "அணங்குகொல் ஆய்மயில் கொல்லோ மாதர் மாதர் நோக்கம்." },
                    { "number": 8, "title": "அத்தியாயம் 8: குறிப்பறிதல் (Understanding Eyes)", "focus": "கண்ணொடு கண்இணை நோக்கொக்கின் வாய்ச்சொற்கள் என்ன பயனும் இல." },
                    { "number": 9, "title": "அத்தியாயம் 9: புணர்ச்சி மகிழ்தல் (Joy of Union)", "focus": "கண்டு கேட்டு உண்டு உயிர்த்து உற்றறியும் ஐம்புலனும் கண் தொடி கண்ணே உளது." }
                ]
            },
            {
                "part": "பாகம் IV: வாழ்வியல் வழிகாட்டி (Part IV: Modern Life Guide)",
                "chapters": [
                    { "number": 10, "title": "அத்தியாயம் 10: தனிமனித ஒழுக்கம் (Personal Ethics)", "focus": "ஒழுக்கம் விழுப்பம் தரலான் ஒழுக்கம் உயிரினும் ஓம்பப் படும்." },
                    { "number": 11, "title": "அத்தியாயம் 11: வாய்மையும் இன்னா செய்யாமையும் (Truth & Non-Violence)", "focus": "பொய்மையும் வாய்மை இடத்த புரைதீர்ந்த நன்மை பயக்கும் எனின்." },
                    { "number": 12, "title": "அத்தியாயம் 12: திருக்குறள் காட்டும் உலகளாவிய நெறி (Universal Wisdom)", "focus": "வள்ளுவம் உலகிற்கு அளித்த நித்திய வழிகாட்டி மற்றும் தொகுப்பு." }
                ]
            }
        ]

    def _generate_tamil_fiction_blueprint(self):
        return [
            {
                "part": "பாகம் I: தொடக்கம் மற்றும் சவால்கள் (Part I: Beginnings)",
                "chapters": [
                    { "number": 1, "title": "அத்தியாயம் 1: புதிய மனிதன் (The New Man)", "focus": f"{self.domain} சூழலில் கதாநாயகனின் அறிமுகம் மற்றும் வாழ்க்கை மாற்றம்." },
                    { "number": 2, "title": "அத்தியாயம் 2: இரகசியச் சந்திப்பு (Secret Meeting)", "focus": "புதிய நண்பர்கள், எதிர்பாராத திருப்பம் மற்றும் முதல் பிரச்சனை." },
                    { "number": 3, "title": "அத்தியாயம் 3: புதிரான பாதை (Mysterious Path)", "focus": "பழைய நினைவுகள், குடும்பப் பின்னணி மற்றும் சவால்கள்." }
                ]
            },
            {
                "part": "பாகம் II: திருப்பங்களும் திருப்புமுனைகளும் (Part II: Turning Points)",
                "chapters": [
                    { "number": 4, "title": "அத்தியாயம் 4: உண்மைகள் வெளிப்படுதல் (Uncovering Truths)", "focus": "எதிரிகளின் திட்டம், துரோகங்கள் மற்றும் தீவிரப் போராட்டம்." },
                    { "number": 5, "title": "அத்தியாயம் 5: உணர்ச்சிப் போராட்டம் (Emotional Conflict)", "focus": "காதலும் குடும்பமும், மன அமைதியின்மை மற்றும் முக்கியமான முடிவு." },
                    { "number": 6, "title": "அத்தியாயம் 6: புதிய கூட்டணி (New Alliance)", "focus": "நம்பிக்கையான நண்பர்கள் இணைதல், புதிய உத்தி வகுத்தல்." }
                ]
            },
            {
                "part": "பாகம் III: உச்சக்கட்டப் போராட்டம் (Part III: Climax Prep)",
                "chapters": [
                    { "number": 7, "title": "அத்தியாயம் 7: நெருக்கடி நிலை (State of Crisis)", "focus": "எதிரியின் சதி உச்சம் அடைதல், கதாநாயகனின் சோதனைக் காலம்." },
                    { "number": 8, "title": "அத்தியாயம் 8: தைரியமான நகர்வு (Bold Move)", "focus": "எதிரிக்கு எதிரான எதிர் தாக்குதல், விறுவிறுப்பான காட்சிகள்." },
                    { "number": 9, "title": "அத்தியாயம் 9: தியாகத்தின் எல்லை (Limits of Sacrifice)", "focus": "உண்மையான தியாகம், அன்பின் வலிமை நிரூபணம்." }
                ]
            },
            {
                "part": "பாகம் IV: வெற்றி மற்றும் நிம்மதி (Part IV: Resolution)",
                "chapters": [
                    { "number": 10, "title": "அத்தியாயம் 10: இறுதி மோதல் (Final Showdown)", "focus": "கடைசிப் போராட்டம், நேருக்கு நேர் மோதல், நன்மையின் வெற்றி." },
                    { "number": 11, "title": "அத்தியாயம் 11: நீதி நிலைநாட்டப்படுதல் (Justice Restored)", "focus": "எதிரிகளின் வீழ்ச்சி, உண்மையான அமைதி திரும்புதல்." },
                    { "number": 12, "title": "அத்தியாயம் 12: புதிய விடியல் (A Brand New Dawn)", "focus": "கதையின் நிறைவு, புதிய எதிர்கால நோக்கிய பயணம்." }
                ]
            }
        ]

    def _generate_fiction_blueprint(self):
        return [
            {
                "part": "Part I: Shadows and Beginnings",
                "chapters": [
                    {
                        "number": 1,
                        "title": "The World Before the Storm",
                        "focus": f"Introducing the world of {self.domain}, character motivations, inciting incident, and initial conflict."
                    },
                    {
                        "number": 2,
                        "title": "A Call to the Unknown",
                        "focus": "Crossing the threshold, reluctant hero, new allies, and emerging threats."
                    },
                    {
                        "number": 3,
                        "title": "Whispers of the Past",
                        "focus": "Deepening history, hidden secrets, character backstory, and the first major obstacle."
                    }
                ]
            },
            {
                "part": "Part II: The Gathering Storm",
                "chapters": [
                    {
                        "number": 4,
                        "title": "Trials in the Dark",
                        "focus": "Escalating stakes, antagonist forces, test of loyalty, and tactical skirmishes."
                    },
                    {
                        "number": 5,
                        "title": "The Shattered Mirror",
                        "focus": "Midpoint twist, devastating betrayal, internal conflict, and loss of certainty."
                    },
                    {
                        "number": 6,
                        "title": "Bonds Forged in Fire",
                        "focus": "Alliance building, emotional growth, strategy formulation, and preparing for war."
                    }
                ]
            },
            {
                "part": "Part III: The Crucible of Fate",
                "chapters": [
                    {
                        "number": 7,
                        "title": "Into the Maw of Danger",
                        "focus": "Infiltration of enemy stronghold, rising action, race against time, high-stakes tension."
                    },
                    {
                        "number": 8,
                        "title": "The Hour of Darkness",
                        "focus": "All-is-lost moment, major sacrifice, emotional rock bottom, and renewed resolve."
                    },
                    {
                        "number": 9,
                        "title": "The Climax of Destiny",
                        "focus": "Final confrontation, epic duel/battle, character redemption, and ultimate climax."
                    }
                ]
            },
            {
                "part": "Part IV: Dawn and Legacy",
                "chapters": [
                    {
                        "number": 10,
                        "title": "Aftermath and Dust",
                        "focus": "Immediate resolution of conflict, mourning, victory assessment, and emotional closure."
                    },
                    {
                        "number": 11,
                        "title": "Rebuilding the World",
                        "focus": "Restoration of order, character transformation, new beginnings, and resolved subplots."
                    },
                    {
                        "number": 12,
                        "title": "An Endless Horizon",
                        "focus": "Epilogue, lasting impact of the journey, final thematic reflection, and future tease."
                    }
                ]
            }
        ]

    def _generate_business_blueprint(self):
        return [
            {
                "part": "Part I: Strategic Imperatives & Current Landscape",
                "chapters": [
                    {
                        "number": 1,
                        "title": f"The New Paradigm of {self.title}",
                        "focus": f"Market disruptions, systemic challenges, and the strategic imperative for {self.domain}."
                    },
                    {
                        "number": 2,
                        "title": "Deconstructing Legacy Business Models",
                        "focus": "Why traditional operational models fail, friction analysis, and market inefficiencies."
                    },
                    {
                        "number": 3,
                        "title": "The Core Value Creation Engine",
                        "focus": "Building competitive moats, customer-centric value propositions, and unit economics."
                    }
                ]
            },
            {
                "part": "Part II: Execution Frameworks & Organizational Alignment",
                "chapters": [
                    {
                        "number": 4,
                        "title": "High-Performance Leadership Mental Models",
                        "focus": "Decision-making frameworks, executive mindset, delegation, and accountability matrices."
                    },
                    {
                        "number": 5,
                        "title": "Optimizing Capital Allocation & Operations",
                        "focus": "Financial modeling, resource allocation, cost optimization, and margin expansion."
                    },
                    {
                        "number": 6,
                        "title": "Building Agile & Scalable Teams",
                        "focus": "Talent acquisition, culture design, cross-functional execution, and performance management."
                    }
                ]
            },
            {
                "part": "Part III: Growth, Innovation & Market Expansion",
                "chapters": [
                    {
                        "number": 7,
                        "title": "Scalable Growth & Acquisition Playbooks",
                        "focus": "Go-to-market strategies, customer acquisition channels, pricing models, and retention."
                    },
                    {
                        "number": 8,
                        "title": "Harnessing Data, AI & Technology Moats",
                        "focus": "Digital transformation, AI integration, operational automation, and technology leverage."
                    },
                    {
                        "number": 9,
                        "title": "Real-World Enterprise Case Studies",
                        "focus": "Deep dives into successful turnarounds, market expansions, and failure post-mortems."
                    }
                ]
            },
            {
                "part": "Part IV: Governance, Resilience & Long-Term Legacy",
                "chapters": [
                    {
                        "number": 10,
                        "title": "Risk Mitigation & Enterprise Resilience",
                        "focus": "Macroeconomic hedging, regulatory compliance, crisis management, and stress testing."
                    },
                    {
                        "number": 11,
                        "title": "Mergers, Acquisitions & Strategic Exits",
                        "focus": "Valuation drivers, M&A integration, strategic exits, and capital restructuring."
                    },
                    {
                        "number": 12,
                        "title": "The Future Roadmap & Sustainable Legacy",
                        "focus": "Long-term vision, continuous innovation, ESG impact, and executive summary."
                    }
                ]
            }
        ]

    def _generate_self_help_blueprint(self):
        return [
            {
                "part": "Part I: Awakening and Root Causes",
                "chapters": [
                    {
                        "number": 1,
                        "title": f"The Awakening: Understanding {self.title}",
                        "focus": f"Identifying limiting beliefs, cultural conditioning, and the root causes of friction in {self.domain}."
                    },
                    {
                        "number": 2,
                        "title": "The Psychology of Change and Self-Mastery",
                        "focus": "Neuroplasticity, emotional intelligence, cognitive reframing, and self-awareness."
                    },
                    {
                        "number": 3,
                        "title": "Auditing Your Internal Environment",
                        "focus": "Energy management, relationship audits, identifying habits, and clarifying core values."
                    }
                ]
            },
            {
                "part": "Part II: The Core Habit Architectures",
                "chapters": [
                    {
                        "number": 4,
                        "title": "Designing Daily Rituals & Systems",
                        "focus": "Morning routines, habit stacking, environment design, and friction reduction."
                    },
                    {
                        "number": 5,
                        "title": "Mastering Focus and Deep Work",
                        "focus": "Overcoming distraction, time blocking, attention management, and flow states."
                    },
                    {
                        "number": 6,
                        "title": "Emotional Resilience & Stress Mastery",
                        "focus": "Stoic principles, stress regulation, boundary setting, and burnout prevention."
                    }
                ]
            },
            {
                "part": "Part III: Overcoming Resistance & Achieving Mastery",
                "chapters": [
                    {
                        "number": 7,
                        "title": "Conquering Procrastination & Fear of Failure",
                        "focus": "Perfectionism traps, courage building, action orientation, and momentum loops."
                    },
                    {
                        "number": 8,
                        "title": "The Power of High-Impact Communication",
                        "focus": "Assertiveness, active listening, conflict resolution, and building deep relationships."
                    },
                    {
                        "number": 9,
                        "title": "Financial, Health & Vitality Alignment",
                        "focus": "Holistic energy management, physical health, financial independence, and lifestyle design."
                    }
                ]
            },
            {
                "part": "Part IV: Long-Term Transformation & Legacy",
                "chapters": [
                    {
                        "number": 10,
                        "title": "Sustaining Momentum Through Life Transitions",
                        "focus": "Adapting to change, handling setback, maintaining consistency over decades."
                    },
                    {
                        "number": 11,
                        "title": "Mentorship, Leadership & Service to Others",
                        "focus": "Giving back, leading by example, mentoring others, and building community."
                    },
                    {
                        "number": 12,
                        "title": "Your Blueprint for an Extraordinary Life",
                        "focus": "Final vision mapping, personal commitment contract, and summary checklist."
                    }
                ]
            }
        ]

    def _generate_technical_blueprint(self):
        return [
            {
                "part": "Part I: Foundations of Architecture & Paradigm Shift",
                "chapters": [
                    {
                        "number": 1,
                        "title": f"The Paradigm Shift in {self.title}",
                        "focus": f"Historical evolution, legacy anti-patterns, and architectural imperatives for {self.domain}."
                    },
                    {
                        "number": 2,
                        "title": "Core Runtime Execution & High Concurrency",
                        "focus": "Virtual threads, async executors, memory models, non-blocking I/O, and resilience primitives."
                    },
                    {
                        "number": 3,
                        "title": "Next-Gen Enterprise Persistence & Vector Storage",
                        "focus": "ACID compliance, converged schemas, document duality views, and semantic vector similarity search."
                    }
                ]
            },
            {
                "part": "Part II: Messaging, Event-Driven Streaming & Agent Protocols",
                "chapters": [
                    {
                        "number": 4,
                        "title": "Bridging Legacy Systems to Modern Streaming Pipelines",
                        "focus": "Enterprise integration patterns, JMS bridges, CDC connectors, and schema governance."
                    },
                    {
                        "number": 5,
                        "title": "Event-Driven Stream Processing Architecture",
                        "focus": "Topic partition topology, Stream-Table joins, transactional outbox pattern, and idempotency."
                    },
                    {
                        "number": 6,
                        "title": "Building Native Model Context Protocol (MCP) Tool Servers",
                        "focus": "MCP specification, JSON-RPC 2.0 primitives, tool registration, resource URIs, and SSE transports."
                    }
                ]
            },
            {
                "part": "Part III: User Interface Architecture & Agentic Workflows",
                "chapters": [
                    {
                        "number": 7,
                        "title": "Modern Frontend Portals & Fine-Grained Reactivity",
                        "focus": "Signal-based state primitives, standalone components, control flow syntax, and real-time SSE streams."
                    },
                    {
                        "number": 8,
                        "title": "Conversational UI & Agentic Co-Pilots",
                        "focus": "Web ReadableStream token parser, human-in-the-loop action approval cards, and copilot components."
                    },
                    {
                        "number": 9,
                        "title": "End-to-End System Implementation & Integration",
                        "focus": "Complete integration walkthrough connecting all tiers, Testcontainers integration suite, and execution logs."
                    }
                ]
            },
            {
                "part": "Part IV: Productionization, Security, and Governance",
                "chapters": [
                    {
                        "number": 10,
                        "title": "Enterprise Security, Zero Trust & Governance",
                        "focus": "OAuth2/OIDC JWT validation, PII masking engines, and cryptographic SHA-256 audit lineage tracking."
                    },
                    {
                        "number": 11,
                        "title": "Resilience, Scalability & Cloud-Native Deployment",
                        "focus": "GraalVM native image builds, multi-stage Dockerfiles, Kubernetes manifests, and HPA auto-scaling."
                    },
                    {
                        "number": 12,
                        "title": "The Future Roadmap & Long-Term System Evolution",
                        "focus": "Multi-agent autonomous matrix, operational reconciliation, and comprehensive architectural blueprint recap."
                    }
                ]
            }
        ]

    def _generate_non_fiction_blueprint(self):
        return [
            {
                "part": "Part I: Historical Origins & Theoretical Foundations",
                "chapters": [
                    {
                        "number": 1,
                        "title": f"The Genesis of {self.title}",
                        "focus": f"Historical background, early developments, foundational concepts, and key figures in {self.domain}."
                    },
                    {
                        "number": 2,
                        "title": "The Core Principles & Mechanics",
                        "focus": "Fundamental laws, underlying mechanics, key theories, and structural frameworks."
                    },
                    {
                        "number": 3,
                        "title": "Evolution Over the Decades",
                        "focus": "Pivotal historical milestones, paradigm shifts, technological breakthroughs, and societal impacts."
                    }
                ]
            },
            {
                "part": "Part II: Deep Analysis & Critical Perspectives",
                "chapters": [
                    {
                        "number": 4,
                        "title": "The Mechanics of Modern Transformations",
                        "focus": "In-depth case studies, structural analysis, modern mechanisms, and empirical evidence."
                    },
                    {
                        "number": 5,
                        "title": "Controversies, Misconceptions & Debate",
                        "focus": "Major debates, opposing viewpoints, myths debunked, and critical analysis."
                    },
                    {
                        "number": 6,
                        "title": "Global Perspectives & Cultural Variance",
                        "focus": "International comparisons, regional differences, cultural adaptation, and global trends."
                    }
                ]
            },
            {
                "part": "Part III: Practical Applications & Modern Impact",
                "chapters": [
                    {
                        "number": 7,
                        "title": "Real-World Case Studies & Breakthroughs",
                        "focus": "Detailed real-world applications, breakthrough discoveries, and measurable outcomes."
                    },
                    {
                        "number": 8,
                        "title": "Systemic Forces & Interdisciplinary Connections",
                        "focus": "Cross-domain implications, economic factors, policy impacts, and interdisciplinary connections."
                    },
                    {
                        "number": 9,
                        "title": "Lessons Learned from Failure and Triumph",
                        "focus": "Analyzing historic failures, successful turnarounds, key takeaways, and strategic insights."
                    }
                ]
            },
            {
                "part": "Part IV: Future Horizons & Lasting Legacy",
                "chapters": [
                    {
                        "number": 10,
                        "title": "Emerging Trends & Horizon Technologies",
                        "focus": "Next-generation developments, emerging research, future projections, and speculative horizons."
                    },
                    {
                        "number": 11,
                        "title": "Ethical Implications & Governance",
                        "focus": "Ethical frameworks, policy recommendations, environmental impact, and long-term sustainability."
                    },
                    {
                        "number": 12,
                        "title": "The Lasting Legacy & Synthesis",
                        "focus": "Comprehensive summary, lasting legacy, final reflections, and future outlook."
                    }
                ]
            }
        ]


# Genre metadata registries & helpers for Web and Streamlit UIs
TAMIL_GENRES = {
    "tamil_historical": {
        "name": "வரலாற்றுப் புதினம் (Historical Fiction)",
        "description": "சோழ, பாண்டிய, சேர சாம்ராஜ்யங்களின் அரசியல் சூழ்ச்சிகள், கடற்படைப் போர்கள் மற்றும் வீர காவியங்கள்."
    },
    "tamil_kavithai": {
        "name": "கவிதைத் தொகுப்பு (Poetry Anthology)",
        "description": "இயற்கை, காதல், வாழ்வியல் தத்துவம் மற்றும் சமூக சீர்திருத்தம் பாடும் நவீன கவிதைகள்."
    },
    "tamil_thirukkural": {
        "name": "திருக்குறள் வாழ்வியல் & மேலாண்மை (Thirukkural Guide)",
        "description": "அறத்துப்பால், பொருட்பால் வழியிலான அறநெறி, அரசியல் தந்திரம் மற்றும் தலைமைத்துவ வழிகாட்டி."
    },
    "tamil_fiction": {
        "name": "நவீன தமிழ் நாவல் (Modern Fiction)",
        "description": "மனித உணர்வுகள், சமூகப் போராட்டங்கள் மற்றும் மர்மங்கள் நிறைந்த நவீன தமிழ் புதினம்."
    }
}

BLUEPRINTS = {
    "fiction": "Fiction (Sci-Fi, Fantasy, Mystery, Thriller)",
    "business": "Business (Leadership, Strategy, Finance, Unicorn Scaling)",
    "self-help": "Self-Help (Productivity, Mindset, Habit Design)",
    "technical": "Technical (Software Engineering, System Design, AI-Native)",
    "non-fiction": "Non-Fiction (History, Science, Philosophy, Biography)",
    **{k: v["name"] for k, v in TAMIL_GENRES.items()}
}


def get_blueprint_for_genre(genre: str, title: str = "Blueprint") -> BookBlueprint:
    """Helper factory to retrieve a BookBlueprint instance for a genre."""
    return BookBlueprint(title=title, genre=genre)

