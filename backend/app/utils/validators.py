from typing import Optional
import re


def validate_email(email: str) -> bool:
    """
    Valida que el email tenga un formato correcto
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida la fortaleza de una contraseña
    
    Requisitos:
    - Al menos 8 caracteres
    - Al menos una mayúscula
    - Al menos una minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Returns:
        Tupla (es_válida, mensaje)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, "Contraseña válida"


def validate_username(username: str) -> bool:
    """
    Valida que el nombre de usuario sea válido
    - Entre 3 y 50 caracteres
    - Solo letras, números y guiones bajos
    """
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return re.match(pattern, username) is not None
