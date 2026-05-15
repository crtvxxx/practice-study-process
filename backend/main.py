from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, Student, Teacher, Course, Group, GroupCourse, Exercise
from schemas import StudentRegister, TeacherRegister, Login, Token, UserOut, CourseOut, GroupOut, ExerciseOut, ExerciseDetailOut, ExerciseCreate
from auth import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

from datetime import timedelta, date
from typing import List

app = FastAPI(title="Auth Service")
app.mount('/public', StaticFiles(directory="public"), name="public") # for future use

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def slash():
    return FileResponse("public/index.html")

@app.get("/registration")
def reg():
    return FileResponse("public/reg/registration.html")

Base.metadata.create_all(bind=engine)

@app.post("/auth/register/student", response_model=Token)
def register_student(data: StudentRegister, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # hashed_pwd = get_password_hash(data.password) # TODO: find WORKING cryptographic engine
    student = Student(
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        email=data.email,
        password=data.password,
        group_id=data.group_id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    access_token = create_access_token(
        data={"sub": str(student.student_id), "role": "student"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/register/teacher", response_model=Token)
def register_teacher(data: TeacherRegister, db: Session = Depends(get_db)):
    if db.query(Teacher).filter(Teacher.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    # hashed_pwd = get_password_hash(data.password)
    teacher = Teacher(
        first_name=data.first_name,
        last_name=data.last_name,
        patronymic=data.patronymic,
        job_title=data.job_title,
        email=data.email,
        password=data.password,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    access_token = create_access_token(
        data={"sub": str(teacher.teacher_id), "role": "teacher"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
def login(data: Login, db: Session = Depends(get_db)):
    user, role = authenticate_user(db, data.email, data.password)
    if not user:
        print('nuh uh')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    user_id = user.student_id if role == "student" else user.teacher_id
    access_token = create_access_token(
        data={"sub": str(user_id), "role": role},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me", response_model=UserOut)
def read_current_user(current=Depends(get_current_user)):
    user, role = current
    user_id = user.student_id if role == "student" else user.teacher_id
    return UserOut(
        id=user_id,
        role=role,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
    )

@app.get("/student/courses", response_model=List[CourseOut])
def get_student_courses(
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "student":
        raise HTTPException(status_code=403, detail="Только для студентов")

    student = user
    if not student.group_id:
        return []
    courses = (
        db.query(Course)
        .join(GroupCourse, GroupCourse.course_id == Course.course_id)
        .filter(GroupCourse.group_id == student.group_id)
        .all()
    )

    result = []
    for c in courses:
        teacher = db.query(Teacher).filter(Teacher.teacher_id == c.teacher_id).first()
        teacher_name = f"{teacher.last_name} {teacher.first_name}" if teacher else "Не назначен"
        result.append(CourseOut(
            course_id=c.course_id,
            course_name=c.course_name,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status,
            teacher_name=teacher_name,
        ))
    return result


@app.get("/teacher/groups", response_model=List[GroupOut])
def get_teacher_groups(
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "teacher":
        raise HTTPException(status_code=403, detail="Только для преподавателей")

    teacher = user
    groups = db.query(Group).filter(Group.curator_id == teacher.teacher_id).all()

    result = []
    for g in groups:
        student_count = db.query(Student).filter(Student.group_id == g.group_id).count()
        result.append(GroupOut(
            group_id=g.group_id,
            group_name=g.group_name,
            prof=g.prof,
            student_count=student_count,
        ))
    return result

@app.get("/student/courses/{course_id}/exercises", response_model=List[ExerciseOut])
def get_student_course_exercises(
    course_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "student":
        raise HTTPException(status_code=403, detail="Только для студентов")
    student = user
    course = db.query(Course).filter(Course.course_id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    link = db.query(GroupCourse).filter(
        GroupCourse.course_id == course_id,
        GroupCourse.group_id == student.group_id
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="У вас нет доступа к этому курсу")

    exercises = db.query(Exercise).filter(Exercise.course_id == course_id).all()
    return exercises

@app.get("/student/exercises/{exercise_id}", response_model=ExerciseDetailOut)
def get_student_exercise_detail(
    exercise_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "student":
        raise HTTPException(status_code=403)
    student = user
    exercise = db.query(Exercise).filter(Exercise.exercise_id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    link = db.query(GroupCourse).filter(
        GroupCourse.course_id == exercise.course_id,
        GroupCourse.group_id == student.group_id
    ).first()
    if not link:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    teacher = db.query(Teacher).filter(Teacher.teacher_id == exercise.creator_id).first()
    course = db.query(Course).filter(Course.course_id == exercise.course_id).first()
    return ExerciseDetailOut(
        exercise_id=exercise.exercise_id,
        exercise_name=exercise.exercise_name,
        expires_on=exercise.expires_on,
        max_score=exercise.max_score,
        status=exercise.status.value if exercise.status else None,
        exercise_desc=exercise.exercise_desc,
        creation_date=exercise.creation_date,
        course_name=course.course_name if course else None,
        teacher_name=f"{teacher.last_name} {teacher.first_name}" if teacher else None,
    )

@app.get("/teacher/groups/{group_id}/courses", response_model=List[CourseOut])
def get_teacher_group_courses(
    group_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "teacher":
        raise HTTPException(status_code=403)
    teacher = user
    group = db.query(Group).filter(Group.group_id == group_id).first()
    if not group or group.curator_id != teacher.teacher_id:
        raise HTTPException(status_code=403, detail="Вы не курируете эту группу")

    courses = db.query(Course).join(GroupCourse).filter(
        GroupCourse.group_id == group_id,
        Course.status == 'active'
    ).all()

    result = []
    for c in courses:
        t = db.query(Teacher).filter(Teacher.teacher_id == c.teacher_id).first()
        result.append(CourseOut(
            course_id=c.course_id,
            course_name=c.course_name,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status.value,
            teacher_name=f"{t.last_name} {t.first_name}" if t else None
        ))
    return result

@app.get("/teacher/courses/{course_id}/exercises", response_model=List[ExerciseOut])
def get_teacher_course_exercises(
    course_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "teacher":
        raise HTTPException(status_code=403)
    teacher = user
    group_link = db.query(GroupCourse).filter(GroupCourse.course_id == course_id).first()
    if not group_link:
        raise HTTPException(status_code=404, detail="Курс не привязан ни к одной группе")
    group = db.query(Group).filter(Group.group_id == group_link.group_id).first()
    if not group or group.curator_id != teacher.teacher_id:
        raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")

    exercises = db.query(Exercise).filter(Exercise.course_id == course_id).all()
    return exercises

@app.post("/teacher/courses/{course_id}/exercises", response_model=ExerciseOut)
def create_exercise(
    course_id: int,
    data: ExerciseCreate,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "teacher":
        raise HTTPException(status_code=403, detail="Только для преподавателей")
    
    teacher = user
    group_link = db.query(GroupCourse).filter(GroupCourse.course_id == course_id).first()
    if not group_link:
        raise HTTPException(status_code=404, detail="Курс не привязан ни к одной группе")
    group = db.query(Group).filter(Group.group_id == group_link.group_id).first()
    if not group or group.curator_id != teacher.teacher_id:
        raise HTTPException(status_code=403, detail="Вы не курируете этот курс")

    exercise = Exercise(
        exercise_name=data.exercise_name,
        exercise_desc=data.exercise_desc,
        course_id=course_id,
        creator_id=teacher.teacher_id,
        expires_on=data.expires_on,
        max_score=data.max_score,
        status=data.status or "active",
        creation_date=date.today()
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise

@app.get("/teacher/exercises/{exercise_id}", response_model=ExerciseDetailOut)
def get_teacher_exercise_detail(
    exercise_id: int,
    current=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user, role = current
    if role != "teacher":
        raise HTTPException(status_code=403)
    teacher = user
    exercise = db.query(Exercise).filter(Exercise.exercise_id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404)
    group_link = db.query(GroupCourse).filter(GroupCourse.course_id == exercise.course_id).first()
    if not group_link:
        raise HTTPException(status_code=404)
    group = db.query(Group).filter(Group.group_id == group_link.group_id).first()
    if not group or group.curator_id != teacher.teacher_id:
        raise HTTPException(status_code=403)

    teacher_obj = db.query(Teacher).filter(Teacher.teacher_id == exercise.creator_id).first()
    course = db.query(Course).filter(Course.course_id == exercise.course_id).first()
    return ExerciseDetailOut(
        exercise_id=exercise.exercise_id,
        exercise_name=exercise.exercise_name,
        expires_on=exercise.expires_on,
        max_score=exercise.max_score,
        status=exercise.status.value if exercise.status else None,
        exercise_desc=exercise.exercise_desc,
        creation_date=exercise.creation_date,
        course_name=course.course_name if course else None,
        teacher_name=f"{teacher_obj.last_name} {teacher_obj.first_name}" if teacher_obj else None,
    )