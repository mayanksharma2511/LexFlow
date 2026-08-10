import bcrypt
from passlib.context import CryptContext  # type: ignore[import-untyped]

if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type(  # type: ignore[attr-defined]
        "About",
        (),
        {"__version__": getattr(bcrypt, "__version__", "4.1.3")},
    )()

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )
def authenticate_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return verify_password(
        plain_password,
        hashed_password,
    )
