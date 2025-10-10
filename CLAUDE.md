
## MCP server
- Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.


## DEBUGGING
- When an error persist after several tries, step back and try a different approach widening the point of view.


## PLANNING 
- Break down complex tasks into smaller ones. Focus on general planning first, with coherent steps and don't enter too much detail at first, once the user starts executing each step or phase, then focus in detailed tasks. The purpose of this is to leverage your potential and avoid loosing track entering in too much detail on too many tasks at once.
- Use TODO.md file ALWAYS as memory of strategy, plan, steps , and update after every change. this file MUST always be up to date.



## CODING BEST PRACTICES
### 1. CLEAN CODE
**Core principles**
- Small, single-purpose functions. One responsibility, one level of abstraction, ≤2 nesting levels.  
- Expressive, intention-revealing names. Consistent vocabulary; no noise words or cryptic abbreviations.  
- No duplication (DRY). Extract, parameterize, or generalize instead of repeating code.  
- Comments only when necessary. Code should explain itself; comment *why*, not *what*.  
- Clean error handling. Use exceptions, never silent catches; provide actionable context.  
- Law of Demeter: “Talk to friends, not strangers.” Don’t expose internals unnecessarily.  
- Always leave the code cleaner than before (Boy Scout Rule).  

**Structure & readability**
- Keep files, classes, and methods short and cohesive (SRP).  
- Public APIs are minimal and clear; hide internal logic.  
- Use consistent formatting and naming conventions.  

**Testing**
- Apply TDD when possible.  
- Tests follow F.I.R.S.T: Fast, Independent, Repeatable, Self-validating, Timely.  
- Test one concept per test; name tests descriptively.  

---

### 2. ARCHITECTURE & DESIGN
- Follow SOLID and separation of concerns; avoid circular dependencies.  
- Prefer composition over inheritance.  
- Keep data flow explicit and predictable.  
- Encapsulate side effects; isolate I/O from logic.  
- Use dependency injection for flexibility and testability.  
- Strive for minimal coupling and maximal cohesion.  

---

### 3. DOCUMENTATION & COMMUNICATION
- Keep README updated with setup, usage, and contribution info.  
- Document public APIs and design decisions (why, not just how).  
- Use clear commit messages and meaningful PR descriptions.  
- Avoid unnecessary verbosity; prefer clarity over completeness.  

---

### 4. TESTING & QUALITY ASSURANCE
- Write automated tests for core logic before or alongside code.  
- Include unit, integration, and regression tests where relevant.  
- Validate edge cases and error paths.  
- Maintain high test coverage, but prefer meaningful tests over numbers.  
- Ensure tests run automatically (CI) and pass consistently.  

---

### 5. PERFORMANCE & EFFICIENCY
- Write clear code first; optimize only proven bottlenecks.  
- Use efficient data structures and algorithms.  
- Avoid unnecessary I/O, allocations, or global state.  
- Profile before optimizing; measure impact of changes.  

---

### 6. SECURITY & RELIABILITY
- Validate and sanitize all inputs.  
- Never expose secrets or credentials.  
- Handle sensitive data securely; follow least privilege principle.  
- Avoid race conditions and shared mutable state.  
- Fail safely — prefer clear, controlled degradation over crashes.  

---

### 7. COLLABORATION & VERSION CONTROL
- Commit frequently with clear, atomic changes.  
- Use feature branches; keep main branch always stable.  
- Write descriptive commit messages (`type(scope): short summary`).  
- Review others’ code with empathy; focus on clarity and correctness.  

---

### 8. OUTPUT EXPECTATIONS (FOR CODE-GENERATING AGENTS)
When generating or refactoring code:
- Output **fully runnable, idiomatic code** following the language’s conventions.  
- Include **clear structure** (modules, classes, functions) with expressive names.  
- Provide **minimal, focused unit tests** that illustrate correct behavior.  
- Avoid unnecessary comments; where added, explain reasoning or trade-offs.  
- Include **docstrings** or short module-level summaries when helpful.  
- Always produce **readable, maintainable code** over cleverness.  
