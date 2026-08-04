from enum import Enum


class UserRole(str, Enum):
    LAWYER = "LAWYER"
    INTERN = "INTERN"
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"