import re

from django.core.exceptions import ValidationError

pattern = r'^[\w.@+-]+\Z'


def validate_username(value):
    '''
    Проверка корректности юзернейма
    '''
    if value == "me":
        raise ValidationError(
            "Вы не можете выбрать никнейм 'me', "
            "выберите другой никнейм.")
    if not re.match(pattern, value):
        invalid_chars = re.sub(pattern, '', value)
        raise ValidationError(
            f'Введите корректный юзернейм.'
            f'Эти символы недопустимы: {invalid_chars}'
        )
