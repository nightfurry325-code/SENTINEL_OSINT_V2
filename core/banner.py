"""core/banner.py — SENTINEL OSINT ASCII banner & module headers"""
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box

console = Console()

BANNER = r"""
  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗
  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║
  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║
  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║
  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
"""

def show_banner(cfg=None):
    console.clear()
    console.print(Text(BANNER, style="bold #00ff9f"), justify="center")
    console.print(Text("[ OSINT INTELLIGENCE FRAMEWORK  v2.0.0 ]", style="#00aaff"), justify="center")
    console.print(Text("Email · Username · Phone · IP/Domain · Breach · Social", style="#555555"), justify="center")
    console.print()
    bar = "  [#00ff9f]120+[/] [#555555]Email Sites[/]   [#333333]│[/]   [#00ff9f]100+[/] [#555555]Username Sites[/]   [#333333]│[/]   [#00ff9f]6[/] [#555555]Modules[/]   [#333333]│[/]   [#00ff9f]3[/] [#555555]Export Formats[/]   [#333333]│[/]   [#00ff9f]Async[/] [#555555]Engine[/]  "
    console.print(Text.from_markup(bar), justify="center")
    console.print()

def show_module_header(title: str, color: str = "#00ff9f"):
    console.clear()
    console.print()
    console.print(Panel(
        Align.center(Text(title, style=f"bold {color}")),
        border_style="#333333",
        box=box.SIMPLE,
        padding=(0, 4),
    ))
    console.print()
