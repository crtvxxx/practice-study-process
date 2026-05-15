import enum

from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from database import Base

class StudentStatus(str, enum.Enum):
    active = 'active'
    expulsion = 'expulsion'
    suspended = 'suspended'

class CourseStatus(str, enum.Enum):
    active = 'active'
    completed = 'completed'

class ExerciseStatus(str, enum.Enum):
    active = 'active'
    expired = 'expired'

class ExerciseCheckStatus(str, enum.Enum):
    not_checked = 'not checked'
    checked = 'checked'

class Student(Base):
    __tablename__ = "students"

    student_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column("fisrt_name", String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    patronymic = Column(String(50))
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    status = Column(Enum(StudentStatus, name='student_status', create_type=False),
                    default=StudentStatus.active, nullable=False)
    group_id = Column(Integer, ForeignKey("groups.group_id", ondelete="SET NULL"), nullable=True)

    group = relationship("Group", back_populates="students")
    completed_exercises = relationship("CompletedExercise", back_populates="student")

class Teacher(Base):
    __tablename__ = "teachers"

    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column("fisrt_name", String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    patronymic = Column(String(50))
    job_title = Column(String(100), nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    courses = relationship("Course", back_populates="teacher")
    exercises = relationship("Exercise", back_populates="creator")
    curated_groups = relationship("Group", back_populates="curator")

class Course(Base):
    __tablename__ = "courses"

    course_id = Column(Integer, primary_key=True)
    course_name = Column(String(50), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="SET NULL"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(CourseStatus, name='course_status', create_type=False),
                    default=CourseStatus.active, nullable=False)

    teacher = relationship("Teacher", back_populates="courses")
    exercises = relationship("Exercise", back_populates="course")
    groups = relationship("GroupCourse", back_populates="course")

class Group(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True)
    group_name = Column(String(10), nullable=False)
    prof = Column(String(50), nullable=False)
    curator_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="SET NULL"))

    curator = relationship("Teacher", back_populates="curated_groups")
    students = relationship("Student", back_populates="group")
    courses = relationship("GroupCourse", back_populates="group")

class Exercise(Base):
    __tablename__ = "exercises"

    exercise_id = Column(Integer, primary_key=True)
    exercise_name = Column(String(50), nullable=False)
    exercise_desc = Column(String(255))
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"))
    creator_id = Column(Integer, ForeignKey("teachers.teacher_id", ondelete="SET NULL"))
    creation_date = Column(Date, default="CURRENT_DATE")
    expires_on = Column(Date, nullable=False)
    max_score = Column(Float, nullable=False)
    status = Column(Enum(ExerciseStatus, name='exercise_status', create_type=False),
                    default=ExerciseStatus.active)

    course = relationship("Course", back_populates="exercises")
    creator = relationship("Teacher", back_populates="exercises")
    completed = relationship("CompletedExercise", back_populates="exercise")

class CompletedExercise(Base):
    __tablename__ = "completed_exercises"

    ce_id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.student_id", ondelete="CASCADE"))
    exercise_id = Column(Integer, ForeignKey("exercises.exercise_id", ondelete="CASCADE"))
    upload_date = Column(Date, default="CURRENT_DATE")
    check_status = Column(Enum(ExerciseCheckStatus, name='exercise_check_status', create_type=False),
                          default=ExerciseCheckStatus.not_checked)
    commentary = Column(String(255))

    student = relationship("Student", back_populates="completed_exercises")
    exercise = relationship("Exercise", back_populates="completed")

class GroupCourse(Base):
    __tablename__ = "group_courses"
    __table_args__ = (
        PrimaryKeyConstraint('group_id', 'course_id'),
    )

    group_id = Column(Integer, ForeignKey("groups.group_id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("courses.course_id", ondelete="CASCADE"))

    group = relationship("Group", back_populates="courses")
    course = relationship("Course", back_populates="groups")