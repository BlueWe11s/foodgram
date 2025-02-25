import re

from django.core.exceptions import ValidationError

PATTERN = r"^[\w.@+-]+\Z"


def validate_username(value):
    """
    Проверка корректности юзернейма
    """
    if value == "me":
        raise ValidationError(
            "Вы не можете выбрать никнейм 'me', " "выберите другой никнейм."
        )
    if not re.match(PATTERN, value):
        invalid_chars = re.sub(PATTERN, "", value)
        raise ValidationError(
            f"Введите корректный юзернейм."
            f"Эти символы недопустимы: {invalid_chars}"
        )
