# Changelog

## [0.6.15] - 2026-07-08

### Chores
- chore(ci): bump actions/checkout from 6 to 7 (bafbae1)
- chore(deps): bump pydantic-settings in the uv group across 1 directory (8b3a5b7)


## [0.6.14] - 2026-06-17

### Bug Fixes
- fix: sync server.json and gemini-extension.json versions, auto-bump on release (#60) (b45d6a0)

### Chores
- chore(deps): bump starlette from 0.52.1 to 1.3.1 (#56) (f260bdc)
- chore(deps): bump fastmcp from 3.0.1 to 3.2.0 (#45) (3d428fa)
- chore(deps): bump python-multipart from 0.0.22 to 0.0.31 (#59) (7f4f2df)
- chore(deps): bump cryptography from 46.0.5 to 48.0.1 (#57) (02e1cec)
- chore(deps): bump authlib from 1.6.8 to 1.6.12 (#53) (eee7601)
- chore(deps): bump python-dotenv from 1.2.1 to 1.2.2 (#51) (d7916da)
- chore(deps): bump idna from 3.11 to 3.15 (#54) (2067864)
- chore(deps): bump pygments from 2.19.2 to 2.20.0 (#44) (ff9f937)
- chore(deps-dev): bump pytest from 9.0.2 to 9.0.3 (#48) (8ba0c1c)
- chore(deps): bump pyjwt from 2.11.0 to 2.13.0 (e373ac0)
- chore(ci): bump softprops/action-gh-release from 2 to 3 (36963db)


## [0.6.13] - 2026-03-05

### Documentation
- docs: update tool count 23→26, add Jira Versions category (#40) (e7862a4)


## [0.6.12] - 2026-03-05

### Features
- feat: add Jira version CRUD tools using REST API v2 (#39) (d9692be)


## [0.6.11] - 2026-03-03

### Features
- feat: add startup logging with package version and config summary (#38) (adc04be)


## [0.6.10] - 2026-02-27

### Bug Fixes
- fix: shorten server.json description to <=100 chars for MCP Registry (#37) (4e11346)


## [0.6.9] - 2026-02-27

### Bug Fixes
- fix: correct broken MCP Registry URLs (#36) (5c3d6d5)


## [0.6.8] - 2026-02-27

### Chores
- chore: improve SEO and discoverability (#35) (f912e9f)


## [0.6.7] - 2026-02-27

### Bug Fixes
- fix: harden resource/prompt loading and add URL support (#33) (0e46b4f)


## [0.6.6] - 2026-02-27

### Features
- feat: add MCP Registry auto-publish on release (9ad379e)


## [0.6.5] - 2026-02-25

### Bug Fixes
- fix: update installation gateway URLs to SPA route (#32) (d248771)


## [0.6.4] - 2026-02-25

### Chores
- chore(ci): bump astral-sh/setup-uv from 5 to 7 (#31) (6e64faf)
- chore(ci): bump actions/checkout from 4 to 6 (#30) (3eaa07a)
- chore: add Dependabot for Python deps and GitHub Actions (#29) (9a360a4)


## [0.6.3] - 2026-02-24

### Features
- feat: add Gemini CLI extension manifest and context (#28) (cc75241)


## [0.6.2] - 2026-02-24

### Documentation
- docs: sync README structure across MCP repos (#27) (0b66cf0)

### Other


## [0.6.1] - 2026-02-24

### Bug Fixes
- fix: disable FastMCP startup banner (#26) (8d433b7)


## [0.6.0] - 2026-02-24

### Features
- feat(#24): add 5 MCP prompts for multi-tool workflows (#25) (735f846)


## [0.5.0] - 2026-02-24


## [0.4.0] - 2026-02-24

### Features
- feat(#20): MCP builder compliance — immediate fixes (#22) (cfbdaa0)

### Documentation
- docs: update AGENTS.md — add release workflow, fix stale info (4afdab3)

### Other


## [0.3.0] - 2026-02-23

### Other


## [0.2.1] - 2026-02-23

### Bug Fixes
- fix(ci): use temp files for blob creation to avoid ARG_MAX (#18) (606a858)
- fix(ci): include uv.lock and CHANGELOG.md in release commits (#17) (8be8ffb)

