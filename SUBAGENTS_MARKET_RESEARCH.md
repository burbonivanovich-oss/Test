# Subagents & Skills для Market Research, Поиска Ниш и Идей для Запуска Приложений/Расширений

Подборка готовых субагентов и skills (Claude Code, Codex, Cursor, Gemini CLI и др.), специализирующихся на исследовании рынка, поиске прибыльных ниш, генерации и валидации идей для SaaS / приложений / Chrome-расширений.

Дата сбора: 2026-05-04.

---

## 1. Market Research / Trend / Competitive Intelligence субагенты

### 1.1 VoltAgent/awesome-claude-code-subagents (категория `10-research-analysis`)
Эталонная коллекция 100+ субагентов. В разделе research-analysis уже готовы:

| Файл | Назначение |
|---|---|
| `market-researcher.md` | Анализ рыночной динамики, потребительского поведения, TAM/SAM/SOM |
| `trend-analyst.md` | Поиск emerging-паттернов, форсайт, ранние сигналы трендов |
| `competitive-analyst.md` | Конкурентная разведка, SWOT, бенчмарк позиционирования |
| `research-analyst.md` | Сводный исследователь по любой доменной области |
| `search-specialist.md` | Продвинутые поисковые техники и discovery источников |
| `project-idea-validator.md` | Жёсткая go/no-go валидация продуктовых идей |
| `data-researcher.md` | Стат-анализ датасетов, извлечение инсайтов |
| `scientific-literature-researcher.md` | Научпоп / academic research |

Репо: https://github.com/VoltAgent/awesome-claude-code-subagents

В категории `08-business-product` дополнительно есть `product-manager.md`, `ux-researcher.md`, `business-analyst.md`, `content-marketer.md` — релевантны для idea-shaping и go-to-market.

### 1.2 rohitg00/awesome-claude-code-toolkit
`agents/research-analysis/market-researcher.md` — количественные оценки рынка (top-down + bottom-up), фондрайзинг и GTM-решения, анализ опросов клиентов.
Репо: https://github.com/rohitg00/awesome-claude-code-toolkit

### 1.3 iflow-ai/NioPD
`core/agents/niopd/market-researcher.md` — функционирует как маркет-аналитик: web-search, summarization свежих отчётов, выделение трендов и стратегических implications.
Репо: https://github.com/iflow-ai/NioPD

### 1.4 alirezarezvani/claude-code-skill-factory
`generated-skills/content-trend-researcher/SKILL.md` — анализ трендов, уровень конкуренции, контентные возможности (полезно для расширений-обозревателей и контент-приложений).
Репо: https://github.com/alirezarezvani/claude-code-skill-factory

### 1.5 pytrak89/everything-claude-code-v2 и affaan-m/everything-claude-code
Оба содержат skill `market-research/SKILL.md` — самостоятельный навык маркет-ресёрча с шаблонами и workflow.
Репо: https://github.com/pytrak89/everything-claude-code-v2
Репо: https://github.com/affaan-m/everything-claude-code

---

## 2. Idea Generation / Validation / Niche Discovery

### 2.1 ferdinandobons/startup-skill
End-to-end startup pipeline (8 фаз, 30+ структурированных deliverable-ов): market research → competitive analysis → brand → product definition → финансовые прогнозы → эксперименты валидации.
Репо: https://github.com/ferdinandobons/startup-skill

### 2.2 bwerneckm/startup-skills
13 skills для оператора стартапа от валидации идеи до стратегического планирования. Каждый skill = 2–6 проверенных бизнес-фреймворков + fill-in шаблоны.
Репо: https://github.com/bwerneckm/startup-skills

### 2.3 rsmdt/the-startup (The Agentic Startup)
Коллекция Claude Code команд / skills / агентов специально под early-stage product building.
Репо: https://github.com/rsmdt/the-startup

### 2.4 slgoodrich/agents (AI PM Workflows)
8 экспертных PM-агентов 24/7 для research / strategy / execution / launch. 16 фреймворков, 100+ шаблонов.
Репо: https://github.com/slgoodrich/agents

### 2.5 phuryn/pm-skills
PM Skills Marketplace: 100+ agentic skills от discovery до growth. Есть отдельные плагины под market research.
Репо: https://github.com/phuryn/pm-skills

### 2.6 Startup Idea Validator (mcpmarket.com)
Хостовый skill: problem intensity / frequency scoring, go/no-go scorecard, дизайн smoke-test и landing-page экспериментов, скрипты customer-interview по "The Mom Test", фреймворки willingness-to-pay и fake-door тестов.
Источник: https://mcpmarket.com/tools/skills/startup-idea-validator

### 2.7 yoyothesheep/claude-skills
"Tested AI agents for common product building needs" — практически опробованные агенты под продуктовые задачи.
Репо: https://github.com/yoyothesheep/claude-skills

---

## 3. Growth, Marketing, Conversion (для оценки прибыльности ниши)

### 3.1 talknerdytome-labs/claude-agents
Production-ready growth-marketing субагенты: lead-generator, email-automator, CRM-specialist, business-analyst, growth-hacker, conversion-optimizer.
Репо: https://github.com/talknerdytome-labs/claude-agents

### 3.2 wshobson/agents
Multi-agent оркестрация под Claude Code, в т.ч. бизнес/маркетинг роли.
Репо: https://github.com/wshobson/agents

---

## 4. Зонтичные каталоги (где искать ещё)

| Репо | Что внутри |
|---|---|
| https://github.com/VoltAgent/awesome-agent-skills | 1000+ skills (Claude / Codex / Gemini CLI / Cursor) |
| https://github.com/ComposioHQ/awesome-claude-skills | 1000+ production-ready skills |
| https://github.com/alirezarezvani/claude-skills | 232+ skills (engineering, marketing, product, compliance, C-level) |
| https://github.com/hesreallyhim/awesome-claude-code | Зонтичный awesome для Claude Code |
| https://github.com/rahulvrane/awesome-claude-agents | Сборник субагентов |
| https://github.com/heilcheng/awesome-agent-skills | Туториалы, гайды, директории skills |
| https://github.com/Nix2828/collective-agent-skills | 500+ skills (мульти-CLI совместимость) |
| https://github.com/zhsama/claude-sub-agent | AI-driven workflow: идея → продакшн через скоординированных агентов |
| https://claudemarketplaces.com/ | Маркетплейс Claude Code плагинов / skills / MCP серверов |
| https://www.awesomeskills.dev/en | Директория Claude / Codex / Cursor skills |

---

## 5. Рекомендуемый стек под задачу «искать прибыльные ниши и формировать идеи приложений/расширений»

Минимально-достаточный комплект, который можно собрать прямо в `.claude/agents/`:

1. **trend-analyst** (VoltAgent) — ранние сигналы спроса.
2. **market-researcher** (VoltAgent или NioPD) — TAM/SAM/SOM, потребительские инсайты.
3. **competitive-analyst** (VoltAgent) — карта конкурентов, gap-анализ.
4. **content-trend-researcher** (alirezarezvani skill-factory) — что ищут / что плохо покрыто контентом → ниши для расширений и инфо-приложений.
5. **project-idea-validator** (VoltAgent) + **Startup Idea Validator** (mcpmarket) — двойная фильтрация идей.
6. **product-manager** + **ux-researcher** (VoltAgent 08-business-product) — превращение ниши в продуктовую концепцию.
7. **growth-hacker / conversion-optimizer** (talknerdytome-labs) — оценка монетизируемости и каналов привлечения.
8. **startup-skill** (ferdinandobons) или **startup-skills** (bwerneckm) — обвязка end-to-end pipeline.

Оркестрация: `wshobson/agents` или `zhsama/claude-sub-agent` как мета-оркестратор, прогоняющий идею по всем агентам последовательно.

---

## 6. Что дальше

- Клонировать `VoltAgent/awesome-claude-code-subagents` и `bwerneckm/startup-skills` в `.claude/agents/` и `.claude/skills/` соответственно.
- Прогнать пилот: сгенерировать 20 ниш через `trend-analyst` + `content-trend-researcher`, отфильтровать через `project-idea-validator`, оставить топ-3 для оформления в продуктовые концепции.
- При желании — обернуть pipeline в slash-команду `/find-niches` через `claude-code-skill-factory`.
