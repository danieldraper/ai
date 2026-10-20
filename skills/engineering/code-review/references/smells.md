# Smell baseline

A fixed set of code smells from Fowler, *Refactoring* (2nd ed.), chapter 3, used by the standards-and-patterns lens even when the repository documents nothing. Two rules bind it:

- **The repository overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation, and never a Blocker. Skip anything tooling already enforces.

Each entry reads *what it is* → *how to fix*. Match against the diff, and quote the hunk when reporting.

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design is murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk, or the diff re-implements something that already exists elsewhere in the repository (search before assuming it is new). → extract or reuse the shared shape.
- **Long Function / Long Parameter List**: a function that needs scrolling or a comment per paragraph, or more than three or four positional parameters. → extract steps; bundle parameters into a type or use keyword arguments / an options struct.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or parameters keep travelling together. → bundle them into one type and pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept (money, currency, status, identifier). → give the concept its own small type.
- **Repeated Switches**: the same `case`/`switch`/`if` cascade on the same type recurs across the change. → polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, interfaces, or hooks added for needs the spec doesn't have. → delete it; inline until a real need shows.
- **Message Chains**: long `a.b.c.d` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly delegates onward. → cut it, call the real target directly.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.
- **Comments as deodorant**: a comment explaining *what* convoluted code does rather than *why*. → make the code say it; keep comments for intent, constraints, and links.
- **Global Data / Mutable Shared State**: new class-level, package-level, or singleton state that any caller can mutate. → pass it explicitly or encapsulate behind one owner.
