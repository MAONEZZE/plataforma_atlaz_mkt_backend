"""
Step C: Rename Python symbols PT→EN in all .py files.
Run from backend/ directory.
"""
import os
import re

REPLACEMENTS = [
    # Module paths (longest first)
    ("app.contexts.community", "app.contexts.community"),
    ("app.contexts.content", "app.contexts.content"),
    ("app.contexts.users", "app.contexts.users"),
    ("app.contexts.metrics", "app.contexts.metrics"),
    # Sub-module paths
    (".use_cases.lessons", ".use_cases.lessons"),
    (".use_cases.comments", ".use_cases.comments"),
    (".use_cases.modules", ".use_cases.modules"),
    (".use_cases.tracks", ".use_cases.tracks"),
    # Use case file module names (after path renames)
    (".validate_token import", ".validate_token import"),
    (".get_me import", ".get_me import"),
    (".update_me import", ".update_me import"),
    (".upload_photo import", ".upload_photo import"),
    (".unmark import", ".unmark import"),
    (".mark_completed import", ".mark_completed import"),
    (".delete import", ".delete import"),
    (".create import", ".create import"),
    (".edit import", ".edit import"),
    (".list import", ".list import"),
    (".list_with_progress import", ".list_with_progress import"),
    (".get_with_modules import", ".get_with_modules import"),
    (".list_community import", ".list_community import"),
    (".update_metric import", ".update_metric import"),
    (".create_metric import", ".create_metric import"),
    (".list_metrics import", ".list_metrics import"),
    (".get_admin_consolidated import", ".get_admin_consolidated import"),
    (".get_dashboard_summary import", ".get_dashboard_summary import"),
    (".get_dashboard_series import", ".get_dashboard_series import"),
    # Presentation router files
    (".router_content import", ".router_content import"),
    (".router_comments import", ".router_comments import"),
    # Class names (entities, models, repos, use cases)
    ("UserNotFound", "UserNotFound"),
    ("InvalidPhoto", "InvalidPhoto"),
    ("TrackNotFound", "TrackNotFound"),
    ("LessonNotFound", "LessonNotFound"),
    ("ModuleNotFound", "ModuleNotFound"),
    ("CommentNotFound", "CommentNotFound"),
    ("MetricNotFound", "MetricNotFound"),
    ("CommunityNotFound", "CommunityNotFound"),
    ("SqlAlchemyUserRepository", "SqlAlchemyUserRepository"),
    ("SqlAlchemyContentRepository", "SqlAlchemyContentRepository"),
    ("SqlAlchemyMetricsRepository", "SqlAlchemyMetricsRepository"),
    ("SqlAlchemyCommunityRepository", "SqlAlchemyCommunityRepository"),
    ("UserRepository", "UserRepository"),
    ("ContentRepository", "ContentRepository"),
    ("MetricsRepository", "MetricsRepository"),
    ("CommunityRepository", "CommunityRepository"),
    ("UserModel", "UserModel"),
    ("TrackModel", "TrackModel"),
    ("ModuleModel", "ModuleModel"),
    ("LessonModel", "LessonModel"),
    ("StudentLessonModel", "StudentLessonModel"),
    ("CommentModel", "CommentModel"),
    ("MetricModel", "MetricModel"),
    ("WeeklyMetricModel", "WeeklyMetricModel"),
    ("UserContentModel", "UserContentModel"),
    ("UserMetricModel", "UserMetricModel"),
    # Domain entities
    ("class User", "class User"),
    ("class Track", "class Track"),
    ("class Module", "class Module"),
    ("class Lesson", "class Lesson"),
    ("class StudentLesson", "class StudentLesson"),
    ("class Comment", "class Comment"),
    ("class Metric", "class Metric"),
    ("class CommunityMember", "class CommunityMember"),
    # Use case class names
    ("class GetMe", "class GetMe"),
    ("class UpdateMe", "class UpdateMe"),
    ("class UploadPhoto", "class UploadPhoto"),
    ("class ValidateToken", "class ValidateToken"),
    ("class MarkCompleted", "class MarkCompleted"),
    ("class Unmark", "class Unmark"),
    ("class Delete", "class Delete"),
    ("class Create", "class Create"),
    ("class Edit", "class Edit"),
    ("class List", "class List"),
    ("class ListComProgresso", "class ListWithProgress"),
    ("class GetWithModules", "class GetWithModules"),
    ("class ListCommunity", "class ListCommunity"),
    ("class CreateMetric", "class CreateMetric"),
    ("class UpdateMetric", "class UpdateMetric"),
    ("class ListMetrics", "class ListMetrics"),
    ("class GetAdminConsolidated", "class GetAdminConsolidated"),
    ("class GetDashboardSummary", "class GetDashboardSummary"),
    ("class GetDashboardSeries", "class GetDashboardSeries"),
    # Also rename instantiation/usage of class names (not just class definitions)
    ("CommunityMember(", "CommunityMember("),
]


def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
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
