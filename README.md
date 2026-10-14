# AI skills

My personal collection of skills for Claude and ChatGPT, starting with local testing in Claude Code and Codex. This is a working repository for collecting, adapting, and refining instructions I use regularly. Publishing comes later.

Some skills are original, while others begin as direct copies or adaptations of existing work. Sources of inspiration include [Matt Pocock](https://github.com/mattpocock), [Cursor's pstack](https://github.com/cursor/plugins/blob/main/pstack/README.md), and [skills.sh](https://www.skills.sh/). Keep source attribution and any upstream license notices alongside copied or adapted skills.

## Organization

Skills start in three buckets. More can be added as the collection grows.

| Bucket | Purpose |
| --- | --- |
| `engineering` | Building, reviewing, testing, and maintaining software. |
| `productivity` | Writing, planning, and everyday workflows. |
| `security` | Security reviews, hardening, and related workflows. |

Each skill lives in its own directory with a `SKILL.md` entry point and any supporting files it needs.

```text
skills/
├── engineering/
├── productivity/
│   └── unslop/
│       └── SKILL.md
└── security/
scripts/
├── link-skills.sh
├── list-skills.sh
└── unlink-skills.sh
```

Skill directory names must be unique across all buckets. The linking script uses the directory name, without the bucket prefix, as the installed name.

## Test locally

Use Bash and a local checkout. From the repository root, run:

```bash
bash scripts/link-skills.sh
```

The script finds every `SKILL.md` under `skills/` and symlinks its containing directory into both destinations:

| Destination | Local harness |
| --- | --- |
| `~/.claude/skills/<skill-name>` | Claude Code |
| `~/.agents/skills/<skill-name>` | Codex and other compatible agent harnesses |

**Check for name collisions before running it.** The script replaces existing entries with matching names, including deleting real files or directories at those paths. Move any local skill you want to preserve out of the way first.

This is a development helper, not a publishing or supported installation workflow. It links files on your machine; it does not upload skills to a hosted chat service.

To try the existing `unslop` skill:

1. Run the linking command above.
2. Check the links:

   ```bash
   ls -ld ~/.claude/skills/unslop ~/.agents/skills/unslop
   ```

3. Start a fresh session in your local agent and explicitly invoke `unslop` with a short piece of writing to edit.
4. Review the result, edit `skills/productivity/unslop/SKILL.md`, and try again in a fresh session.

The links point directly into this checkout, so edits and pulled updates are available without copying files again. Rerun the script after adding a skill. After renaming or removing skills, run the unlink script below, then rerun the linking script to refresh the installed set. Unlink before moving the checkout, then link again from its new location.

## Unlink local skills

From the repository root, run:

```bash
bash scripts/unlink-skills.sh
```

This removes symlinks created for this checkout from both `~/.claude/skills` and `~/.agents/skills`, including broken links left by renamed or deleted skills. Source files, real files and directories in the destinations, and links to other repositories are preserved. It is safe to rerun when nothing is linked.

The script matches the absolute link targets written by `link-skills.sh`. It skips symlinked destination directories and reports them for manual review. It cannot restore entries that the linking script previously replaced.

## Add a skill

1. Create `skills/<bucket>/<skill-name>/SKILL.md` with a name, description, and instructions for the agent.
2. Keep supporting scripts, references, and assets in that skill's directory.
3. Record the source when copying or adapting existing work.
4. Run `bash scripts/link-skills.sh` and test the skill on a representative task before treating it as ready to publish.
