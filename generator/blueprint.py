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
        if self.genre == "fiction":
            return self._generate_fiction_blueprint()
        elif self.genre == "business":
            return self._generate_business_blueprint()
        elif self.genre == "self-help":
            return self._generate_self_help_blueprint()
        elif self.genre == "technical":
            return self._generate_technical_blueprint()
        else:
            return self._generate_non_fiction_blueprint()

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
