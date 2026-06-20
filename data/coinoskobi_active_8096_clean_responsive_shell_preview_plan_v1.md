# COINOSKOBI_ACTIVE_8096_CLEAN_RESPONSIVE_SHELL_PREVIEW_PLAN_NOAPI

## Decision

Active 8096 will not receive another CSS patch layer. A clean responsive shell preview will be built on a separate port first.

## Target preview

- Port: `8143`
- Next phase: `COINOSKOBI_ACTIVE_8096_CLEAN_RESPONSIVE_SHELL_PREVIEW_8143_NOACTIVE`
- Active write now: `0`
- Preview write now: `0`

## Main visual problems

- `HIGH` — `ACTIVE_PRE_V2_DESKTOP_100_STILL_NOT_ACCEPTABLE`: User screenshot after rollback shows 100 percent desktop still clips hero and leaves excessive vertical gap.
- `HIGH` — `CENTER_HERO_CLIPPED`: Hero/card area is vertically clipped; main medallion and health cards do not fit cleanly.
- `HIGH` — `LARGE_EMPTY_VERTICAL_GAP`: Large empty vertical region remains before system components.
- `HIGH` — `RIGHT_SIDEBAR_SCROLL_OVERFLOW`: Right sidebar creates separate scrollbar/overflow and competes with main content height.
- `CRITICAL` — `PATCH_LAYERING_STOP`: Do not add more active CSS layers; build clean preview shell on a separate port.

## Clean shell requirements

- Desktop: single viewport-safe grid shell
- Desktop: left navigation fixed narrow column
- Desktop: main content owns central width
- Desktop: right sidebar in normal grid column without separate hard scroll
- Desktop: hero is not clipped
- Desktop: system components start immediately after hero with compact gap
- Desktop: no overlapping sections
- Desktop: no full-page hidden overflow trap
- Mobile: right sidebar hidden or converted to top summary cards
- Mobile: left navigation collapsed to compact rail/top menu
- Mobile: cards use one/two column responsive flow
- Mobile: risk security execution cards remain readable
- Mobile: no horizontal overflow

## Stop rules

- do not mutate active 8096
- do not add V3 layer to active shell
- do not replace active panel before visual approval
- do not touch DB/API/fetch/nginx/service/timer/live/paper/auto

## Data contract

- Centers: `8`
- Modules: `47`
- Risk slots: `7`
- Risk cards: `12`

