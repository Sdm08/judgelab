"""judgelab CLI."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import typer
from rich.console import Console

from judgelab.dataset import AuditSuite
from judgelab.judge import Judge
from judgelab.labels import HumanLabels

app = typer.Typer(help="Audit and calibrate LLM-as-judge pipelines.")
console = Console()


def _load_judge(path: str) -> Judge:
    """Load a Judge from a python file exporting `judge`.

    SECURITY: this executes arbitrary Python from `path`. By default the path
    must resolve inside the current working directory. Set
    JUDGELAB_ALLOW_ANY_PATH=1 to allow absolute paths elsewhere.
    """
    p = Path(path).resolve()
    if not p.exists():
        raise typer.BadParameter(f"Judge file not found: {path}")
    if p.suffix != ".py":
        raise typer.BadParameter(f"Judge file must be .py: {path}")
    if os.environ.get("JUDGELAB_ALLOW_ANY_PATH") != "1":
        cwd = Path.cwd().resolve()
        try:
            p.relative_to(cwd)
        except ValueError:
            raise typer.BadParameter(
                f"Refusing to load judge outside cwd: {p}. "
                "Set JUDGELAB_ALLOW_ANY_PATH=1 to override."
            )
    spec = importlib.util.spec_from_file_location("user_judge", p)
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    sys.modules["user_judge"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    obj = getattr(mod, "judge", None)
    if obj is None:
        raise typer.BadParameter(f"{path} must export `judge`")
    if isinstance(obj, Judge):
        return obj
    return Judge.from_callable(obj)


@app.command()
def audit(
    judge: str = typer.Option(..., "--judge", help="Path to .py file exporting `judge`"),
    dataset: str = typer.Option(..., "--dataset", help="JSONL dataset path"),
    labels: str = typer.Option(None, "--labels", help="Optional human labels CSV"),
    checks: str = typer.Option(
        "position_bias,verbosity_bias",
        "--checks",
        help="Comma-separated check names",
    ),
    out: str = typer.Option("report", "--out", help="Output directory"),
):
    """Run audit checks, write HTML + JSON reports."""
    j = _load_judge(judge)
    suite = AuditSuite.from_jsonl(dataset)
    hl = HumanLabels.from_csv(labels) if labels else None
    check_list = [c.strip() for c in checks.split(",") if c.strip()]

    console.print(f"[bold]Auditing[/bold] {j.name} on {len(suite.examples)} examples...")
    report = suite.run(j, checks=check_list, human_labels=hl)

    out_dir = Path(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    report.to_json(out_dir / "report.json")
    report.to_html(out_dir / "report.html")

    console.print(f"[green]Wrote[/green] {out_dir}/report.html and report.json")
    for name, data in report.checks.items():
        interp = data.get("interpretation", "")
        console.print(f"  [cyan]{name}[/cyan]: {interp}")


@app.command()
def ci(config: str = typer.Option(..., "--config", help="YAML config path")):
    """Run audit with thresholds; exit non-zero on failure."""
    import yaml

    cfg = yaml.safe_load(Path(config).read_text(encoding="utf-8"))
    j = _load_judge(cfg["judge"])
    suite = AuditSuite.from_jsonl(cfg["dataset"])
    hl = HumanLabels.from_csv(cfg["labels"]) if cfg.get("labels") else None
    report = suite.run(j, checks=cfg.get("checks", ["position_bias"]), human_labels=hl)

    thresholds = cfg.get("thresholds", {})
    try:
        report.assert_thresholds(**thresholds)
    except AssertionError as e:
        console.print(f"[red]CI FAIL[/red]\n{e}")
        raise typer.Exit(1)
    console.print("[green]CI PASS[/green]")


if __name__ == "__main__":
    app()
