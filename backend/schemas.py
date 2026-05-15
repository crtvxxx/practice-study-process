from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date

class StudentRegister(BaseModel):
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    email: EmailStr
    password: str
    group_id: Optional[int] = None

class TeacherRegister(BaseModel):
    first_name: str
    last_name: str
    patronymic: Optional[str] = None
    job_title: str
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    role: str
    email: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True

class CourseOut(BaseModel):
    course_id: int
    course_name: str
    start_date: date
    end_date: date
    status: str
    teacher_name: Optional[str] = None

    class Config:
        from_attributes = True

class GroupOut(BaseModel):
    group_id: int
    group_name: str
    prof: str
    student_count: int

    class Config:
        from_attributes = True

class ExerciseOut(BaseModel):
    exercise_id: int
    exercise_name: str
    expires_on: date
    max_score: float
    status: str
    class Config:
        from_attributes = True

class ExerciseDetailOut(ExerciseOut):
    exercise_desc: Optional[str] = None
    creation_date: date
    course_name: Optional[str] = None
    teacher_name: Optional[str] = None

class ExerciseCreate(BaseModel):
    exercise_name: str
    exercise_desc: Optional[str] = None
    expires_on: date
    max_score: float
    status: Optional[str] = "active"