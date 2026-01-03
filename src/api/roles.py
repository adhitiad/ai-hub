from enum import Enum


# 1. Definisi Enum Role (Agar tidak typo saat coding)
class UserRole(str, Enum):
    FREE = "free"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"
    OWNER = "owner"


# 2. Definisi Level Kekuasaan (Hierarchy)
# Semakin tinggi angka, semakin kuat permission-nya
ROLE_LEVELS = {
    UserRole.FREE: 1,
    UserRole.PREMIUM: 2,
    UserRole.ENTERPRISE: 3,
    UserRole.ADMIN: 9,
    UserRole.OWNER: 10,
}


# 3. Fungsi Cek Permission
def check_permission(user_role: str, required_role: UserRole) -> bool:
    """
    Mengembalikan True jika level role user >= level yang dibutuhkan.
    Contoh: User 'admin' (9) boleh akses fitur 'premium' (2).
    """
    # Default ke level 0 jika role aneh/tidak terdaftar
    try:
        user_role_enum = UserRole(user_role)
        current_level = ROLE_LEVELS.get(user_role_enum, 0)
    except ValueError:
        current_level = 0
    required_level = ROLE_LEVELS.get(required_role, 0)

    return current_level >= required_level
