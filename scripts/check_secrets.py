import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_NAME = re.compile(r'(KEY|TOKEN|SECRET|PASSWORD)', re.IGNORECASE)
GOOGLE_KEY_PATTERN = re.compile(rb'AIza[0-9A-Za-z_-]{30,}')
PRIVATE_KEY_PATTERN = re.compile(rb'-----BEGIN [A-Z ]*PRIVATE KEY-----')
TEXT_SUFFIXES = {
    '.csv',
    '.example',
    '.json',
    '.jsonl',
    '.md',
    '.py',
    '.sql',
    '.toml',
    '.txt',
    '.yaml',
    '.yml',
}
EXCLUDED_DIRECTORIES = {
    '_backups',
    '.git',
    '.idea',
    '.mypy_cache',
    '.pytest_cache',
    '.ruff_cache',
    '.venv',
    '__pycache__',
    'data',
    'models',
    'venv',
}


@dataclass(frozen=True, slots=True)
class Finding:
    path: Path
    category: str


def read_sensitive_values(env_path: Path) -> dict[str, bytes]:
    if not env_path.is_file():
        return {}

    values = {}
    for raw_line in env_path.read_text(encoding='utf-8-sig').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, value = line.split('=', 1)
        name = name.strip()
        value = value.strip()
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in (chr(39), chr(34))
        ):
            value = value[1:-1]
        if SENSITIVE_NAME.search(name) and len(value) >= 8:
            values[name] = value.encode('utf-8')
    return values


def candidate_files(root: Path) -> list[Path]:
    files = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_DIRECTORIES for part in relative.parts):
            continue
        if path.name == '.env' or (
            path.name.startswith('.env.') and path.name != '.env.example'
        ):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == 'Dockerfile':
            files.append(path)
    return files


def scan_repository(
    root: Path,
    secret_values: dict[str, bytes],
) -> tuple[list[Finding], int]:
    findings = []
    files = candidate_files(root)
    for path in files:
        content = path.read_bytes()
        for name, value in secret_values.items():
            if value in content:
                findings.append(Finding(path.relative_to(root), name))
        if GOOGLE_KEY_PATTERN.search(content):
            findings.append(Finding(path.relative_to(root), 'google-api-key-pattern'))
        if PRIVATE_KEY_PATTERN.search(content):
            findings.append(Finding(path.relative_to(root), 'private-key-pattern'))
    return findings, len(files)


def main() -> int:
    secret_values = read_sensitive_values(ROOT / '.env')
    findings, scanned_files = scan_repository(ROOT, secret_values)
    if findings:
        print('Secret scan failed.')
        for finding in findings:
            print(f'- {finding.path.as_posix()}: {finding.category}')
        return 1

    print(
        'Secret scan passed: '
        f'{scanned_files} files checked; '
        f'{len(secret_values)} local secret values compared.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
