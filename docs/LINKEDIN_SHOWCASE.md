# RepoLens LinkedIn Launch & Showcase Kit

This kit contains copy-paste ready LinkedIn posts, video demo talking points, and carousel slide blueprints to launch **RepoLens** to the developer community.

---

## 🚀 Post Option 1: The Engineer Story (High Engagement / Narrative)

> **Headline:** I got tired of outdated architecture diagrams in Confluence. So I built an open-source tool that maps codebases automatically in seconds.
>
> ---
>
> Ever joined a new engineering team or inherited a legacy repository and asked:
> *"Where does the data flow? Which modules depend on what? Why is this service coupled to billing?"*
>
> The typical answer:
> 1. Check the Confluence architecture diagram (last updated 18 months ago).
> 2. Trace dozens of imports manually.
> 3. Hope you don’t accidentally create a circular dependency.
>
> To solve this once and for all, I built **RepoLens**: an interactive, static-analysis-first architecture visualizer and linter for Python, TypeScript, and JavaScript codebases.
>
> 💡 **What makes it different:**
>
> 🔒 **100% Zero-Runtime Execution:** RepoLens never runs target code, imports untrusted modules, or installs dependencies. It analyzes code purely via AST and masked lexical parsing. Safe for private and enterprise codebases.
>
> 🌐 **Interactive React Flow Explorer:** Run `repolens .` and instantly get an interactive architecture map in your browser with semantic zoom, 1-hop/2-hop neighborhood focus, and breadcrumb drill-downs.
>
> ⚡ **Framework Intelligence:** Statically extracts FastAPI routes, HTTP methods, route handlers, and SQLAlchemy/SQLModel database entities without running any server.
>
> 🛡️ **CI Architectural Linter (`repolens check`):** Enforces clean layer boundaries (e.g. `domain` can never import `api`) and fails pull requests that introduce circular dependencies.
>
> 📊 **Multi-Format Exporters (`repolens export`):** Exports clean diagrams to Mermaid, PlantUML, Graphviz DOT, or a self-contained offline HTML report with zero external CDN dependencies.
>
> 🔄 **CI Architecture Diff (`repolens diff`):** Compares architecture states across commits to catch dropped public API routes or unexpected coupling spikes before merging.
>
> 🤖 **Bounded AI Insights (`repolens explain`):** Deterministic local rule engine by default (0 API keys needed), with optional OpenAI-compatible bounded context that never uploads entire codebases.
>
> The project is fully open source under the MIT license!
>
> ⭐️ **GitHub Repo:** https://github.com/ompatelz/RepoLenz
>
> Try it on your own codebase:
> ```bash
> git clone https://github.com/ompatelz/RepoLenz.git
> pip install -e ".[dev]"
> repolens .
> ```
>
> Would love your feedback and stars on GitHub! What architectural pain points do you face most often in large codebases?
>
> #OpenSource #SoftwareArchitecture #Python #TypeScript #DevTools #ReactJS #FastAPI #SystemDesign #SoftwareEngineering

---

## 🎥 Post Option 2: Short & Punchy (Best paired with a 30s screen recording)

> **Headline:** Turn any codebase into an interactive architecture map in one command.
>
> ---
>
> One command:
> `repolens .`
>
> Instant result:
> A living, interactive architecture map of your entire Python / TypeScript codebase in your browser.
>
> Features under the hood:
> • Pure static analysis (Zero runtime execution, zero cloud upload)
> • Semantic zoom from package down to function
> • FastAPI route & SQLAlchemy model detection
> • CI architectural boundaries linter (`repolens check`)
> • One-click Mermaid & PlantUML exports
> • Pull request architecture regression diffing (`repolens diff`)
>
> Built with Python 3.12, FastAPI, NetworkX, and React 19 / React Flow.
>
> 100% Free & Open Source (MIT):
> 👉 https://github.com/ompatelz/RepoLenz
>
> Drop a ⭐️ on GitHub if you find this useful!
>
> #DeveloperTools #SoftwareEngineering #Python #React #OpenSource #CodeQuality

---

## 📑 Carousel Slide Deck Blueprint (PDF Presentation)

Use Canva or Keynote/Figma to export these 7 slides as a PDF carousel for LinkedIn's document viewer:

- **Slide 1 (Hook):**
  - *Title:* "How to map any codebase in 5 seconds."
  - *Subtitle:* "No outdated Confluence diagrams. No runtime tracing. 100% open source."
  - *Visual:* RepoLens dark-mode logo + terminal prompt: `repolens .`

- **Slide 2 (The Problem):**
  - *Title:* "The Architecture Drift Trap"
  - *Points:*
    - Diagrams get stale the day after they're drawn.
    - Accidental circular dependencies sneak into PRs.
    - Onboarding new engineers takes weeks of manual import tracing.

- **Slide 3 (The Solution):**
  - *Title:* "Static-Analysis-First Architecture"
  - *Points:*
    - Pure AST & lexical parsing (Python, JavaScript, TypeScript).
    - Zero execution: safe for proprietary and untrusted code.
    - Zero cloud leakage: 100% local-first.

- **Slide 4 (Interactive Web Canvas):**
  - *Title:* "Explore Your Code at Any Scale"
  - *Points:*
    - High-level package overview down to granular functions.
    - 1-hop and 2-hop neighborhood isolation.
    - Automatic FastAPI routes and SQLModel table mapping.

- **Slide 5 (Automated CI Guardrails):**
  - *Title:* "Prevent Architectural Rot in CI"
  - *Command:* `repolens check ./src --strict`
  - *Benefit:* Enforce layer boundaries (e.g. `domain` must never depend on `api`) and block circular imports before merge.

- **Slide 6 (Export & Diff):**
  - *Title:* "From Terminal to PR Comments"
  - *Points:*
    - Export to Mermaid (`.mmd`), PlantUML (`.puml`), or standalone offline HTML.
    - `repolens diff`: Catch breaking route changes and introduced cycles across PR branches.

- **Slide 7 (Call to Action):**
  - *Title:* "Try RepoLens Today"
  - *Points:*
    - Open source under MIT License.
    - `git clone https://github.com/ompatelz/RepoLenz.git`
    - Star the project on GitHub: `github.com/ompatelz/RepoLenz`

---

## 📸 Media Asset Recommendations

1. **GIF / Video Clip (30-45 seconds):**
   - Start in terminal: type `repolens .`
   - Browser opens showing dark-mode React Flow canvas with nodes and edges.
   - Click a node: inspector panel reveals source line, routes, and relationships.
   - Click "1-hop" focus mode: graph animates to isolate direct neighbors.
   - Click "Explain node": instant architectural synthesis appears.
2. **Static Screenshot (PR comment):**
   - Screenshot showing `repolens check` failing on a layer boundary violation in a GitHub Action.
