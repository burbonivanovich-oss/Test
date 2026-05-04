# Niche → Idea → Money → Launch Plan kit

Готовая сборка субагентов, skills и оркестратор для автоматического поиска прибыльной ниши, формирования продуктовой идеи, расчёта денег в нише и составления плана запуска приложения / Chrome-расширения.

## Что собрано

```
.claude/
├── agents/
│   ├── trend-analyst.md            # VoltAgent — обнаружение слабых сигналов (тренды, патенты, academic)
│   ├── competitive-analyst.md      # VoltAgent — Porter, SWOT, position maps
│   ├── project-idea-validator.md   # VoltAgent — 8-мерный go/no-go scorecard
│   └── market-researcher.md        # rohitg00 — TAM/SAM/SOM со статистической дисциплиной
├── skills/
│   ├── content-trend-researcher/   # alirezarezvani — intent gaps, 10+ платформ, opportunity score
│   ├── validating-ideas/           # bwerneckm — Lean Canvas + Mom Test + Pretotyping + GO/PIVOT/KILL
│   ├── modeling-finances/          # bwerneckm — revenue model, 13-week cash flow, scenarios
│   ├── launching-go-to-market/     # bwerneckm — Beachhead, Racecar, channel scorecards, PLG
│   ├── planning-market-entry/      # bwerneckm — entry sequence + attractiveness scorecard
│   └── gathering-competitive-intelligence/  # bwerneckm — battle cards
└── commands/
    └── find-and-plan.md            # Slash-команда-оркестратор (5 фаз, 14 шагов)
```

## Как использовать

```
/find-and-plan productivity for SMB
```

или для domain-agnostic discovery:

```
/find-and-plan auto
```

Команда последовательно прогоняет 5 фаз:

1. **Discovery** — `trend-analyst` + `content-trend-researcher` находят 8–12 ниш и ранжируют топ-3.
2. **Idea formulation** — для каждой ниши генерируются 2 концепта (SaaS + расширение); `competitive-analyst` + `project-idea-validator` отбирают одну победительную.
3. **Money** — `validating-ideas` + `market-researcher` (TAM/SAM/SOM) + `modeling-finances` (cash flow) считают рынок и юнит-экономику.
4. **Launch plan** — `planning-market-entry` + `launching-go-to-market` + `gathering-competitive-intelligence` строят 90-дневный план с каналами, бюджетом и battle-cards.
5. **Compile** — финальный отчёт `output/launch-plan-<date>.md`.

## Источники

| Файл | Репозиторий | Лицензия |
|---|---|---|
| `agents/trend-analyst.md`, `competitive-analyst.md`, `project-idea-validator.md` | [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) | см. репо |
| `agents/market-researcher.md` | [rohitg00/awesome-claude-code-toolkit](https://github.com/rohitg00/awesome-claude-code-toolkit) | см. репо |
| `skills/content-trend-researcher/` | [alirezarezvani/claude-code-skill-factory](https://github.com/alirezarezvani/claude-code-skill-factory) (ветка `dev`) | см. репо |
| `skills/validating-ideas/`, `modeling-finances/`, `launching-go-to-market/`, `planning-market-entry/`, `gathering-competitive-intelligence/` | [bwerneckm/startup-skills](https://github.com/bwerneckm/startup-skills) | см. репо |

## Минимальный manual-mode (без slash-команды)

Можно вызывать агентов напрямую в порядке:

1. `> Use the trend-analyst subagent to find 10 niches in <domain>`
2. `> Use the content-trend-researcher skill on those 10 niches`
3. `> Use competitive-analyst on the top 3`
4. `> Use project-idea-validator on each candidate concept`
5. `> Use the validating-ideas skill on the winner`
6. `> Use market-researcher to compute TAM/SAM/SOM`
7. `> Use modeling-finances skill`
8. `> Use planning-market-entry skill`
9. `> Use launching-go-to-market skill`
10. `> Use gathering-competitive-intelligence skill`

См. также:
- `SUBAGENTS_MARKET_RESEARCH.md` — полный каталог найденных альтернатив
- `SUBAGENTS_ANALYSIS.md` — детальное сравнение и матрицы покрытия
