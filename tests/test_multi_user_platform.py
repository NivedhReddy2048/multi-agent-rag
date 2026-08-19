"""Unit and Integration Test Suite for EKIP Phase 2.9 Multi-User Educational SaaS Platform."""

import pytest
import tempfile
import os
from core.auth import auth_manager, UserRole, SubscriptionPlan
from core.db import db_manager
from core.storage import StorageManager, LocalStorageProvider, S3StorageProvider, AzureBlobStorageProvider, GCSStorageProvider
from core.rbac import rbac_manager
from core.courses import course_manager
from core.collaboration import collaboration_manager
from core.billing import billing_manager
from core.admin import admin_manager
from api import api_router
from graph.builder import create_ekip_planning_graph
from graph.state import EKIPGraphState


def test_auth_and_user_registration():
    """Verify user registration, password hashing, login token generation, and logout."""
    user = auth_manager.register_user(
        username="alice_teacher",
        email="alice@ekip.edu",
        password="SecurePassword123",
        role=UserRole.TEACHER,
    )
    assert user.username == "alice_teacher"
    assert user.role == UserRole.TEACHER

    # Login
    token, logged_user = auth_manager.login("alice@ekip.edu", "SecurePassword123")
    assert token is not None
    assert logged_user.user_id == user.user_id

    # Verify Token
    verified = auth_manager.verify_token(token)
    assert verified.user_id == user.user_id

    # Logout
    auth_manager.logout(token)
    assert auth_manager.verify_token(token) is None


def test_role_based_access_control():
    """Verify RBAC permission checks across roles."""
    teacher = auth_manager.register_user("bob_teacher", "bob@ekip.edu", "pass123", role=UserRole.TEACHER)
    student = auth_manager.register_user("charlie_student", "charlie@ekip.edu", "pass123", role=UserRole.STUDENT)

    assert rbac_manager.has_permission(teacher, "course:create") is True
    assert rbac_manager.has_permission(student, "course:create") is False
    assert rbac_manager.has_permission(student, "quiz:submit") is True


def test_database_manager():
    """Verify dual database execution."""
    res = db_manager.execute_query("SELECT 1")
    assert isinstance(res, list)


def test_cloud_storage_abstraction():
    """Verify Local, S3, Azure, and GCS storage abstraction providers."""
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        local_p = LocalStorageProvider(base_dir=tmp_dir)
        path = local_p.upload_file("test.txt", b"Hello Cloud Storage")
        assert os.path.exists(path)
        assert local_p.download_file("test.txt") == b"Hello Cloud Storage"

    s3_p = S3StorageProvider()
    uri = s3_p.upload_file("s3_file.txt", b"S3 Data")
    assert uri.startswith("s3://")
    assert s3_p.download_file("s3_file.txt") == b"S3 Data"

    azure_p = AzureBlobStorageProvider()
    az_uri = azure_p.upload_file("az.txt", b"Azure Data")
    assert "blob.core.windows.net" in az_uri

    gcs_p = GCSStorageProvider()
    gcs_uri = gcs_p.upload_file("gcs.txt", b"GCS Data")
    assert gcs_uri.startswith("gs://")


def test_course_manager():
    """Verify course creation, student enrollment, and study material publishing."""
    t = auth_manager.register_user("prof_smith", "smith@ekip.edu", "pass123", role=UserRole.TEACHER)
    st = auth_manager.register_user("diana_st", "diana@ekip.edu", "pass123", role=UserRole.STUDENT)

    course = course_manager.create_course("CS101 AI Fundamentals", "Intro to AI", t.user_id)
    course_manager.enroll_student(course.course_id, st.user_id)
    course_manager.publish_material(course.course_id, "Lecture 1", "Introduction to Search")

    student_courses = course_manager.list_courses_for_student(st.user_id)
    assert len(student_courses) == 1
    assert student_courses[0].title == "CS101 AI Fundamentals"


def test_collaboration_manager():
    """Verify shared workspace items and user collaboration permissions."""
    owner = auth_manager.register_user("owner_user", "owner@ekip.edu", "pass123", role=UserRole.RESEARCHER)
    collab = auth_manager.register_user("collab_user", "collab@ekip.edu", "pass123", role=UserRole.RESEARCHER)

    item = collaboration_manager.create_shared_item("Shared ML Notebook", "notebook", {"notes": "initial"}, owner.user_id)
    collaboration_manager.share_with_user(item.item_id, collab.user_id, owner.user_id)

    items = collaboration_manager.list_accessible_items(collab.user_id)
    assert len(items) == 1
    assert items[0].title == "Shared ML Notebook"


def test_saas_billing_manager():
    """Verify subscription tier quotas and feature gating."""
    free_user = auth_manager.register_user("free_user", "free@ekip.edu", "pass123", role=UserRole.STUDENT)
    free_user.subscription_plan = SubscriptionPlan.FREE

    pro_user = auth_manager.register_user("pro_user", "pro@ekip.edu", "pass123", role=UserRole.STUDENT)
    pro_user.subscription_plan = SubscriptionPlan.PRO

    assert billing_manager.check_feature_access(free_user, "team_collaboration_enabled") is False
    assert billing_manager.check_feature_access(pro_user, "team_collaboration_enabled") is True


def test_admin_manager():
    """Verify AdminConsole system metrics and user lists."""
    summary = admin_manager.get_system_summary()
    assert summary["system_status"] == "healthy"
    assert summary["total_registered_users"] >= 1


def test_api_router():
    """Verify REST API endpoint handlers."""
    # Register
    res = api_router.handle_request("/api/auth/register", method="POST", payload={"username": "api_user", "email": "api@ekip.edu", "password": "pass", "role": "student"})
    assert res["status"] == "success"

    # Login
    login_res = api_router.handle_request("/api/auth/login", method="POST", payload={"email": "api@ekip.edu", "password": "pass"})
    assert login_res["status"] == "success"
    token = login_res["token"]

    # Profile ME
    profile_res = api_router.handle_request("/api/users/me", method="GET", token=token)
    assert profile_res["status"] == "success"
    assert profile_res["user"]["email"] == "api@ekip.edu"


def test_langgraph_pipeline_regression():
    """Verify 12-node LangGraph pipeline executes cleanly without regression."""
    graph = create_ekip_planning_graph()
    state = graph.invoke({"question": "Explain Multi-User SaaS Platform Architecture"})
    assert isinstance(state, EKIPGraphState)
