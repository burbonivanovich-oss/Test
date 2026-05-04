# Детальный анализ и сравнение субагентов / skills

Глубокий разбор каждого субагента из каталога `SUBAGENTS_MARKET_RESEARCH.md`: какие инструменты использует, по какой методологии работает, какие deliverables выдаёт, в чём сильные и слабые стороны и где он уникален относительно остальных.

---

## A. Отдельные субагенты (атомарные)

### A1. VoltAgent · `market-researcher.md`
- **Tools:** Read, Grep, Glob, WebFetch, WebSearch.
- **Методология:** market sizing, value-chain, регуляторика, поведенческий анализ, сегментация, ethnographic / social listening, SWOT, positioning maps.
- **Deliverables:** executive summary, конкурентный/потребительский анализ, визуальные отчёты, ROI и risk-проекции.
- **Сильные стороны:** широкий охват «классического» маркет-ресёрча, готовая интеграция с product-manager и competitive-analyst.
- **Слабые стороны:** TAM/SAM/SOM явно не зашиты, нет акцента на статистическую дисциплину. По сути — generic ресёрчер.
- **Когда брать:** базовый рабочий конь для общего разведывания рынка.

### A2. VoltAgent · `trend-analyst.md`
- **Tools:** Read, Grep, Glob, WebFetch, WebSearch.
- **Методология:** time-series, pattern matching, predictive modelling, scenario planning, systems thinking. Источники: соцсети, поисковые тренды, **патенты**, академические работы, отраслевые отчёты, новости, экспертные комментарии.
- **Deliverables:** trend reports, impact assessment по 3 осям (рынок/бизнес/технология), 6+ сценариев, opportunity/risk анализ, monitoring setup.
- **Сильные стороны:** единственный из «коробки», который тянет patents + academic. Отлично для раннего поиска ниш.
- **Слабые стороны:** не валидирует идеи, не считает рынок; нужен в связке.
- **Когда брать:** первая фаза — обнаружение «слабых сигналов».

### A3. VoltAgent · `competitive-analyst.md`
- **Tools:** Read, Grep, Glob, WebFetch, WebSearch.
- **Методология:** SWOT, **Porter (5 сил, явно)**, benchmarking, position maps, value curves, финансовый анализ конкурентов.
- **Deliverables:** competitive intelligence reports, gap-анализ, defense/attack стратегии, monitoring и алерты.
- **Сильные стороны:** единственный из VoltAgent с явным Porter; покрывает substitutes и adjacent markets.
- **Слабые стороны:** не делает sizing рынка и не валидирует идею, не работает с Ad-libraries.
- **Когда брать:** после market-researcher, перед idea-validator.

### A4. VoltAgent · `project-idea-validator.md`
- **Tools:** Read, **Write, Edit**, Glob, Grep, WebFetch, WebSearch (single — пишет deliverables в файлы).
- **Методология:** 8-мерный scorecard (demand, competition, uniqueness, difficulty, audience, weaknesses, strengths, viability) → 3 фазы (Assessment → Implementation → Excellence). Дефолт-скепсис: «каждая идея flawed, пока не доказано обратное».
- **Deliverables:** competitive teardown, search-volume saturation, MVP scope, risk matrix (market/execution/tech/regulatory), pivot suggestions, чёткий go/no-go.
- **Сильные стороны:** жёсткий фильтр + готовые pivot-предложения. Идеален как «вторая инстанция».
- **Слабые стороны:** не делает discovery (нужен upstream агент, кидающий идеи).
- **Когда брать:** после генерации идей, перед MVP.

### A5. rohitg00 · `market-researcher.md`
- **Tools:** Read, Write, Edit, Bash, Glob, Grep (НЕ имеет WebFetch/WebSearch из коробки — рассчитан на локальные данные / pipe из других инструментов).
- **Методология:** **топ-даун + боттом-ап TAM (расхождение ≤30%)**, статистическая дисциплина (margin of error <5% при 95% confidence), три сценария (cons/base/opt), SOM привязан к производственным мощностям (1–2% SAM на год 1).
- **Deliverables:** segmentation с границами, TAM/SAM/SOM с источниками, опросы, customer profiles.
- **Сильные стороны:** единственный, кто **формально требует доказательств и статистики**. Защита от «красивых, но липовых» цифр.
- **Слабые стороны:** нет встроенного web — нужен внешний фидер источников.
- **Когда брать:** когда уже есть данные / отчёты и нужно из них вывести defensible цифры для инвесторов.

### A6. iflow-ai · NioPD `market-researcher.md`
- **Tools:** WebSearch, WebFetch, Read, Grep, Bash.
- **Методология:** жёсткий 8-шаговый pipeline: refinement → query strategy → source discovery (5–8 источников) → content analysis → 5-категорийная классификация (Emerging / Established / Disruptive / Challenges / Opportunities) → cross-validation → strategic context → синтез.
- **Deliverables:** структурированный markdown-отчёт со стандартизованным naming convention.
- **Сильные стороны:** самый воспроизводимый pipeline; хорош для регулярных «прогонов» по нишам.
- **Слабые стороны:** меньше про продукт, больше про рынок и тренды.
- **Когда брать:** автоматизированные ежемесячные апдейты по нише.

### A7. alirezarezvani · `content-trend-researcher` SKILL
- **Tools/sources:** Google Trends, Google Analytics, Substack, Medium, Reddit, LinkedIn, X, блоги, подкасты, YouTube.
- **Методология:** intent classification (informational / commercial / transactional / navigational / problem-solving), engagement-сигналы, rising queries, viral discussions, viewing metrics → content gaps с difficulty rating.
- **Deliverables:** opportunity scores, intent breakdown, content gaps + 1–5 SEO-оптимизированных аутлайнов с keywords и multimedia.
- **Сильные стороны:** **лучший инструмент именно под Chrome-расширения и инфо-продукты** — прямо ищет underserved-темы с высокой demand.
- **Слабые стороны:** контент-фокус, не валидирует SaaS-механику.
- **Когда брать:** охота за нишами расширений и контентных приложений.

---

## B. End-to-end пакеты (несколько skills/agents)

### B1. ferdinandobons · `startup-skill` (4 skills)
| Skill | Назначение |
|---|---|
| `startup-design` | Стратегия: research → конкуренты → бренд → product def → финансы → эксперименты валидации |
| `startup-competitors` | Battle cards, pricing landscape, feature matrix |
| `startup-positioning` | **April Dunford framework** + competitive mapping |
| `startup-pitch` | Питчи 10 / 5 / 2 мин + elevator + email + Q&A |
- **License:** MIT. **Целевой пользователь:** founder, ищущий «$10k strategy consultant без денег».
- **Сильные стороны:** позиционирование по Dunford — редкость; готовый pitch-deliverable.
- **Слабые стороны:** именно discovery нишы вшит лишь внутри `startup-design`; нет atomic trend-агента.

### B2. bwerneckm · `startup-skills` (13 skills)
1. Idea Validation · 2. Business Model Design · 3. Competitive Intelligence · 4. Market Entry & Expansion · 5. Product Strategy · 6. Growth & Analytics · 7. Go-to-Market · 8. Sales & Partnerships · 9. Fundraising · 10. Financial Modeling · 11. Marketing & Brand · 12. Regulatory & Compliance · 13. Strategic Planning.
- **Фреймворки:** 60+, в т.ч. Lean Canvas, Wardley Mapping, **7 Powers**, Shape Up, AARRR, MEDDIC, OKR.
- **Целевой пользователь:** pre-seed → Series A.
- **Сильные стороны:** покрытие. Wardley Mapping и 7 Powers — большая редкость в готовых пакетах.
- **Слабые стороны:** нет trend / niche discovery как отдельного skill — стартует уже с готовой идеи.

### B3. rsmdt · `the-startup`
- **Slash-команды:** `/constitution /specify /validate /implement /test /review /document /analyze /refactor /debug`.
- **Auto-skills:** specify-requirements / specify-solution / specify-factory.
- **Roles:** Chief, Analyst, Architect, SWE, QA, Designer, Platform, Meta.
- **Сильные стороны:** spec-driven development → отлично, чтобы превратить найденную нишу в производственный код. Параллельное исполнение + quality gates.
- **Слабые стороны:** **не про discovery** — про execution. Нужен в паре с trend/idea-агентами.

### B4. slgoodrich · `agents` (8 PM-агентов)
1. product-manager (роутер) · 2. **market-analyst** · 3. research-ops · 4. product-strategist · 5. roadmap-builder · 6. feature-prioritizer (RICE/ICE) · 7. requirements-engineer · 8. launch-planner.
- **16 фреймворков:** Continuous Discovery, Just Enough Research, Empowered, PMF, Positioning, Story Mapping, Shape Up, HEART, RICE, Lean Product Playbook, **Kano**, Lean Startup, ICE, Value/Effort, SWOT, Porter.
- **Целевой пользователь:** соло-разработчики, indie-hackers, малые команды.
- **Сильные стороны:** маршрутизатор `product-manager` — встроенный диспетчер; Kano — редкость.
- **Слабые стороны:** нет trend и idea-validation как самостоятельных агентов.

### B5. phuryn · `pm-skills` (≈60 skills, 5 категорий)
- **Discovery (13)** — brainstorming, OST, assumption mapping, interview scripts.
- **Strategy (12)** — **Lean Canvas, BMC, PESTLE, Porter, Ansoff**.
- **Execution (15)** — PRD, OKR, roadmap, retro, pre-mortem.
- **GTM & Growth (11)** — beachhead, ICP, battlecards, growth loops, North Star.
- **Research & Analytics (10)** — personas, journey, **TAM/SAM/SOM**, cohort, A/B.
- **Сильные стороны:** самый широкий PM-набор; есть Discovery как отдельная категория.
- **Слабые стороны:** **нет dedicated trend / niche discovery skill** — discovery в их понимании = customer interviews и assumption testing.

### B6. talknerdytome-labs · `claude-agents` (3 growth-агента)
1. Website Intelligence Agent — конкурентный сайт-аудит (messaging, ICP, pricing).
2. Meta Ads Library Agent — анализ конкурентов через Facebook Ads Library API.
3. Google Ads Library Agent — то же через Google Ads Transparency.
- **Сильные стороны:** **уникальная фишка** — реальные ad-libraries, чего нет ни у кого. Точная оценка «есть ли уже платный спрос в нише».
- **Слабые стороны:** очень узкий набор — сам по себе нишу не нашёл бы, но валидирует «горит ли deck» у конкурентов.

### B7. wshobson · `agents` (16 оркестраторов)
- Full-Stack Feature, Agent Teams (7 пресетов: review/debug/feature/fullstack/**research**/security/migration), Conductor (Context → Spec & Plan → Implement).
- **Сильные стороны:** именно про оркестрацию параллельных команд; есть готовый «research team».
- **Слабые стороны:** уклон в инжиниринг, бизнес-агенты слабее.

### B8. zhsama · `claude-sub-agent` (spec-driven)
- 3 фазы строго последовательно: **Planning** (spec-analyst → spec-architect → spec-planner, gate 95%) → **Development** (spec-developer → spec-tester, gate 80%) → **Validation** (spec-reviewer → spec-validator, gate 85%).
- **Сильные стороны:** quality gates и feedback-loops; идеально для перевода найденной ниши в spec → код.
- **Слабые стороны:** discovery вообще нет; начинается с готовых требований.

---

## C. Сравнительные матрицы

### C1. Покрытие задач (атомарные агенты)

| Задача \ Агент | VoltAgent market | VoltAgent trend | VoltAgent comp | VoltAgent validator | rohitg00 market | NioPD market | content-trend |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Поиск ранних трендов | – | ✅ | – | – | – | ◐ | ✅ |
| Поиск контент-ниш | – | – | – | – | – | – | ✅✅ |
| Sizing рынка (TAM/SAM/SOM) | ◐ | – | – | – | ✅✅ | ◐ | – |
| Конкурентный анализ | ◐ | – | ✅✅ | ◐ | ◐ | ◐ | – |
| Валидация идеи | – | – | – | ✅✅ | – | – | – |
| Статистическая дисциплина | – | – | – | – | ✅✅ | ◐ | – |
| Реальные ad-сигналы | – | – | – | – | – | – | – |
| Интент-классификация | – | – | – | – | – | – | ✅✅ |

(✅✅ — флагман, ✅ — есть, ◐ — частично, «–» — нет.)

### C2. Tools / источники

| Агент | Web | Pisanie файлов | Bash | Особое |
|---|:-:|:-:|:-:|---|
| VoltAgent market | WebFetch+WebSearch | – | – | Read-only ресёрч |
| VoltAgent trend | WebFetch+WebSearch | – | – | + патенты, academic |
| VoltAgent competitive | WebFetch+WebSearch | – | – | Porter явно |
| VoltAgent validator | WebFetch+WebSearch | **Write+Edit** | – | Сохраняет teardowns |
| rohitg00 market | – | Write+Edit | ✅ | Локальный data-pipeline |
| NioPD market | WebFetch+WebSearch | – | ✅ | 8-шаговый процесс |
| content-trend | (через web) | – | – | 10+ платформ интент-сигналов |
| talknerdytome (3 агента) | API Facebook/Google Ads | – | – | Уникальные ad APIs |

### C3. Пакеты — что покрывают и где дыры

| Пакет | Discovery ниши | Validation | Strategy/PM | Execution → Code | Pitch/Fundraise |
|---|:-:|:-:|:-:|:-:|:-:|
| ferdinandobons (4) | ◐ (внутри design) | ✅ | ✅ (Dunford) | – | ✅✅ |
| bwerneckm (13) | – | ✅✅ | ✅✅ (60+ frameworks) | – | ✅ |
| rsmdt the-startup | – | ◐ | ◐ | ✅✅ (spec-driven) | – |
| slgoodrich (8 PM) | ◐ (research-ops) | ◐ | ✅✅ | – | ◐ |
| phuryn pm-skills (60+) | ✅ (Discovery cat) | ✅ | ✅✅ | – | – |
| talknerdytome (3) | – (узкий validator) | ◐ (через ads) | – | – | – |
| wshobson agents | – | – | ◐ | ✅✅ (16 orchestrators) | – |
| zhsama sub-agent | – | – | – | ✅✅ (3 phase + gates) | – |

---

## D. Где каждый уникален (не дублируется)

- **VoltAgent trend-analyst** — единственный с патентами + academic.
- **VoltAgent project-idea-validator** — единственный с явным 8-мерным go/no-go scorecard и pivot-режимом.
- **rohitg00 market-researcher** — единственный с **формальной статистической дисциплиной** (CI 95%, top-down/bottom-up convergence ≤30%).
- **NioPD market-researcher** — единственный с **жёстким воспроизводимым 8-шаговым pipeline** под повторяющиеся запуски.
- **content-trend-researcher** — единственный покрывающий **Substack / Medium / Reddit / X / YouTube intent-signals** для контент-ниш.
- **talknerdytome ad-агенты** — единственные, кто читает Facebook/Google **Ads Libraries** (доказательство платного спроса).
- **ferdinandobons startup-positioning** — единственный с **April Dunford** в коробке.
- **bwerneckm startup-skills** — единственный с **Wardley Mapping + 7 Powers**.
- **slgoodrich** — единственный с **Kano model** и встроенным product-manager-роутером.
- **phuryn pm-skills** — самая широкая Discovery-категория (13 skills).
- **rsmdt the-startup / zhsama / wshobson** — единственные, кто доводит идею до production-кода с quality gates.

---

## E. Перекрытие (дублирование)

- **Маркет-ресёрч:** VoltAgent market ⊂ rohitg00 market ⊂ NioPD market по строгости. Брать **NioPD** для регулярных ранов и **rohitg00** когда нужны цифры для инвесторов; VoltAgent — fallback.
- **Конкурентный анализ:** VoltAgent competitive ≈ ferdinandobons startup-competitors ≈ bwerneckm Competitive Intelligence. Лучший по фреймворкам — **bwerneckm** (7 Powers + Wardley); по deliverables (battle cards) — **ferdinandobons**; по чистоте Porter — **VoltAgent**.
- **Валидация:** VoltAgent project-idea-validator (8 dim, brutal) vs bwerneckm Idea Validation (PMF + interviews) vs slgoodrich research-ops (RICE/ICE). Они **не взаимозаменяемы** — VoltAgent даёт go/no-go, bwerneckm готовит interview-скрипты, slgoodrich скорит. Идеально — связка всех трёх.
- **PM-агрегатор:** slgoodrich product-manager ≈ bwerneckm Strategic Planning ≈ phuryn skills как набор. Если нужен **роутер** — slgoodrich; **глубина** — phuryn; **готовые workflow** — bwerneckm.

---

## F. Итоговые рекомендации по сборке

### F1. Минимальный «niche hunter» (для расширений и инфо-продуктов)
1. `trend-analyst` (VoltAgent) — слабые сигналы.
2. `content-trend-researcher` (alirezarezvani) — underserved-темы.
3. `Website Intelligence Agent` + `Meta Ads Library Agent` (talknerdytome) — есть ли платный спрос.
4. `project-idea-validator` (VoltAgent) — go/no-go.

### F2. Полный «founder kit» (от ниши до питча)
1. **Discovery:** trend-analyst + content-trend-researcher + ad-libraries.
2. **Sizing:** rohitg00 market-researcher (статистика) ИЛИ NioPD (трендовый отчёт).
3. **Конкуренты:** bwerneckm Competitive Intelligence (7 Powers) + ferdinandobons startup-competitors (battle cards).
4. **Validation:** VoltAgent project-idea-validator (фильтр) + bwerneckm Idea Validation (interviews).
5. **Strategy/Positioning:** ferdinandobons startup-positioning (Dunford).
6. **Pitch:** ferdinandobons startup-pitch.
7. **Execution → Code:** zhsama claude-sub-agent ИЛИ wshobson Conductor.

### F3. Самое экономичное по числу зависимостей
Один пакет **bwerneckm/startup-skills** (13 skills) покрывает ~70% потребностей, плюс точечно докинуть `trend-analyst` + `content-trend-researcher` + `talknerdytome ad-libraries` — закрывают разрыв в discovery.

---

## G. Один взгляд

> Для задачи «искать прибыльные ниши и формировать идеи приложений/расширений» **ни один пакет не самодостаточен**. Discovery + платный-спрос-сигнал + статистическая дисциплина закрываются только сборкой из трёх разных репозиториев (VoltAgent + alirezarezvani + talknerdytome). Поверх него — любой execution-pipeline (zhsama/wshobson) для перевода в код.
