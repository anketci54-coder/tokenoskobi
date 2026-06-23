# PHASE52_7_REPO_CLEAN_POLICY_PLAN_NOAPI

## STATUS
PLAN_ONLY

## PURPOSE

Define safe repository cleanup policy before PHASE53.

No delete.
No move.
No git add.
No commit.
No archive action.

## CURRENT ISSUE

Repository has untracked artifacts.

These must not be blindly deleted.

## POLICY

### BACKUP FILES

Files matching:

*.bak
*.bak_*

Classification:

ARCHIVE_OR_IGNORE_CANDIDATE

Action:

Do not commit to canonical repo.
Move/archive only after explicit approval.

### PHASE52_5 / PHASE52_6 AUDIT FILES

Classification:

COMMIT_CANDIDATE

Reason:

They document repository clutter and canonical path audit.

Action:

May be committed if user approves.

### PHASE43E UNTRACKED FILES

Classification:

COMPARE_REQUIRED

Reason:

Possible duplicate or legacy artifact.

Action:

Compare against tracked PHASE43E repair artifacts before deciding.

### PHASE47 POST PUSH UNTRACKED FILES

Classification:

COMPARE_REQUIRED

Reason:

PHASE47 seal already exists, but untracked post-push canonical audit files remain.

Action:

Compare against tracked PHASE47 seal artifacts before deciding.

## SAFE NEXT STEP

PHASE52_8_UNTRACKED_COMPARE_AUDIT_NOAPI

## HARD LOCKS

DELETE=false
MOVE=false
GIT_ADD=false
GIT_COMMIT=false
DB_WRITE=false
RUNTIME_CHANGE=false
PANEL_WRITE=false
SERVICE_RESTART=false

## FINAL_GATE

PASS_PHASE52_7_REPO_CLEAN_POLICY_PLAN_NOAPI
