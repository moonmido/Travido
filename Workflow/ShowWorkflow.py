"""Render the full Travido workflow and show it as an image.

Run it directly:

    .venv/bin/python Workflow/ShowWorkflow.py

or from a notebook:

    from Workflow.ShowWorkflow import show_workflow
    show_workflow()
"""

import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Workflow.NodePolicy import POLICIES  # noqa: E402
from Workflow.TravidoWorkflow import build_graph  # noqa: E402


PNG_PATH = PROJECT_ROOT / "workflow_graph.png"
MERMAID_PATH = PROJECT_ROOT / "workflow_graph.mmd"


def _render_with_mermaid_ink(drawable) -> bytes:
    return drawable.draw_mermaid_png()


def _render_with_mermaid_cli(drawable, mmdc: str, png_path: Path) -> bytes:
    """Local render through the mermaid CLI, no mermaid.ink round trip."""

    source = png_path.with_suffix(".mmd.tmp")
    source.write_text(drawable.draw_mermaid(), encoding="utf-8")

    try:
        subprocess.run(
            [mmdc, "-i", str(source), "-o", str(png_path), "-b", "white"],
            check=True,
            capture_output=True,
        )
    finally:
        source.unlink(missing_ok=True)

    return png_path.read_bytes()


def _render(drawable, png_path: Path) -> Optional[bytes]:
    try:
        return _render_with_mermaid_ink(drawable)
    except Exception as exc:
        print(f"mermaid.ink unavailable ({type(exc).__name__}), trying local CLI")

    mmdc = shutil.which("mmdc")
    if mmdc:
        try:
            return _render_with_mermaid_cli(drawable, mmdc, png_path)
        except subprocess.CalledProcessError as exc:
            print(exc.stderr.decode(errors="replace"))

    return None


def show_workflow(
    png_path: Path = PNG_PATH,
    open_when_done: bool = False,
) -> Optional[bytes]:
    """Draw the compiled graph and display it with ``IPython.display.Image``.

    Outside a notebook the PNG is written to ``png_path`` and, when
    ``open_when_done`` is set, opened with the system viewer.
    """

    drawable = build_graph().get_graph()

    MERMAID_PATH.write_text(drawable.draw_mermaid(), encoding="utf-8")

    png = _render(drawable, png_path)

    if png is None:
        print("could not render a PNG, mermaid source written instead:")
        print(f"  {MERMAID_PATH}")
        print("  npm install -g @mermaid-js/mermaid-cli   # provides mmdc")
        return None

    png_path.write_bytes(png)

    try:
        from IPython.display import Image, display
    except ImportError:
        print("IPython is not installed, PNG written instead:")
        print(f"  {png_path}")
        print("  pip install ipython   # enables display(Image(...))")
        if open_when_done:
            webbrowser.open(png_path.as_uri())
        return png

    display(Image(png))

    return png


def print_policies() -> None:
    print("node                     attempts  run_timeout  idle_timeout")
    print("-" * 58)
    for name, policy in POLICIES.items():
        print(
            f"{name:<24}{policy.max_attempts:>6}"
            f"{policy.run_timeout:>14}{str(policy.idle_timeout):>14}"
        )
    print()


if __name__ == "__main__":
    print_policies()
    show_workflow(open_when_done=True)
