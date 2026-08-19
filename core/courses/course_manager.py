"""Course, Organization, and Enrollment Management System."""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from core.logger import get_logger

logger = get_logger("core.courses.manager")


class Course(BaseModel):
    course_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str
    description: str
    teacher_id: str
    organization_id: Optional[str] = None
    created_at: float = Field(default_factory=time.time)
    study_materials: List[Dict[str, Any]] = Field(default_factory=list)
    quizzes: List[Dict[str, Any]] = Field(default_factory=list)


class CourseManager:
    """Manages courses, organization enrollment, quiz assignments, and study materials."""

    def __init__(self):
        self._courses: Dict[str, Course] = {}
        self._enrollments: Dict[str, List[str]] = {}  # course_id -> list of student_ids

    def create_course(self, title: str, description: str, teacher_id: str, organization_id: Optional[str] = None) -> Course:
        course = Course(title=title, description=description, teacher_id=teacher_id, organization_id=organization_id)
        self._courses[course.course_id] = course
        self._enrollments[course.course_id] = []
        logger.info(f"Created course '{title}' (ID: {course.course_id}) by Teacher '{teacher_id}'")
        return course

    def enroll_student(self, course_id: str, student_id: str):
        if course_id not in self._courses:
            raise ValueError(f"Course '{course_id}' does not exist.")
        if student_id not in self._enrollments[course_id]:
            self._enrollments[course_id].append(student_id)
            logger.info(f"Enrolled student '{student_id}' in course '{course_id}'")

    def publish_material(self, course_id: str, title: str, content: str):
        if course_id in self._courses:
            self._courses[course_id].study_materials.append({"title": title, "content": content, "published_at": time.time()})

    def assign_quiz(self, course_id: str, quiz_data: Dict[str, Any]):
        if course_id in self._courses:
            self._courses[course_id].quizzes.append(quiz_data)

    def list_courses_for_teacher(self, teacher_id: str) -> List[Course]:
        return [c for c in self._courses.values() if c.teacher_id == teacher_id]

    def list_courses_for_student(self, student_id: str) -> List[Course]:
        enrolled_ids = [c_id for c_id, st_list in self._enrollments.items() if student_id in st_list]
        return [self._courses[c_id] for c_id in enrolled_ids if c_id in self._courses]


# Global singleton instance
course_manager = CourseManager()
