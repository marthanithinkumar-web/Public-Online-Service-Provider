from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password, method='pbkdf2:sha256:600000')


def verify_password(password: str, hashed: str) -> bool:
    if hashed.startswith('$pbkdf2-sha256$'):
        # Backward compatibility for accounts created before the Werkzeug
        # password format was adopted. New/changed passwords use Werkzeug.
        from passlib.hash import pbkdf2_sha256
        return pbkdf2_sha256.verify(password, hashed)
    return check_password_hash(hashed, password)
