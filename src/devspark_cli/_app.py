"""Typer application, banner, and top-level callback."""

import sys

import typer
from rich.align import Align
from rich.console import Console
from rich.text import Text
from typer.core import TyperGroup

from .commands.skills import skills_app
from .harness.cli import adapter_app, harness_app

BANNER = """
██████╗ ███████╗██╗   ██╗███████╗██████╗  █████╗ ██████╗ ██╗  ██╗
██╔══██╗██╔════╝██║   ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝
██║  ██║█████╗  ██║   ██║███████╗██████╔╝███████║██████╔╝█████╔╝ 
██║  ██║██╔══╝  ╚██╗ ██╔╝╚════██║██╔═══╝ ██╔══██║██╔══██╗██╔═██╗ 
██████╔╝███████╗ ╚████╔╝ ███████║██║     ██║  ██║██║  ██║██║  ██╗
╚═════╝ ╚══════╝  ╚═══╝  ╚══════╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
"""

TAGLINE = "DevSpark — AI Development Lifecycle Prompts"

console = Console()


class BannerGroup(TyperGroup):
    """Custom group that shows banner before help."""

    def format_help(self, ctx, formatter):
        # Show banner before help
        show_banner()
        super().format_help(ctx, formatter)


app = typer.Typer(
    name="devspark",
    help="Scaffold projects with DevSpark prompt templates and scripts",
    add_completion=False,
    invoke_without_command=True,
    cls=BannerGroup,
)

app.add_typer(harness_app, name="harness")
app.add_typer(adapter_app, name="adapter")
app.add_typer(skills_app, name="skills")


def show_banner():
    """Display the ASCII art banner."""
    banner_lines = BANNER.strip().split('\n')
    colors = ["bright_blue", "blue", "cyan", "bright_cyan", "white", "bright_white"]

    styled_banner = Text()
    for i, line in enumerate(banner_lines):
        color = colors[i % len(colors)]
        styled_banner.append(line + "\n", style=color)

    console.print(Align.center(styled_banner))
    console.print(Align.center(Text(TAGLINE, style="italic bright_yellow")))
    console.print()


@app.callback()
def callback(ctx: typer.Context):
    """Show banner when no subcommand is provided."""
    if ctx.invoked_subcommand is None and "--help" not in sys.argv and "-h" not in sys.argv:
        show_banner()
        console.print(Align.center("[dim]Run 'devspark --help' for usage information[/dim]"))
        console.print()
