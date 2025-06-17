from passlib.context import CryptContext

# It's recommended to use a strong hashing algorithm like bcrypt.
# schemes lists the algorithms that passlib will try, bcrypt is the default.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Hasher:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
