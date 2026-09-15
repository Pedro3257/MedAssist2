import os
import re
from pathlib import Path


ENVIRONMENT_KEY_PATTERN = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')


class ConfigurationError(ValueError):
    '''A configuracao da aplicacao e ausente ou invalida.'''


def load_env_file(
    path: str | Path = '.env',
    *,
    override: bool = False,
) -> bool:
    env_path = Path(path)
    if not env_path.is_file():
        return False

    for line_number, raw_line in enumerate(
        env_path.read_text(encoding='utf-8-sig').splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue

        if line.startswith('export '):
            line = line[len('export '):].lstrip()

        if '=' not in line:
            raise ConfigurationError(
                f'Linha {line_number} invalida no arquivo de ambiente'
            )

        key, value = line.split('=', 1)
        key = key.strip()
        value = value.strip()

        if not ENVIRONMENT_KEY_PATTERN.fullmatch(key):
            raise ConfigurationError(
                f'Nome de variavel invalido na linha {line_number}'
            )

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in (chr(39), chr(34))
        ):
            value = value[1:-1]

        if override or key not in os.environ:
            os.environ[key] = value

    return True


def positive_float_from_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f'{name} deve ser um numero'
        ) from error

    if value <= 0:
        raise ConfigurationError(
            f'{name} deve ser maior que zero'
        )

    return value


def nonnegative_float_from_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = float(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f'{name} deve ser um numero'
        ) from error

    if value < 0:
        raise ConfigurationError(
            f'{name} nao pode ser negativo'
        )

    return value


def nonnegative_int_from_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise ConfigurationError(
            f'{name} deve ser um numero inteiro'
        ) from error

    if value < 0:
        raise ConfigurationError(
            f'{name} nao pode ser negativo'
        )

    return value
