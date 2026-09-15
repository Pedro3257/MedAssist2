import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from time import sleep
from typing import TextIO

from medassist.application.llm import LLMProviderError, LLMRequest
from medassist.application.prompts import SYSTEM_PROMPT_VERSION, get_system_prompt
from medassist.providers.factory import LLMRuntime, create_llm_runtime


DEFAULT_INPUT = Path('data/processed/evaluation.jsonl')
DEFAULT_OUTPUT_DIR = Path('reports/evidence')


def load_records(path: Path, limit: int | None = None) -> list[dict]:
    if limit is not None and limit <= 0:
        raise ValueError('limit deve ser maior que zero')
    records = []
    with path.open(encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f'JSON invalido na linha {line_number}') from error
            if not isinstance(record, dict):
                raise ValueError(f'Registro invalido na linha {line_number}')
            if not str(record.get('id', '')).strip():
                raise ValueError(f'ID ausente na linha {line_number}')
            if not str(record.get('question', '')).strip():
                raise ValueError(f'Pergunta ausente na linha {line_number}')
            records.append(record)
            if limit is not None and len(records) >= limit:
                break
    return records


def successful_results(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    results = []
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if not line.strip():
                continue
            item = json.loads(line)
            if item.get('status') == 'success':
                results.append(item)
    return results


def evaluate_record(
    record: dict,
    runtime: LLMRuntime,
    max_tokens: int,
    temperature: float,
) -> dict:
    common = {
        'schema_version': '1.0.0',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'id': record['id'],
        'question': record['question'],
        'reference_answer': record.get('answer'),
        'focus': record.get('focus'),
        'question_type': record.get('question_type'),
        'source': record.get('source'),
        'url': record.get('url'),
        'provider': runtime.provider.name,
        'configured_model': runtime.model,
        'system_prompt_version': SYSTEM_PROMPT_VERSION,
    }
    request = LLMRequest(
        system_prompt=get_system_prompt(),
        user_prompt=record['question'],
        model=runtime.model,
        temperature=temperature,
        max_tokens=max_tokens,
        correlation_id=(
            f"baseline-{runtime.provider.name}-{record['id']}"
        ),
    )
    try:
        response = runtime.provider.generate(request)
    except LLMProviderError as error:
        return {
            **common,
            'status': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
        }
    return {
        **common,
        'status': 'success',
        'model': response.model,
        'response': response.content,
        'latency_ms': round(response.latency_ms, 3),
        'input_tokens': response.input_tokens,
        'output_tokens': response.output_tokens,
        'finish_reason': response.finish_reason,
    }


def run_baseline(
    records: list[dict],
    runtime: LLMRuntime,
    output_path: Path,
    *,
    max_tokens: int = 256,
    temperature: float = 0.1,
    resume: bool = False,
    delay_seconds: float = 0,
    progress: TextIO | None = None,
) -> dict:
    if max_tokens <= 0:
        raise ValueError('max_tokens deve ser maior que zero')
    if not 0 <= temperature <= 2:
        raise ValueError('temperature deve estar entre 0 e 2')
    if delay_seconds < 0:
        raise ValueError('delay_seconds nao pode ser negativo')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    previous_successes = successful_results(output_path) if resume else []
    skipped_ids = {item['id'] for item in previous_successes}
    if resume and output_path.is_file():
        with output_path.open('w', encoding='utf-8', newline='\n') as stream:
            for item in previous_successes:
                stream.write(json.dumps(item, ensure_ascii=False) + '\n')
    mode = 'a' if resume else 'w'
    stats = {'selected': len(records), 'success': 0, 'error': 0, 'skipped': 0}
    with output_path.open(mode, encoding='utf-8', newline='\n') as stream:
        for index, record in enumerate(records, start=1):
            if record['id'] in skipped_ids:
                stats['skipped'] += 1
                continue
            result = evaluate_record(
                record,
                runtime,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            stream.write(json.dumps(result, ensure_ascii=False) + '\n')
            stream.flush()
            stats[result['status']] += 1
            if progress is not None:
                print(
                    f"[{index}/{len(records)}] {record['id']} {result['status']}",
                    file=progress,
                    flush=True,
                )
            if delay_seconds and index < len(records):
                sleep(delay_seconds)
    return stats


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Executa o baseline da LLM.')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--provider', choices=('ollama', 'google_ai'))
    parser.add_argument('--limit', type=int)
    parser.add_argument('--max-tokens', type=int, default=256)
    parser.add_argument('--temperature', type=float, default=0.1)
    parser.add_argument('--delay-seconds', type=float, default=0)
    parser.add_argument('--resume', action='store_true')
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.provider:
        os.environ['LLM_PROVIDER'] = args.provider
    runtime = create_llm_runtime()
    output_path = args.output or (
        DEFAULT_OUTPUT_DIR / f'baseline_{runtime.provider.name}.jsonl'
    )
    records = load_records(args.input, args.limit)
    stats = run_baseline(
        records,
        runtime,
        output_path,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        resume=args.resume,
        delay_seconds=args.delay_seconds,
        progress=os.sys.stdout,
    )
    summary_path = output_path.with_suffix('.summary.json')
    summary = {
        **stats,
        'provider': runtime.provider.name,
        'configured_model': runtime.model,
        'system_prompt_version': SYSTEM_PROMPT_VERSION,
        'output': output_path.as_posix(),
    }
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
        encoding='utf-8',
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 1 if stats['error'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
