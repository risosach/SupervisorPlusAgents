# Claude Modes Cheat Sheet (Cursor)

Claude in Cursor can operate in different **modes**, optimized for specific workflows.  
Use this cheat sheet to switch modes depending on your task.

---

## 🎛️ Claude Modes Overview

| Mode       | Purpose                                                             | Best For…                                   | Shortcut              |
|------------|---------------------------------------------------------------------|----------------------------------------------|------------------------|
| **Develop** (default) | Code completion, test-driven development, bug fixing              | ✅ Writing code, fixing tests, codegen         | `Cmd+J` / `Ctrl+J`     |
| **Explain**          | Describe code, debug errors, interpret tracebacks                | 🧠 Understanding logic, failures, design       | `Cmd+Shift+E` / `Ctrl+Shift+E` |
| **Plan**             | Outline features, architecture, generate structured roadmaps     | 🧭 Designing tools, workflows, implementation  | `Cmd+Shift+P` / `Ctrl+Shift+P` |

---

## 🛠️ How Modes Affect Claude

- Each mode changes Claude's **tone and behavior**:
  - **Develop** = productive and code-focused
  - **Explain** = descriptive and teaching-oriented
  - **Plan** = strategic and structured

- Mode affects **Claude Sidebar Panel**, not the `cc>` terminal.
- You can **switch modes before asking** your next question in the sidebar.

---

## 📍 When to Use Each Mode

| Use Case                                    | Mode      |
|---------------------------------------------|-----------|
| Write Python to pass tests                  | Develop   |
| Understand what a method/class is doing     | Explain   |
| Plan out a new tool or LangGraph structure  | Plan      |
| Refactor existing logic                     | Develop   |
| Debug a traceback from pytest               | Explain   |
| Draft multi-step implementation strategy    | Plan      |

---

## 💡 Claude Code (`cc>` Terminal)

- The Claude terminal (started with `claude`) is always in **Develop** mode.
- Ideal for TDD, test-writing, implementation, and iterative fixes.

---

## 🗂️ Reference

Keep this file in `docs/claude_modes_cheatsheet.md` for quick reference in all phases of development.
