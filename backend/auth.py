from datetime import datetime, timedelta
from typing import Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from database import get_db
from models import Student, Teacher
import schemas

SECRET_KEY = "supersecretkey" # TODO: change it
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password[:72].encode('utf8'))

def authenticate_user(db: Session, email: str, password: str):
    student = db.query(Student).filter(Student.email == email).first()
    if student and password == student.password:
        return student, "student"
    teacher = db.query(Teacher).filter(Teacher.email == email).first()
    if teacher and password == teacher.password:
        return teacher, "teacher"
    return None, None

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None or role is None:
            print('user_id is none')
            raise credentials_exception
    except JWTError:
        print('jwt error')
        raise credentials_exception

    if role == "student":
        user = db.query(Student).filter(Student.student_id == user_id).first()
    elif role == "teacher":
        user = db.query(Teacher).filter(Teacher.teacher_id == user_id).first()
    else:
        print('could not find user')
        raise credentials_exception

    if user is None:
        raise credentials_exception
    return user, role