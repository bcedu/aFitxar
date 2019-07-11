from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_numeric_char(value):
    try:
        int(value)
    except Exception as e:
        raise ValidationError(
            _('%(value)s no es un codi numeric.'),
            params={'value': value},
        )
