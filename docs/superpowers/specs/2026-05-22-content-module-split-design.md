# Design: Split content_module into 4 modules

**Date:** 2026-05-22

## Goal

Split `content_module` (which mixes tracks, modules, lessons, and comments) into 4 independent modules across all layers (controllers, services, domain, database).

## New modules

- `tracks_module` — track CRUD + list with progress + get with modules
- `modules_module` — module CRUD
- `lessons_module` — lesson CRUD + get detail + mark/unmark completed
- `comments_module` — comment CRUD (list, create, edit, soft-delete)

## Architecture

### Controllers layer (`app/api/controllers/`)

```
shared_content/
  shared_dto.py       # LessonSummaryDTO/Out, TrackSummaryDTO/Out, ReorderIn, OrderItem
                      # Shared here to avoid circular imports between tracks ↔ lessons DTOs

tracks_module/
  tracks_dto/tracks_dto.py
    # TrackProgressDTO, TrackProgressOut
    # ModuleWithLessonsDTO, ModuleWithLessonsOut
    # TrackWithModulesDTO, TrackWithModulesOut
    # CreateTrackIn, UpdateTrackIn, TrackAdminOut
  tracks_routes/tracks_router.py
    # GET  /tracks
    # GET  /tracks/{track_id}
    # POST/PATCH/DELETE/REORDER  /admin/tracks

modules_module/
  modules_dto/modules_dto.py
    # CreateModuleIn, UpdateModuleIn, ModuleAdminOut
  modules_routes/modules_router.py
    # POST/PATCH/DELETE/REORDER  /admin/modules

lessons_module/
  lessons_dto/lessons_dto.py
    # LessonDetailDTO, LessonDetailOut
    # CreateLessonIn, UpdateLessonIn, LessonAdminOut
  lessons_routes/lessons_router.py
    # GET  /lessons/{lesson_id}
    # POST /lessons/{lesson_id}/complete
    # DELETE /lessons/{lesson_id}/complete
    # POST/PATCH/DELETE/REORDER  /admin/lessons

comments_module/
  comments_dto/comments_dto.py
    # AuthorDTO, CommentDTO, AuthorOut, CommentOut
    # CreateCommentIn, EditCommentIn
  comments_routes/comments_router.py
    # GET  /lessons/{lesson_id}/comments
    # POST /lessons/{lesson_id}/comments
    # PATCH   /comments/{comment_id}
    # DELETE  /comments/{comment_id}
```

### Services layer (`app/services/`)

```
tracks_module/
  crud_admin.py          # CreateTrack, UpdateTrack, DeleteTrack, ReorderTracks
  get_with_modules.py    # GetTrackWithModules
  list_with_progress.py  # ListTracksWithProgress

modules_module/
  crud_admin.py          # CreateModule, UpdateModule, DeleteModule, ReorderModules

lessons_module/
  crud_admin.py          # CreateLesson, UpdateLesson, DeleteLesson, ReorderLessons
  get.py                 # GetLesson
  mark_completed.py      # MarkCompleted
  unmark.py              # Unmark

comments_module/
  create.py              # CreateComment
  delete.py              # DeleteComment
  edit.py                # EditComment
  list.py                # ListComments
```

Services like `GetTrackWithModules` and `GetLesson` depend on repo interfaces from multiple domain modules — this is acceptable at the service layer.

### Domain layer (`app/domain/`)

```
tracks_module/
  tracks_model.py          # Track dataclass
  tracks_exceptions.py     # TrackNotFound
  tracks_repo_interface.py # TrackRepository protocol

modules_module/
  modules_model.py          # Module dataclass
  modules_exceptions.py     # ModuleNotFound
  modules_repo_interface.py # ModuleRepository protocol

lessons_module/
  lessons_model.py          # Lesson, StudentLesson dataclasses
  lessons_exceptions.py     # LessonNotFound, InvalidDriveUrl
  lessons_repo_interface.py # LessonRepository, StudentLessonRepository protocols
  lessons_validator.py      # parse_drive_file_id, DriveFileId

comments_module/
  comments_model.py          # Comment, CommentRead dataclasses
  comments_exceptions.py     # CommentNotFound, CommentNotOwnedByUser
  comments_repo_interface.py # CommentRepository protocol
```

Each domain module is standalone — no cross-imports between domain modules.

### Database layer (`app/database/`)

```
tracks_module/
  tracks_repo.py    # TrackModel + SqlAlchemyTrackRepository
                    # imports ModuleModel + LessonModel for count_lessons()

modules_module/
  modules_repo.py   # ModuleModel + SqlAlchemyModuleRepository

lessons_module/
  lessons_repo.py   # LessonModel, StudentLessonModel + Repositories
                    # imports ModuleModel from modules_repo for next_lesson() query

comments_module/
  comments_repo.py  # CommentModel, UserContentModel + SqlAlchemyCommentRepository
```

**DB cross-imports (no cycles):**
- `lessons_repo` → `modules_repo` (ModuleModel needed in next_lesson)
- `tracks_repo` → `modules_repo`, `lessons_repo` (ModuleModel + LessonModel needed in count_lessons)
- `modules_repo` → nothing
- `comments_repo` → nothing

### Other files updated

- `app/main.py` — imports 4 new routers instead of 3 from content_module
- `app/database/migrations/env.py` — imports 4 new database modules for Alembic model discovery

## Bugs fixed during split

1. **Wrong service import paths** — `content_router.py` currently imports services via `content_service.comments.create` (path doesn't exist). Fixed to correct paths during split.
2. **`TrackModel` column name mismatch** — `_track_from_model` accesses `m.title` but column attribute is `titulo`. Will be preserved as-is (pre-existing bug, out of scope).

## Deletions after split

- `app/api/controllers/content_module/` (entire directory)
- `app/services/content_module/` (entire directory)
- `app/domain/content_module/` (entire directory)
- `app/database/content_module/` (entire directory)
