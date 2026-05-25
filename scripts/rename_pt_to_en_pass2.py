"""
Step C Pass 2: Fix remaining PT symbols in all .py files.
Run from backend/ directory.
"""
import os

REPLACEMENTS = [
    # Fix main.py router variable names (still Portuguese)
    ("router as community_router", "router as community_router"),
    ("router as admin_content_router", "router as admin_content_router"),
    ("router as comments_router", "router as comments_router"),
    ("router as content_router", "router as content_router"),
    ("admin_router as admin_metrics_router", "admin_router as admin_metrics_router"),
    ("router as metrics_router", "router as metrics_router"),
    ("router as users_router", "router as users_router"),
    ("community_router", "community_router"),
    ("admin_content_router", "admin_content_router"),
    ("comments_router", "comments_router"),
    ("content_router", "content_router"),
    ("admin_metrics_router", "admin_metrics_router"),
    ("metrics_router", "metrics_router"),
    ("users_router", "users_router"),

    # Fix remaining import references
    ("from app.contexts.community.domain.entities import CommunityMember",
     "from app.contexts.community.domain.entities import CommunityMember"),
    ("from app.contexts.metrics.domain.entities import WeeklyMetric, UserMonthlyMetrics",
     "from app.contexts.metrics.domain.entities import WeeklyMetric, UserMonthlyMetrics"),
    ("from app.contexts.metrics.domain.entities import WeeklyMetric",
     "from app.contexts.metrics.domain.entities import WeeklyMetric"),
    ("from app.contexts.metrics.domain.entities import UserMonthlyMetrics",
     "from app.contexts.metrics.domain.entities import UserMonthlyMetrics"),
    ("from app.contexts.metrics.infrastructure.models import WeeklyMetricModel, UserMetricModel",
     "from app.contexts.metrics.infrastructure.models import WeeklyMetricModel, UserMetricModel"),
    ("UserMetricModel", "UserMetricModel"),

    # Entity class names - metrics
    ("class WeeklyMetric", "class WeeklyMetric"),
    ("WeeklyMetric(", "WeeklyMetric("),
    (": WeeklyMetric", ": WeeklyMetric"),
    ("WeeklyMetric", "WeeklyMetric"),
    ("class UserMonthlyMetrics", "class UserMonthlyMetrics"),
    ("class UserMonthlyMetrics", "class UserMonthlyMetrics"),
    ("UserMonthlyMetrics(", "UserMonthlyMetrics("),
    ("UserMonthlyMetrics(", "UserMonthlyMetrics("),
    (": UserMonthlyMetrics", ": UserMonthlyMetrics"),
    (": UserMonthlyMetrics", ": UserMonthlyMetrics"),
    ("list[UserMonthlyMetrics]", "list[UserMonthlyMetrics]"),
    ("list[UserMonthlyMetrics]", "list[UserMonthlyMetrics]"),

    # Entity class names - content
    ("class CommentRead", "class CommentRead"),
    ("CommentRead(", "CommentRead("),
    (": CommentRead", ": CommentRead"),
    ("list[CommentRead]", "list[CommentRead]"),
    ("CommentRead", "CommentRead"),
    # Old entity names used in repositories
    ("class Track", "class Track"),
    ("Track(", "Track("),
    (": Track", ": Track"),
    ("list[Track]", "list[Track]"),
    ("-> Track", "-> Track"),
    ("class Module", "class Module"),
    ("Module(", "Module("),
    (": Module", ": Module"),
    ("list[Module]", "list[Module]"),
    ("-> Module", "-> Module"),
    ("class Lesson", "class Lesson"),
    ("Lesson(", "Lesson("),
    (": Lesson", ": Lesson"),
    ("list[Lesson]", "list[Lesson]"),
    ("-> Lesson", "-> Lesson"),
    ("class Comment", "class Comment"),
    ("Comment(", "Comment("),
    (": Comment", ": Comment"),
    ("list[Comment]", "list[Comment]"),
    ("-> Comment", "-> Comment"),
    ("class StudentLesson", "class StudentLesson"),
    ("StudentLesson(", "StudentLesson("),

    # Infrastructure repo class names - content
    ("class SqlAlchemyTrackRepository", "class SqlAlchemyTrackRepository"),
    ("SqlAlchemyTrackRepository", "SqlAlchemyTrackRepository"),
    ("class SqlAlchemyModuleRepository", "class SqlAlchemyModuleRepository"),
    ("SqlAlchemyModuleRepository", "SqlAlchemyModuleRepository"),
    ("class SqlAlchemyLessonRepository", "class SqlAlchemyLessonRepository"),
    ("SqlAlchemyLessonRepository", "SqlAlchemyLessonRepository"),
    ("class SqlAlchemyStudentLessonRepository", "class SqlAlchemyStudentLessonRepository"),
    ("SqlAlchemyStudentLessonRepository", "SqlAlchemyStudentLessonRepository"),
    ("class SqlAlchemyCommentRepository", "class SqlAlchemyCommentRepository"),
    ("SqlAlchemyCommentRepository", "SqlAlchemyCommentRepository"),
    ("class SqlAlchemyMetricRepository", "class SqlAlchemyMetricRepository"),
    ("SqlAlchemyMetricRepository", "SqlAlchemyMetricRepository"),

    # Use case class names - content
    ("class CreateLesson", "class CreateLesson"),
    ("CreateLesson(", "CreateLesson("),
    ("class UpdateLesson", "class UpdateLesson"),
    ("UpdateLesson(", "UpdateLesson("),
    ("class DeleteLesson", "class DeleteLesson"),
    ("DeleteLesson(", "DeleteLesson("),
    ("class ReorderLessons", "class ReorderLessons"),
    ("ReorderLessons(", "ReorderLessons("),
    ("class GetLesson", "class GetLesson"),
    ("GetLesson(", "GetLesson("),
    ("class Unmark", "class Unmark"),
    ("class ListComments", "class ListComments"),
    ("ListComments(", "ListComments("),
    ("class CreateComment", "class CreateComment"),
    ("CreateComment(", "CreateComment("),
    ("class DeleteComment", "class DeleteComment"),
    ("DeleteComment(", "DeleteComment("),
    ("class EditComment", "class EditComment"),
    ("EditComment(", "EditComment("),
    ("class CreateModule", "class CreateModule"),
    ("CreateModule(", "CreateModule("),
    ("class UpdateModule", "class UpdateModule"),
    ("UpdateModule(", "UpdateModule("),
    ("class DeleteModule", "class DeleteModule"),
    ("DeleteModule(", "DeleteModule("),
    ("class ReorderModules", "class ReorderModules"),
    ("ReorderModules(", "ReorderModules("),
    ("class CreateTrack", "class CreateTrack"),
    ("CreateTrack(", "CreateTrack("),
    ("class UpdateTrack", "class UpdateTrack"),
    ("UpdateTrack(", "UpdateTrack("),
    ("class DeleteTrack", "class DeleteTrack"),
    ("DeleteTrack(", "DeleteTrack("),
    ("class ReorderTracks", "class ReorderTracks"),
    ("ReorderTracks(", "ReorderTracks("),
    ("class ListTracksWithProgress", "class ListTracksWithProgress"),
    ("ListTracksWithProgress(", "ListTracksWithProgress("),
    ("class GetTrackWithModules", "class GetTrackWithModules"),
    ("GetTrackWithModules(", "GetTrackWithModules("),

    # Use case names - community
    ("class ListCommunity", "class ListCommunity"),
    ("ListCommunity(", "ListCommunity("),

    # Use case names - metrics
    ("class ListMetrics", "class ListMetrics"),
    ("ListMetrics(", "ListMetrics("),
    ("class UpdateMetric", "class UpdateMetric"),
    ("UpdateMetric(", "UpdateMetric("),
    ("class CreateMetric", "class CreateMetric"),
    ("CreateMetric(", "CreateMetric("),

    # DTO class names - content
    ("class TrackProgressDTO", "class TrackProgressDTO"),
    ("TrackProgressDTO(", "TrackProgressDTO("),
    (": TrackProgressDTO", ": TrackProgressDTO"),
    ("list[TrackProgressDTO]", "list[TrackProgressDTO]"),
    ("class LessonSummaryDTO", "class LessonSummaryDTO"),
    ("LessonSummaryDTO(", "LessonSummaryDTO("),
    (": LessonSummaryDTO", ": LessonSummaryDTO"),
    ("list[LessonSummaryDTO]", "list[LessonSummaryDTO]"),
    ("class ModuleWithLessonsDTO", "class ModuleWithLessonsDTO"),
    ("ModuleWithLessonsDTO(", "ModuleWithLessonsDTO("),
    (": ModuleWithLessonsDTO", ": ModuleWithLessonsDTO"),
    ("list[ModuleWithLessonsDTO]", "list[ModuleWithLessonsDTO]"),
    ("class ModuleWithLessonsDTO", "class ModuleWithLessonsDTO"),
    ("ModuleWithLessonsDTO(", "ModuleWithLessonsDTO("),
    (": ModuleWithLessonsDTO", ": ModuleWithLessonsDTO"),
    ("list[ModuleWithLessonsDTO]", "list[ModuleWithLessonsDTO]"),
    ("class TrackWithModulesDTO", "class TrackWithModulesDTO"),
    ("TrackWithModulesDTO(", "TrackWithModulesDTO("),
    (": TrackWithModulesDTO", ": TrackWithModulesDTO"),
    ("list[TrackWithModulesDTO]", "list[TrackWithModulesDTO]"),
    ("class TrackSummaryDTO", "class TrackSummaryDTO"),
    ("TrackSummaryDTO(", "TrackSummaryDTO("),
    (": TrackSummaryDTO", ": TrackSummaryDTO"),
    ("class TrackSummaryDTO", "class TrackSummaryDTO"),
    ("TrackSummaryDTO(", "TrackSummaryDTO("),
    (": TrackSummaryDTO", ": TrackSummaryDTO"),
    ("class LessonDetailDTO", "class LessonDetailDTO"),
    ("LessonDetailDTO(", "LessonDetailDTO("),
    (": LessonDetailDTO", ": LessonDetailDTO"),

    # DTO class names - community
    ("class ListCommunityResultDTO", "class ListCommunityResultDTO"),
    ("ListCommunityResultDTO(", "ListCommunityResultDTO("),
    (": ListCommunityResultDTO", ": ListCommunityResultDTO"),

    # DTO class names - metrics
    ("class DashboardSummaryDTO", "class DashboardSummaryDTO"),
    ("DashboardSummaryDTO(", "DashboardSummaryDTO("),
    (": DashboardSummaryDTO", ": DashboardSummaryDTO"),
    ("class WeeklySeriesDTO", "class WeeklySeriesDTO"),
    ("WeeklySeriesDTO(", "WeeklySeriesDTO("),
    (": WeeklySeriesDTO", ": WeeklySeriesDTO"),
    ("list[WeeklySeriesDTO]", "list[WeeklySeriesDTO]"),
    ("class DashboardSeriesDTO", "class DashboardSeriesDTO"),
    ("DashboardSeriesDTO(", "DashboardSeriesDTO("),
    (": DashboardSeriesDTO", ": DashboardSeriesDTO"),
    ("class UserMonthlyMetricsDTO", "class UserMonthlyMetricsDTO"),
    ("UserMonthlyMetricsDTO(", "UserMonthlyMetricsDTO("),
    (": UserMonthlyMetricsDTO", ": UserMonthlyMetricsDTO"),
    ("list[UserMonthlyMetricsDTO]", "list[UserMonthlyMetricsDTO]"),
    ("class AdminAggregatesDTO", "class AdminAggregatesDTO"),
    ("AdminAggregatesDTO(", "AdminAggregatesDTO("),
    (": AdminAggregatesDTO", ": AdminAggregatesDTO"),
    ("class AdminConsolidatedDTO", "class AdminConsolidatedDTO"),
    ("AdminConsolidatedDTO(", "AdminConsolidatedDTO("),
    (": AdminConsolidatedDTO", ": AdminConsolidatedDTO"),

    # Presentation Schema class names - content
    ("class TrackProgressOut", "class TrackProgressOut"),
    ("TrackProgressOut(", "TrackProgressOut("),
    ("class LessonSummaryOut", "class LessonSummaryOut"),
    ("LessonSummaryOut(", "LessonSummaryOut("),
    ("class ModuleWithLessonsOut", "class ModuleWithLessonsOut"),
    ("ModuleWithLessonsOut(", "ModuleWithLessonsOut("),
    ("class TrackWithModulesOut", "class TrackWithModulesOut"),
    ("TrackWithModulesOut(", "TrackWithModulesOut("),
    ("class LessonDetailOut", "class LessonDetailOut"),
    ("LessonDetailOut(", "LessonDetailOut("),
    ("class CreateTrackIn", "class CreateTrackIn"),
    ("CreateTrackIn(", "CreateTrackIn("),
    ("class UpdateTrackIn", "class UpdateTrackIn"),
    ("UpdateTrackIn(", "UpdateTrackIn("),
    ("class CreateModuleIn", "class CreateModuleIn"),
    ("CreateModuleIn(", "CreateModuleIn("),
    ("class UpdateModuleIn", "class UpdateModuleIn"),
    ("UpdateModuleIn(", "UpdateModuleIn("),
    ("class CreateLessonIn", "class CreateLessonIn"),
    ("CreateLessonIn(", "CreateLessonIn("),
    ("class UpdateLessonIn", "class UpdateLessonIn"),
    ("UpdateLessonIn(", "UpdateLessonIn("),
    ("class CreateCommentIn", "class CreateCommentIn"),
    ("CreateCommentIn(", "CreateCommentIn("),
    ("class EditCommentIn", "class EditCommentIn"),
    ("EditCommentIn(", "EditCommentIn("),

    # Presentation Schema class names - community
    ("class ListCommunityResponse", "class ListCommunityResponse"),
    ("ListCommunityResponse(", "ListCommunityResponse("),

    # Presentation Schema class names - metrics
    ("class DashboardSummaryOut", "class DashboardSummaryOut"),
    ("DashboardSummaryOut(", "DashboardSummaryOut("),
    ("class WeeklySeriesOut", "class WeeklySeriesOut"),
    ("WeeklySeriesOut(", "WeeklySeriesOut("),
    ("class DashboardSeriesOut", "class DashboardSeriesOut"),
    ("DashboardSeriesOut(", "DashboardSeriesOut("),
    ("class UserMonthlyMetricsOut", "class UserMonthlyMetricsOut"),
    ("UserMonthlyMetricsOut(", "UserMonthlyMetricsOut("),
    ("class AdminAggregatesOut", "class AdminAggregatesOut"),
    ("AdminAggregatesOut(", "AdminAggregatesOut("),
    ("class AdminConsolidatedOut", "class AdminConsolidatedOut"),
    ("AdminConsolidatedOut(", "AdminConsolidatedOut("),

    # Auth class names
    ("class SqlAlchemyUserAuthRepository", "class SqlAlchemyUserAuthRepository"),
    ("SqlAlchemyUserAuthRepository", "SqlAlchemyUserAuthRepository"),
    ("class AuthenticatedUserDTO", "class AuthenticatedUserDTO"),
    ("AuthenticatedUserDTO(", "AuthenticatedUserDTO("),
    (": AuthenticatedUserDTO", ": AuthenticatedUserDTO"),
    ("class InvalidToken", "class InvalidToken"),
    ("InvalidToken(", "InvalidToken("),
    ("class ExpiredToken", "class ExpiredToken"),
    ("ExpiredToken(", "ExpiredToken("),
    ("class InactiveAccount", "class InactiveAccount"),
    ("InactiveAccount(", "InactiveAccount("),
    ("class InvalidCredentials", "class InvalidCredentials"),
    ("InvalidCredentials(", "InvalidCredentials("),
    ("class LogoutFailed", "class LogoutFailed"),
    ("LogoutFailed(", "LogoutFailed("),

    # Users
    ("class PhotoStorageGateway", "class PhotoStorageGateway"),
    ("PhotoStorageGateway", "PhotoStorageGateway"),
    ("class PhotoUrlDTO", "class PhotoUrlDTO"),
    ("PhotoUrlDTO(", "PhotoUrlDTO("),
    (": PhotoUrlDTO", ": PhotoUrlDTO"),
    ("class PhotoUrlResponse", "class PhotoUrlResponse"),
    ("PhotoUrlResponse(", "PhotoUrlResponse("),

    # Method names (repository methods) - keep as they are since these are internal
    # Only rename when they appear as PT-only method names not matching English
    # These are method names we'll leave as-is since they're implementation details
    # unless they cross public API boundaries

    # Exception classes - metrics domain
    ("class DuplicateMetric", "class DuplicateMetric"),
    ("DuplicateMetric(", "DuplicateMetric("),
    ("class MetricOutOfWindow", "class MetricOutOfWindow"),
    ("MetricOutOfWindow(", "MetricOutOfWindow("),
    ("class FutureWeekNotAllowed", "class FutureWeekNotAllowed"),
    ("FutureWeekNotAllowed(", "FutureWeekNotAllowed("),
    ("class MetricNotOwnedByUser", "class MetricNotOwnedByUser"),
    ("MetricNotOwnedByUser(", "MetricNotOwnedByUser("),

    # Exception classes - content domain
    ("class CommentNotOwnedByUser", "class CommentNotOwnedByUser"),
    ("CommentNotOwnedByUser(", "CommentNotOwnedByUser("),
    ("class InvalidDriveUrl", "class InvalidDriveUrl"),
    ("InvalidDriveUrl(", "InvalidDriveUrl("),

    # Shared domain
    ("class WeekStart", "class WeekStart"),
    ("WeekStart(", "WeekStart("),
    (": WeekStart", ": WeekStart"),

    # StudentLessonModel (was improperly named in pass 1)
    ("class StudentLessonModel", "class StudentLessonModel"),
    ("StudentLessonModel", "StudentLessonModel"),
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
