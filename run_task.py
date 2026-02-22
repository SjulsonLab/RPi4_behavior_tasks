#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from runtime.artifact_validation import validate_run_directory
from runtime.compatibility_layer import parse_cli_overrides, resolve_runtime_parameters
from runtime.logging_schema import (
    RunMetadata,
    append_event,
    create_run_paths,
    write_quality_report,
    write_result,
    write_run_metadata,
)
from runtime.preflight import run_preflight
from runtime.quality_checks import evaluate_run_quality
from runtime.release_policy import DEFAULT_RELEASE_POLICY, ReleasePolicy
from runtime.runner import EXPERIMENTAL_PROTOCOLS, SUPPORTED_PROTOCOLS, run_protocol
from runtime.session_config import build_session_config, load_mouse_info, load_session_template


DEFAULT_TEMPLATE_BY_PROTOCOL = {
    "noop": Path("users/shared/session_templates/noop_default.json"),
    "gonogo": Path("users/shared/session_templates/gonogo_default.json"),
    "go_nogo": Path("users/shared/session_templates/gonogo_default.json"),
    "context": Path("users/shared/session_templates/context_default.json"),
    "matt_context": Path("users/shared/session_templates/context_default.json"),
    "soyoun_treadmill": Path("users/shared/session_templates/soyoun_treadmill_experimental.json"),
    "soyoun_treadmill_experimental": Path("users/shared/session_templates/soyoun_treadmill_experimental.json"),
    "ivsa": Path("users/shared/session_templates/ivsa_experimental.json"),
    "cue_ivsa": Path("users/shared/session_templates/ivsa_experimental.json"),
}
DEFAULT_MOUSE_INFO = Path("users/shared/mouse_info/demo_mouse.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a behavioral task protocol.")
    parser.add_argument(
        "--protocol",
        default=None,
        help=(
            f"Protocol name. Maintained: {', '.join(SUPPORTED_PROTOCOLS)}. "
            f"Experimental (requires --allow-experimental): {', '.join(EXPERIMENTAL_PROTOCOLS)}. "
            "If omitted, use template protocol."
        ),
    )
    parser.add_argument("--template", type=Path, help="Path to session template JSON file.")
    parser.add_argument("--mouse-info", type=Path, help="Path to mouse info JSON file.")
    parser.add_argument("--output-dir", type=Path, default=Path(".task_runs"), help="Output root directory.")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override runtime parameter. Can be repeated.",
    )
    parser.add_argument("--no-interactive", action="store_true", help="Disable interactive fallback prompts.")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip preflight confirmation prompt (debug mode only).",
    )
    parser.add_argument(
        "--run-mode",
        choices=["debug", "production"],
        default="debug",
        help=(
            "Run mode. 'debug' keeps current behavior; 'production' enforces shared-checkout guardrails "
            "(clean checkout + release ref)."
        ),
    )
    parser.add_argument(
        "--allow-experimental",
        action="store_true",
        help="Allow running experimental protocols.",
    )
    parser.add_argument(
        "--require-release-tag",
        action="store_true",
        help=(
            "Production mode only: require HEAD to have an allowed release tag prefix "
            "(recommended on shared Pis)."
        ),
    )
    parser.add_argument(
        "--no-validate-artifacts",
        action="store_true",
        help="Skip run artifact validation (debug-only escape hatch).",
    )
    parser.add_argument(
        "--no-validate-quality",
        action="store_true",
        help="Skip semantic run quality checks (debug-only escape hatch).",
    )
    return parser.parse_args()


def resolve_template_path(repo_root: Path, protocol: str | None, template_arg: Path | None) -> Path:
    if template_arg is not None:
        return (repo_root / template_arg).resolve() if not template_arg.is_absolute() else template_arg
    selected_protocol = protocol if protocol else "noop"
    if selected_protocol not in DEFAULT_TEMPLATE_BY_PROTOCOL:
        raise ValueError(f"No default template is configured for protocol '{selected_protocol}'.")
    return (repo_root / DEFAULT_TEMPLATE_BY_PROTOCOL[selected_protocol]).resolve()


def resolve_mouse_info_path(repo_root: Path, mouse_info_arg: Path | None) -> Path:
    if mouse_info_arg is not None:
        return (repo_root / mouse_info_arg).resolve() if not mouse_info_arg.is_absolute() else mouse_info_arg
    return (repo_root / DEFAULT_MOUSE_INFO).resolve()


def validate_protocol_access(protocol: str, allow_experimental: bool) -> None:
    if protocol in EXPERIMENTAL_PROTOCOLS and not allow_experimental:
        raise ValueError(
            f"Protocol '{protocol}' is experimental and excluded by default. "
            "Re-run with --allow-experimental to continue."
        )


def resolve_release_policy(require_release_tag: bool) -> ReleasePolicy:
    if not require_release_tag:
        return DEFAULT_RELEASE_POLICY
    return replace(DEFAULT_RELEASE_POLICY, require_release_tag_in_production=True)


def validate_runtime_options(
    run_mode: str,
    no_validate_artifacts: bool,
    no_validate_quality: bool,
) -> None:
    if run_mode == "production" and no_validate_artifacts:
        raise ValueError("Artifact validation cannot be disabled in production mode.")
    if run_mode == "production" and no_validate_quality:
        raise ValueError("Run quality validation cannot be disabled in production mode.")


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent

    template_path = resolve_template_path(repo_root, args.protocol, args.template)
    mouse_info_path = resolve_mouse_info_path(repo_root, args.mouse_info)

    template = load_session_template(template_path)
    mouse_info = load_mouse_info(mouse_info_path)

    # Allow CLI protocol override while reusing a template as a parameter source.
    protocol_name = args.protocol if args.protocol else template.protocol
    validate_protocol_access(protocol=protocol_name, allow_experimental=args.allow_experimental)

    cli_overrides = parse_cli_overrides(args.set)
    parameters = resolve_runtime_parameters(
        template=template,
        cli_overrides=cli_overrides,
        interactive=not args.no_interactive,
    )

    session = build_session_config(
        template=template,
        mouse_info=mouse_info,
        resolved_parameters=parameters,
        protocol_override=protocol_name,
        source_template=str(template_path),
    )

    require_confirmation = True if args.run_mode == "production" else (not args.yes)
    release_policy = resolve_release_policy(require_release_tag=args.require_release_tag)
    validate_runtime_options(
        run_mode=args.run_mode,
        no_validate_artifacts=args.no_validate_artifacts,
        no_validate_quality=args.no_validate_quality,
    )

    git_state = run_preflight(
        repo_root=repo_root,
        protocol=session.protocol,
        preset=session.preset,
        mouse_id=session.mouse_info.mouse_id,
        require_confirmation=require_confirmation,
        run_mode=args.run_mode,
        release_policy=release_policy,
    )

    run_paths = create_run_paths(output_root=args.output_dir, run_id=session.run_id)

    metadata = RunMetadata(
        run_id=session.run_id,
        protocol=session.protocol,
        preset=session.preset,
        mouse_id=session.mouse_info.mouse_id,
        project=session.mouse_info.project,
        started_at=session.started_at,
        git_branch=git_state.branch,
        git_tag=git_state.exact_tag,
        git_commit=git_state.commit,
        git_dirty=git_state.dirty,
        run_mode=args.run_mode,
        seed=session.resolved_parameters.get("seed"),
        template_path=session.source_template,
    )
    write_run_metadata(run_paths.metadata_path, metadata)

    def emit_event(event_type: str, payload: dict[str, object]) -> None:
        append_event(run_paths.events_path, event_type=event_type, payload=payload)

    result = run_protocol(session=session, emit_event=emit_event)
    write_result(run_paths.result_path, result)

    if not args.no_validate_artifacts:
        validation_errors = validate_run_directory(run_paths.run_dir)
        if validation_errors:
            joined = "\n".join(f"- {error}" for error in validation_errors)
            raise RuntimeError(f"Run artifact validation failed:\n{joined}")

    quality_report = evaluate_run_quality(run_paths.run_dir)
    write_quality_report(run_paths.quality_report_path, quality_report)
    if not args.no_validate_quality and quality_report["status"] == "FAIL":
        quality_errors = [
            finding["message"]
            for finding in quality_report.get("findings", [])
            if finding.get("level") == "error"
        ]
        joined = "\n".join(f"- {error}" for error in quality_errors)
        raise RuntimeError(f"Run quality validation failed:\n{joined}")

    print(f"Run complete: {session.run_id}")
    print(f"Protocol: {session.protocol}")
    print(f"Output directory: {run_paths.run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
