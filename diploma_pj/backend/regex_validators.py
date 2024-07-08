from django.core.validators import RegexValidator

phone_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message="Phone number must be entered in the format: " "'+999999999'. Up to 15 digits allowed.",
)

city_name_validator = RegexValidator(
    regex=r"^[a-zA-Z\s-]+$",
    message="City name is not a valid. Only letters, spaces, and hyphens are allowed.",
)
