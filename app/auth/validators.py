import re


def validate_password(password):
    """
    Password must:
    - Be at least 8 characters long
    - Contain at least one uppercase letter
    - Contain at least one lowercase letter
    - Contain at least one number
    - Contain at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"

    if not re.search(r"[ !@#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', password):
        return False, "Password must contain at least one special character"

    return True, "Password is strong"
