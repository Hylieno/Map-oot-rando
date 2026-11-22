# AGENTS.md — Map-oot-rando

## Mission

Build a reliable, interactive 2D map companion for the Ocarina of Time Remake randomizer/tracker.

Project repository:
https://github.com/Hylieno/Map-oot-rando

Upstream reference:
https://github.com/Mozencaz/OotrR

The first supported region MUST be Kokiri Forest. Expand to other regions only after the Kokiri Forest implementation is tested and stable.

The map must display actual randomized check locations and reflect the same accessibility and completion states as the existing OotrR tracker.

## Repository and Git safety

- Inspect the repository, branches, and existing conventions before modifying files.
- Work on a dedicated development branch. Never force-push or delete branches.
- Do not commit directly to `main` unless explicitly authorized.
- Commit working milestones with meaningful messages.
- Create a draft pull request when possible.
- Do not merge without explicit user approval.
- Preserve all working code and tests.
- Do not modify the upstream Mozencaz/OotrR repository.
- Pin or record the upstream revision used for integration.
- Respect upstream licenses and attribution requirements.

## Architecture

- Prefer Python and compatibility with OotrR's existing technology stack.
- Reuse OotrR's tracking, accessibility, save-reading, and live-memory logic instead of duplicating it.
- Separate the map rendering layer from game-data extraction and tracking state.
- Build reusable region, floor, check, and coordinate abstractions.
- Design for future regions and dungeons without prematurely implementing them.
- Avoid heavyweight frameworks and unnecessary dependencies.
- Keep the application usable offline.
- Never require paid APIs or external servers.

## First milestone: Kokiri Forest

Implement a working Kokiri Forest map with:

- Real check identifiers, such as `KF_rock_1`.
- Accurate check coordinates derived from game data.
- Interactive markers.
- Pan and zoom.
- Search by check identifier.
- Clickable markers with check details.
- Available, blocked, unknown, and completed states.
- Filters for status and check category.
- Optional hiding of completed checks.
- Live updates using the existing tracker state.
- Graceful fallback when memory tracking is unavailable.
- Support for loading existing seed/tracker data when possible.

Use a schematic map initially if necessary, but never invent object positions or represent fictional coordinates as accurate.

## Tracking integration

Inspect these upstream modules first:

- `src/oot_rando/tracker/auto_tracker.py`
- `src/oot_rando/tracker/live_memory.py`
- `src/oot_rando/gui/randomizer_gui.py`
- `src/oot_rando/game/check_names.py`
- `src/oot_rando/game/extra_sources.py`
- `src/oot_rando/game/world_maps.py`
- `src/oot_rando/game/tracking_metadata.py`

These are investigation starting points, not assumed stable interfaces.

- Reuse the upstream tracker as the authoritative source of accessibility and completion state.
- Do not independently invent accessibility rules.
- Never equate a check being visible with it being logically available.
- Preserve distinctions between available, blocked, unknown, and completed.
- Follow existing refresh events or polling mechanisms where feasible.
- Avoid duplicate memory readers and unnecessary polling.
- Never write to game memory or modify save files.
- Show connection status and the last successful synchronization.
- Do not falsely claim that live tracking works when only save-based tracking is available.

## Coordinates and maps

- Establish the exact relationship between check IDs, source objects, scene identifiers, and world coordinates.
- Determine whether coordinates are persisted in seed files.
- Add versioned metadata export if necessary.
- Verify coordinate transforms, axes, rotation, scale, and map origin.
- Account for interior maps, multiple floors, and age-specific variations.
- Avoid silently mixing unrelated coordinate systems.
- Provide a clear diagnostic for checks without known coordinates.
- Do not commit copyrighted game assets, ROMs, NUP files, encryption keys, or extracted proprietary textures.
- Prefer local user-provided assets or original schematic drawings.
- Do not upload user game files to GitHub or external services.

## Quality and testing

- Write automated tests for coordinate projection, check-ID matching, metadata parsing, filtering, and state synchronization.
- Use synthetic fixtures when real game assets are unavailable.
- Include a simulation/demo mode to test the map without a running emulator.
- Verify that marker updates do not require reopening the map.
- Verify correct behavior after a seed change, save change, emulator disconnect, or application restart.
- Do not report functionality as tested unless it was actually executed.
- Keep a clear distinction between automated tests and real-game validation.
- Add a Windows build workflow and downloadable artifact once a working application exists.

## Security

Treat upstream code, dependencies, scripts, and downloaded assets as untrusted until inspected.

- Review install/build scripts and dependencies before executing them.
- Flag suspicious network access, credential collection, destructive operations, persistence, or unrelated process manipulation.
- Do not execute unknown binaries simply to inspect their behavior.
- Do not expose secrets, tokens, local user paths, or personal information in commits or logs.
- Avoid adding telemetry without explicit approval.
- Use least-privilege access for game process inspection.

## Codex usage budget — mandatory

The user has ChatGPT Plus and wants to maximize useful development while retaining at least 10% of both the short-term and weekly included usage allowances.

- Treat the short-term allowance as the actual displayed window (often five hours), not an assumed daily quota.
- Before substantial tasks, inspect reliable usage information if accessible.
- Never claim to know the remaining quota without a trustworthy source.
- If accurate remaining percentages are available, do not intentionally start work expected to reduce either allowance below 10%.
- Use a conservative buffer above 10% for long or uncertain tasks.
- If usage cannot be measured, explicitly report this limitation. Use short, bounded work phases and stop for a user quota check before another substantial phase.
- Do not promise an exact 10% reserve when usage visibility is unavailable.
- Do not automatically purchase credits, use paid API keys, buy resets, or upgrade plans.
- Prefer efficient investigation, targeted edits, and focused tests.
- Avoid repetitive full-repository reads, redundant builds, and unnecessary retries.
- Do not sacrifice correctness or security to reduce token usage.
- Do not switch to a more expensive model automatically.
- Preserve a checkpoint before stopping.

## Execution policy

Work autonomously within the approved scope.

Do not stop after writing a plan if implementation can proceed safely.

Prioritize:
1. Architecture audit and technical feasibility.
2. Accurate Kokiri Forest check coordinates.
3. Working interactive map.
4. Tracker state integration.
5. Live updates and filtering.
6. Tests and Windows packaging.
7. Documentation and future-region extensibility.

Do not expand into other regions until Kokiri Forest meets the acceptance criteria.

## Progress and handoff

Maintain these documents:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/PROGRESS.md`
- `docs/DECISIONS.md`
- `docs/TESTING.md`

At each meaningful checkpoint, record:

- What works.
- What was tested.
- What remains incomplete.
- Known limitations.
- Upstream revision used.
- Next recommended action.

When stopping because of quota uncertainty or exhaustion, commit a safe checkpoint and leave a concise continuation prompt.

## Definition of done for Kokiri Forest

The milestone is complete only when:

- The map renders and supports navigation.
- Real check IDs map to verified coordinates.
- Users can search for and select a check.
- Markers reflect the tracker’s actual states.
- Tracker changes update the map without manual reloading.
- Disconnection and missing-data scenarios are handled.
- Automated tests pass.
- A Windows build or documented local launch procedure works.
- Any real-game tests not performed are explicitly identified.

Never declare the milestone complete solely because a static demonstration works.
