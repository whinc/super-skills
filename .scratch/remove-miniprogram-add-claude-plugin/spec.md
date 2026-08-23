## Problem Statement

仓库当前仍包含微信小程序专用 skills、对应评测 workspace、README 安装说明和项目规则引用，导致仓库定位与实际保留能力不一致。仓库也尚未提供 Claude Code plugin/marketplace manifest，Claude Code 用户无法通过 marketplace 安装并随 Git 提交自动获取更新；现有 Skills CLI 安装说明也未统一遵循仓库约定。

## Solution

移除全部微信小程序相关源 skill、评测 workspace 和文档引用，只保留 `react-effects`、`eli12` 与 `implement-tmux`。在仓库根目录增加 Claude Code plugin 与 marketplace manifest：两者均使用 `super-skills`，marketplace 条目以 `source: "./"` 指向当前仓库，省略 `version` 以使用 Git commit 作为更新判断依据。更新中英文 README，统一提供 Skills CLI、Claude Code 本地 plugin 校验和 Git marketplace 安装方式，并说明 marketplace 必须通过 Git 源或本地目录添加，不能直接添加 `marketplace.json` URL。

## User Stories

1. As a CodeBuddy Code user, I want to install the repository's remaining skills with the documented Skills CLI command, so that my CodeBuddy environment receives the supported skill collection.
2. As a Claude Code user, I want to validate the repository as a plugin, so that I can detect malformed plugin metadata before installation.
3. As a Claude Code user, I want to add the repository as a marketplace from its Git source, so that relative plugin sources resolve correctly.
4. As a Claude Code user, I want to install `super-skills` from the `super-skills` marketplace, so that the remaining skills are available through Claude Code's plugin mechanism.
5. As a Claude Code user, I want marketplace refreshes to observe new Git commits without requiring a manually bumped plugin version, so that installed skills can receive repository updates automatically.
6. As a maintainer, I want the marketplace and plugin to expose the same remaining skills as the Skills CLI source, so that installation mechanisms do not drift in capability.
7. As a maintainer, I want the existing root `skills/` layout to remain the single source of truth, so that Skills CLI discovery and current skill links remain simple and no duplicate skill content is introduced.
8. As a maintainer, I want all WeChat Mini Program skills removed from the source tree, so that users cannot discover or install deprecated capabilities.
9. As a maintainer, I want Mini Program evaluation workspaces removed, so that obsolete benchmark assets do not imply ongoing support.
10. As a maintainer, I want the repository's project rules to stop mentioning Mini Program demo and CI behavior, so that contributor guidance matches the supported scope.
11. As a maintainer, I want English and Chinese README sections to list the same skills, so that users receive consistent documentation regardless of language.
12. As a maintainer, I want English and Chinese README sections to contain equivalent installation commands, so that both language sections remain copyable and correct.
13. As a maintainer, I want the README to link to the official Skills CLI documentation, so that users can find authoritative command details.
14. As a maintainer, I want the README to explain the Git-source restriction for a relative marketplace source, so that users do not attempt an unsupported direct manifest URL installation.
15. As a maintainer, I want non-Mini Program skills and their evaluation assets preserved, so that unrelated functionality is not lost during cleanup.
16. As a maintainer, I want installation-generated copies and obsolete lock metadata absent from the repository, so that generated state cannot diverge from the source skills.
17. As a reviewer, I want repository-wide validation to show no remaining Mini Program references, so that the cleanup boundary is independently observable.
18. As a reviewer, I want plugin validation, Skills CLI discovery, and installation checks recorded as acceptance evidence, so that the new distribution paths are proven rather than only documented.

## Implementation Decisions

- The root `skills/` directory remains the only source directory and continues to contain the three supported skills: `react-effects`, `eli12`, and `implement-tmux`.
- The two Mini Program source skills and both Mini Program evaluation workspaces are removed. The historical Mini Program demo is not recreated or separately removed because it is not present in this repository.
- Existing generated skill copies, symbolic links, and the obsolete skills lock file are not reintroduced. Their prior removal is treated as repository baseline state.
- A Claude Code plugin manifest and a Claude Code marketplace manifest are added under the repository's root plugin metadata directory. The marketplace and plugin both use the kebab-case name `super-skills`.
- The marketplace exposes the repository itself as the plugin source using the relative source `./`. The plugin relies on the default root `skills/` discovery rather than duplicating skills or moving them under another plugin directory.
- Neither manifest sets a `version`. Git commit identity is therefore the update signal for marketplace installations, allowing repository commits to qualify for refreshes.
- The manifest metadata contains only the fields required for valid marketplace/plugin identity plus concise descriptive metadata; no commands, agents, hooks, MCP servers, or other unrelated Claude Code components are added.
- README English and Chinese sections remain structurally equivalent. Both list only the three supported skills and document the same Skills CLI installation, Claude Code plugin validation, marketplace addition, plugin installation, and reload/refresh guidance as applicable.
- Skills CLI documentation continues to reference `https://skills.sh/docs/cli`. The repository-local CodeBuddy installation command is documented as `npx skills add . -a codebuddy --yes`.
- Claude Code marketplace documentation uses the Git-source form for this repository and the installation identifier `super-skills@super-skills`. The README explicitly warns that adding a direct URL to `marketplace.json` cannot resolve a relative `source: "./"`.
- The project rules retain general repository guidance but remove Mini Program-specific evaluation and `miniprogram-ci` instructions.
- The implementation must not alter the behavior or contents of the retained skills, their retained evaluation assets, or the unrelated issue-tracker setup.

## Testing Decisions

- Tests validate externally observable repository behavior and distribution metadata, not the internal wording or arrangement of manifest files.
- The highest-value validation seam is the repository root as consumed by the two distribution CLIs:
  - Run the Skills CLI discovery command against the local repository and confirm exactly the three retained skills are listed.
  - Run `npx skills add . -a codebuddy --yes` and confirm installation completes without Mini Program skills being discovered.
  - Run `claude plugin validate .` and, where supported, strict validation; confirm the output reports a valid plugin or marketplace manifest. Because the installed CLI may return success for some validation failures, validation evidence must include the command output, not only the exit status.
- Validate repository cleanup through external content queries: a case-insensitive repository search for `miniprogram` should return no supported-source, workspace, README, or project-rule references. Historical planning notes may be excluded only if the chosen acceptance command explicitly scopes the search to product/source files; the implementation should prefer removing stale references from all user-facing files.
- Validate README consistency by checking that English and Chinese sections list the same three skills and equivalent installation commands, including the official Skills CLI documentation link and Git marketplace restriction.
- Validate preservation by checking that the retained skill directories and `react-effects-workspace/` remain present and unchanged except for intentional metadata updates, if any.
- Validate the final Git diff and status to ensure all intended deletions/additions are included, no generated installation copies are recreated, and no unrelated files are changed.
- No npm test, lint, or build command is required because the repository has no `package.json` or project test script. CLI validation and repository-content checks are the applicable prior art for this static skills collection.

## Out of Scope

- Adding or changing Claude Code commands, agents, hooks, MCP servers, LSP servers, workflows, themes, or other plugin components.
- Adding a separate marketplace repository or a second plugin directory.
- Moving retained skills out of the root `skills/` directory or maintaining duplicate copies for Claude Code.
- Adding fixed semantic versioning, release automation, tags, CI workflows, or a hosted update service.
- Changing the behavior, prompt content, evaluations, or references of `react-effects`, `eli12`, or `implement-tmux`.
- Removing `react-effects-workspace/` or other non-Mini Program evaluation assets.
- Recreating or importing the external `miniprogram-demo` project.
- Publishing, pushing, or installing the plugin into external user environments as part of the repository change.

## Further Notes

- The local Markdown tracker has no physical triage-label backend. This spec is published at `.scratch/remove-miniprogram-add-claude-plugin/spec.md`; readiness is represented by the completed Wayfinder decisions and the existence of this implementation spec.
- The implementation should use precise path staging because the repository previously contained unrelated generated skill-copy deletions. Do not restore or re-delete unrelated paths while applying this spec.
- Marketplace installation from a Git source is required for `source: "./"` to resolve. A direct URL to the manifest alone is intentionally not a supported installation path for this repository.
- The implementation agent should run the applicable CLI checks after editing and report any environment-specific limitation separately from repository correctness.
