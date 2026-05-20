"""
Step C Pass 3: Fix remaining PT symbol references - imports and function signatures.
Run from backend/ directory.
"""
import os

REPLACEMENTS = [
    # Fix imports of old use case class names - lessons
    ("from app.contexts.content.application.use_cases.lessons.crud_admin import (\n    UpdateLesson,\n    CreateLesson,\n    DeleteLesson,\n    ReorderLessons,\n)",
     "from app.contexts.content.application.use_cases.lessons.crud_admin import (\n    UpdateLesson,\n    CreateLesson,\n    DeleteLesson,\n    ReorderLessons,\n)"),
    # Individual import names for old use cases
    ("CreateLesson,", "CreateLesson,"),
    ("UpdateLesson,", "UpdateLesson,"),
    ("DeleteLesson,", "DeleteLesson,"),
    ("ReorderLessons,", "ReorderLessons,"),
    ("CreateLesson", "CreateLesson"),
    ("UpdateLesson", "UpdateLesson"),
    ("DeleteLesson", "DeleteLesson"),
    ("ReorderLessons", "ReorderLessons"),
    # lessons/get (old name was obter.py with GetLesson class)
    ("from app.contexts.content.application.use_cases.lessons.get import GetLesson",
     "from app.contexts.content.application.use_cases.lessons.get import GetLesson"),
    ("GetLesson", "GetLesson"),
    # lessons/unmark (old had Unmark class - now Unmark)
    ("from app.contexts.content.application.use_cases.lessons.unmark import Unmark",
     "from app.contexts.content.application.use_cases.lessons.unmark import Unmark"),
    ("Unmark", "Unmark"),
    # lessons/mark_completed (old had MarkCompleted - now MarkCompleted)
    ("from app.contexts.content.application.use_cases.lessons.mark_completed import MarkCompleted",
     "from app.contexts.content.application.use_cases.lessons.mark_completed import MarkCompleted"),
    ("MarkCompleted", "MarkCompleted"),
    # comments use cases
    ("from app.contexts.content.application.use_cases.comments.delete import DeleteComment",
     "from app.contexts.content.application.use_cases.comments.delete import DeleteComment"),
    ("from app.contexts.content.application.use_cases.comments.create import CreateComment",
     "from app.contexts.content.application.use_cases.comments.create import CreateComment"),
    ("from app.contexts.content.application.use_cases.comments.edit import EditComment",
     "from app.contexts.content.application.use_cases.comments.edit import EditComment"),
    ("from app.contexts.content.application.use_cases.comments.list import ListComments",
     "from app.contexts.content.application.use_cases.comments.list import ListComments"),
    ("DeleteComment,", "DeleteComment,"),
    ("DeleteComment", "DeleteComment"),
    ("CreateComment,", "CreateComment,"),
    ("CreateComment", "CreateComment"),
    ("EditComment,", "EditComment,"),
    ("EditComment", "EditComment"),
    ("ListComments,", "ListComments,"),
    ("ListComments", "ListComments"),
    # modules use cases
    ("CreateModule,", "CreateModule,"),
    ("UpdateModule,", "UpdateModule,"),
    ("DeleteModule,", "DeleteModule,"),
    ("ReorderModules,", "ReorderModules,"),
    ("CreateModule", "CreateModule"),
    ("UpdateModule", "UpdateModule"),
    ("DeleteModule", "DeleteModule"),
    ("ReorderModules", "ReorderModules"),
    # tracks use cases
    ("CreateTrack,", "CreateTrack,"),
    ("UpdateTrack,", "UpdateTrack,"),
    ("DeleteTrack,", "DeleteTrack,"),
    ("ReorderTracks,", "ReorderTracks,"),
    ("CreateTrack", "CreateTrack"),
    ("UpdateTrack", "UpdateTrack"),
    ("DeleteTrack", "DeleteTrack"),
    ("ReorderTracks", "ReorderTracks"),
    ("ListTracksWithProgress,", "ListTracksWithProgress,"),
    ("ListTracksWithProgress", "ListTracksWithProgress"),
    ("GetTrackWithModules,", "GetTrackWithModules,"),
    ("GetTrackWithModules", "GetTrackWithModules"),
    # Deps function names (Portuguese -> English)
    ("get_list_tracks", "get_list_tracks"),
    ("get_track_with_modules", "get_track_with_modules"),
    ("get_create_track", "get_create_track"),
    ("get_update_track", "get_update_track"),
    ("get_delete_track", "get_delete_track"),
    ("get_reorder_tracks", "get_reorder_tracks"),
    ("get_create_module", "get_create_module"),
    ("get_update_module", "get_update_module"),
    ("get_delete_module", "get_delete_module"),
    ("get_reorder_modules", "get_reorder_modules"),
    ("get_lesson", "get_lesson"),
    ("get_create_lesson", "get_create_lesson"),
    ("get_update_lesson", "get_update_lesson"),
    ("get_delete_lesson", "get_delete_lesson"),
    ("get_reorder_lessons", "get_reorder_lessons"),
    ("get_mark_completed", "get_mark_completed"),
    ("get_unmark", "get_unmark"),
    ("get_list_comments", "get_list_comments"),
    ("get_create_comment", "get_create_comment"),
    ("get_edit_comment", "get_edit_comment"),
    ("get_delete_comment", "get_delete_comment"),
    # Fix instantiation with wrong mixed names in deps.py
    ("CreateTrack(", "CreateTrack("),
    ("UpdateTrack(", "UpdateTrack("),
    ("DeleteTrack(", "DeleteTrack("),
    ("CreateModule(", "CreateModule("),
    ("UpdateModule(", "UpdateModule("),
    ("DeleteModule(", "DeleteModule("),
    ("GetLesson(", "GetLesson("),
    ("CreateLesson(", "CreateLesson("),
    ("UpdateLesson(", "UpdateLesson("),
    ("DeleteLesson(", "DeleteLesson("),
    ("CreateComment(", "CreateComment("),
    ("EditComment(", "EditComment("),
    ("DeleteComment(", "DeleteComment("),
    # Schema input class names
    ("CreateCommentIn", "CreateCommentIn"),
    ("EditCommentIn", "EditCommentIn"),
    ("UpdateTrackIn", "UpdateTrackIn"),
    ("UpdateModuleIn", "UpdateModuleIn"),
    ("UpdateLessonIn", "UpdateLessonIn"),
    ("CreateTrackIn", "CreateTrackIn"),
    ("CreateModuleIn", "CreateModuleIn"),
    ("CreateLessonIn", "CreateLessonIn"),
    # Community DTO/schema names
    ("CommunityMemberDTO", "CommunityMemberDTO"),
    ("CommunityMemberSchema", "CommunityMemberSchema"),
    ("ListCommunityResponse", "ListCommunityResponse"),
    ("ListCommunityResultDTO", "ListCommunityResultDTO"),
    ("ListCommunity", "ListCommunity"),
    # Community - fix entity imports
    ("from app.contexts.community.domain.entities import CommunityMember",
     "from app.contexts.community.domain.entities import CommunityMember"),
    ("CommunityMember", "CommunityMember"),
    # Community repository method
    ("async def list_active", "async def list_active"),
    ("list_active(", "list_active("),
    # Content domain repositories - import
    ("from app.contexts.content.domain.entities import (\n    Aula,\n    Comentario,\n    CommentRead,\n    Modulo,\n    Trilha,\n)",
     "from app.contexts.content.domain.entities import (\n    Lesson,\n    Comment,\n    CommentRead,\n    Module,\n    Track,\n)"),
    # Remaining entity names in repos
    ("_track_from_model", "_track_from_model"),
    ("_module_from_model", "_module_from_model"),
    ("_lesson_from_model", "_lesson_from_model"),
    ("_comment_from_model", "_comment_from_model"),
    # Repository method names - content
    ("async def list_by_track", "async def list_by_track"),
    ("list_by_track(", "list_by_track("),
    ("async def list_by_module", "async def list_by_module"),
    ("list_by_module(", "list_by_module("),
    ("async def list_by_lesson", "async def list_by_lesson"),
    ("list_by_lesson(", "list_by_lesson("),
    ("async def get_by_id", "async def get_by_id"),
    ("get_by_id(", "get_by_id("),
    ("async def list_all(", "async def list_all("),
    # But don't rename listar_ativos again
    ("async def list_active", "async def list_active"),
    ("async def create(", "async def create("),
    ("async def update(", "async def update("),
    ("async def delete(", "async def delete("),
    ("async def reorder(", "async def reorder("),
    ("async def next_lesson(", "async def next_lesson("),
    ("async def count_lessons(", "async def count_lessons("),
    ("async def mark_completed(", "async def mark_completed("),
    ("async def unmark(", "async def unmark("),
    ("async def completed_ids(", "async def completed_ids("),
    ("async def delete_comment(", "async def delete_comment("),
    # Fix function calls (non-async)
    ("await self._repo.list_by_track(", "await self._repo.list_by_track("),
    ("await self._repo.list_by_module(", "await self._repo.list_by_module("),
    ("await self._repo.list_by_lesson(", "await self._repo.list_by_lesson("),
    ("await self._repo.get_by_id(", "await self._repo.get_by_id("),
    ("await self._repo.list_all()", "await self._repo.list_all()"),
    ("await self._repo.create(", "await self._repo.create("),
    ("await self._repo.update(", "await self._repo.update("),
    ("await self._repo.delete(", "await self._repo.delete("),
    ("await self._repo.reorder(", "await self._repo.reorder("),
    ("await self._repo.delete_comment(", "await self._repo.delete_comment("),
    ("await self._trilha_repo.get_by_id(", "await self._trilha_repo.get_by_id("),
    ("await self._modulo_repo.get_by_id(", "await self._modulo_repo.get_by_id("),
    ("await self._aula_repo.get_by_id(", "await self._aula_repo.get_by_id("),
    ("await self._trilha_repo.list_all()", "await self._trilha_repo.list_all()"),
    ("await self._modulo_repo.list_by_track(", "await self._modulo_repo.list_by_track("),
    ("await self._aula_repo.list_by_module(", "await self._aula_repo.list_by_module("),
    ("await self._aula_repo.next_lesson(", "await self._aula_repo.next_lesson("),
    ("await self._aluno_aula_repo.mark_completed(", "await self._aluno_aula_repo.mark_completed("),
    ("await self._aluno_aula_repo.unmark(", "await self._aluno_aula_repo.unmark("),
    ("await self._aluno_aula_repo.completed_ids(", "await self._aluno_aula_repo.completed_ids("),
    # Metrics entity names
    ("WeeklyMetric(", "WeeklyMetric("),
    ("WeeklyMetric", "WeeklyMetric"),
    ("UserMonthlyMetrics", "UserMonthlyMetrics"),
    ("UserMonthlyMetrics", "UserMonthlyMetrics"),
    # Content entities in repositories
    ("Track(", "Track("),
    ("Module(", "Module("),
    ("Lesson(", "Lesson("),
    ("Comment(", "Comment("),
    ("CommentRead", "CommentRead"),
    # Fix remaining DTO names with Portuguese
    ("LessonSummaryDTO", "LessonSummaryDTO"),
    ("ModuleWithLessonsDTO", "ModuleWithLessonsDTO"),
    ("TrackProgressDTO", "TrackProgressDTO"),
    ("TrackSummaryDTO", "TrackSummaryDTO"),
    ("LessonDetailDTO", "LessonDetailDTO"),
    ("TrackWithModulesDTO", "TrackWithModulesDTO"),
    # Output schemas (presentation layer)
    ("LessonSummaryOut", "LessonSummaryOut"),
    ("ModuleWithLessonsOut", "ModuleWithLessonsOut"),
    ("TrackWithModulesOut", "TrackWithModulesOut"),
    ("LessonDetailOut", "LessonDetailOut"),
    # Fix auth exception names
    ("InvalidToken", "InvalidToken"),
    ("ExpiredToken", "ExpiredToken"),
    ("InactiveAccount", "InactiveAccount"),
    ("InvalidCredentials", "InvalidCredentials"),
    ("LogoutFailed", "LogoutFailed"),
    # Auth DTO
    ("AuthenticatedUserDTO", "AuthenticatedUserDTO"),
    # users
    ("PhotoStorageGateway", "PhotoStorageGateway"),
    ("PhotoUrlDTO", "PhotoUrlDTO"),
    ("PhotoUrlResponse", "PhotoUrlResponse"),
    # Metrics exceptions
    ("DuplicateMetric", "DuplicateMetric"),
    ("MetricOutOfWindow", "MetricOutOfWindow"),
    ("FutureWeekNotAllowed", "FutureWeekNotAllowed"),
    ("MetricNotOwnedByUser", "MetricNotOwnedByUser"),
    # Content exceptions
    ("CommentNotOwnedByUser", "CommentNotOwnedByUser"),
    ("InvalidDriveUrl", "InvalidDriveUrl"),
    # Shared domain
    ("class WeekStart", "class WeekStart"),
    ("WeekStart(", "WeekStart("),
    ("WeekStart", "WeekStart"),
    # Metrics DTO names
    ("DashboardSummaryDTO", "DashboardSummaryDTO"),
    ("WeeklySeriesDTO", "WeeklySeriesDTO"),
    ("DashboardSeriesDTO", "DashboardSeriesDTO"),
    ("UserMonthlyMetricsDTO", "UserMonthlyMetricsDTO"),
    ("AdminAggregatesDTO", "AdminAggregatesDTO"),
    ("AdminConsolidatedDTO", "AdminConsolidatedDTO"),
    # Metrics presentation schema names
    ("DashboardSummaryOut", "DashboardSummaryOut"),
    ("WeeklySeriesOut", "WeeklySeriesOut"),
    ("DashboardSeriesOut", "DashboardSeriesOut"),
    ("UserMonthlyMetricsOut", "UserMonthlyMetricsOut"),
    ("AdminAggregatesOut", "AdminAggregatesOut"),
    ("AdminConsolidatedOut", "AdminConsolidatedOut"),
    # Auth repo
    ("SqlAlchemyUserAuthRepository", "SqlAlchemyUserAuthRepository"),
    # Infrastructure model tablename references
    ("__tablename__ = \"trilha\"", "__tablename__ = \"tracks\""),
    ("__tablename__ = \"modulo\"", "__tablename__ = \"modules\""),
    ("__tablename__ = \"aula\"", "__tablename__ = \"lessons\""),
    ("__tablename__ = \"aluno_aula\"", "__tablename__ = \"student_lessons\""),
    ("__tablename__ = \"comentario\"", "__tablename__ = \"comments\""),
    ("__tablename__ = \"metrica_semanal\"", "__tablename__ = \"weekly_metrics\""),
    ("__tablename__ = \"usuario\"", "__tablename__ = \"users\""),
    # ForeignKey references
    ("ForeignKey(\"public.trilha.id\"", "ForeignKey(\"public.tracks.id\""),
    ("ForeignKey(\"public.modulo.id\"", "ForeignKey(\"public.modules.id\""),
    ("ForeignKey(\"public.aula.id\"", "ForeignKey(\"public.lessons.id\""),
    ("ForeignKey(\"public.usuario.id\"", "ForeignKey(\"public.users.id\""),
    # SQL string references in repos
    ("FROM public.users", "FROM public.users"),
    ("ORDER BY name", "ORDER BY name"),
]


def replace_in_file(filepath, replacements):
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    original = content
    for old, new in replacements:
        content = content.replace(old, new)
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


changed = []
roots = ['app', 'tests', 'alembic', 'scripts']
for root_dir in roots:
    for dirpath, _, files in os.walk(root_dir):
        for fname in files:
            if fname.endswith('.py'):
                fp = os.path.join(dirpath, fname)
                if replace_in_file(fp, REPLACEMENTS):
                    changed.append(fp)
print(f"Changed {len(changed)} files:")
for f in changed:
    print(f"  {f}")
