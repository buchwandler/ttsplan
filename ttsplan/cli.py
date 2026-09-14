from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Literal, cast

from . import PlannerConfig, TTSPlan, TTSPlanner
from .exceptions import TTSPlanError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ttsplan", description="Compile text into an engine-independent TTS plan"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    compile_parser = commands.add_parser("compile", help="compile text or SSMD")
    compile_parser.add_argument("input", type=Path)
    compile_parser.add_argument("--language", required=True)
    compile_parser.add_argument("--format", choices=("plain", "ssmd"))
    compile_parser.add_argument("--unit", choices=("paragraph", "sentence"), default="paragraph")
    compile_parser.add_argument("--output", "-o", required=True, type=Path)
    validate_parser = commands.add_parser("validate", help="validate a plan file")
    validate_parser.add_argument("input", type=Path)
    inspect_parser = commands.add_parser("inspect", help="inspect a plan file")
    inspect_parser.add_argument("input", type=Path)
    inspect_parser.add_argument("--unit", type=int)
    inspect_parser.add_argument("--segment", type=int)
    inspect_parser.add_argument("--warnings", action="store_true")
    inspect_parser.add_argument("--boundaries", action="store_true")
    inspect_parser.add_argument("--tokens", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "compile":
            source = args.input.read_text(encoding="utf-8")
            format_name = cast(
                Literal["plain", "ssmd"],
                args.format
                or ("ssmd" if args.input.suffix.lower() in {".ssmd", ".ssml"} else "plain"),
            )
            plan = TTSPlanner(
                PlannerConfig(language=args.language, document_format=format_name, unit=args.unit)
            ).plan(source)
            plan.save(args.output)
            print(f"wrote {args.output} ({len(plan.segments)} segments, {len(plan.units)} units)")
            return 0
        plan = TTSPlan.load(args.input)
        if args.command == "validate":
            print("valid")
            print(f"schema version: {plan.schema_version}")
            print(f"plan ID: {plan.plan_id}")
            print(f"segments: {len(plan.segments)}")
            print(f"units: {len(plan.units)}")
            print(f"warnings: {len(plan.warnings)}")
            return 0
        _inspect(plan, args)
        return 0
    except (OSError, TTSPlanError, ValueError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _inspect(plan: TTSPlan, args: argparse.Namespace) -> None:
    print(f"TTSPlan schema {plan.schema_version}")
    print(f"Plan: {plan.plan_id}")
    print(f"Source: {plan.source.format}")
    print(f"Default language: {plan.config.get('language', '')}")
    print("\nTexts")
    print(f"  source:      {len(plan.source.text)} characters")
    print(f"  structural:  {len(plan.texts.structural)} characters")
    print(f"  spoken:      {len(plan.texts.spoken)} characters")
    print(f"\nUnits:     {len(plan.units)}")
    print(f"Segments:  {len(plan.segments)}")
    print(f"Languages: {len(plan.languages)}")
    print(f"Warnings:  {len(plan.warnings)}")
    if args.warnings:
        for warning in plan.warnings:
            print(f"warning: {warning}")
    if args.boundaries:
        print("\nBoundaries")
        for boundary in plan.boundaries:
            print(
                f"  {boundary.id}: {boundary.kind} at {boundary.position}, {boundary.seconds}s, {boundary.origin}"
            )
    if args.tokens:
        print("\nTokens")
        for token in plan.tokens:
            print(
                f"  {token.spoken_start}:{token.spoken_end} {token.text!r} {token.language or ''}"
            )
    if args.unit is not None:
        unit = plan.units[args.unit]
        print(f"\nUnit {unit.index}: {unit.kind} {unit.spoken_start}:{unit.spoken_end}")
        for segment_id in unit.segment_ids:
            print(f"  {segment_id}")
    if args.segment is not None:
        segment = plan.segments[args.segment]
        print(f"\nSegment {args.segment}")
        print(f"  text:          {segment.text!r}")
        print(f"  language:      {segment.language}")
        print(f"  paragraph:     {segment.paragraph}")
        print(f"  sentence:      {segment.sentence}")
        print(f"  clause:        {segment.clause}")
        print(f"  pause_before:  {segment.pause_before.seconds}s {segment.pause_before.events}")
        print(f"  pause_after:   {segment.pause_after.seconds}s {segment.pause_after.events}")
        print(f"  directives:    {segment.directives.to_dict()}")
