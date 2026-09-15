"""
Minimiza dados do paciente antes do envio a providers remotos.

O contexto interno permanece completo. A versão remota remove nome,
datas exatas e identificadores de atendimentos e exames.
"""

from __future__ import annotations

from dataclasses import replace

from medassist.application.context_builder import GenerationContext
from medassist.application.patient_context import PatientContext


def build_minimized_patient_text(
    context: PatientContext,
) -> str:
    """Cria um resumo clínico sem identificadores ou datas exatas."""
    lines = [
        "Dados exclusivamente sintéticos e minimizados.",
        f"Biological sex: {context.patient.biological_sex}",
        "",
        "Relevant encounter information:",
    ]

    if context.encounters:
        for encounter in context.encounters:
            lines.extend(
                [
                    f"- Reason: {encounter.reason}",
                    f"  Notes: {encounter.clinical_notes}",
                ]
            )
    else:
        lines.append("- No encounters recorded.")

    lines.extend(
        [
            "",
            "Completed exams:",
        ]
    )

    if context.exams:
        for exam in context.exams:
            lines.extend(
                [
                    f"- Type: {exam.exam_type}",
                    f"  Result: {exam.result_text}",
                ]
            )
    else:
        lines.append("- No completed exams recorded.")

    lines.extend(
        [
            "",
            "Pending or scheduled exams:",
        ]
    )

    if context.pending_exams:
        for pending_exam in context.pending_exams:
            lines.extend(
                [
                    f"- Type: {pending_exam.exam_type}",
                    f"  Status: {pending_exam.status}",
                ]
            )
    else:
        lines.append("- No pending or scheduled exams.")

    return "\n".join(lines)


def minimize_generation_context(
    generation_context: GenerationContext,
    patient_context: PatientContext,
) -> GenerationContext:
    """
    Substitui somente o texto do paciente pela versão minimizada.

    Evidências, fontes e patient_id interno permanecem disponíveis para
    validação e auditoria, mas o patient_id não aparece no texto remoto.
    """
    return replace(
        generation_context,
        patient_text=build_minimized_patient_text(
            patient_context
        ),
    )