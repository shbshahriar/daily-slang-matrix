# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/ui/terminal_ui.py
# PURPOSE: Handles all terminal output — how the slangs look when printed.
#          This is the presentation layer. It knows nothing about how slangs
#          are generated or stored; it only cares about displaying them nicely.
#
# WHAT IT DOES:
#   - Creates a Rich Console for styled terminal output
#   - display_slangs() takes a list of SlangWord objects and prints each one
#     as a styled panel with colour-coded fields
#
# WHY RICH:
#   Python's built-in print() can't do colours, borders, or panels.
#   Rich is a library that renders styled text, tables, and panels in the
#   terminal. Each slang gets its own bordered card for clean readability.
#
# COLOUR CODING:
#   cyan    → slang word (stands out at the top)
#   green   → meaning (positive, easy to read)
#   yellow  → Bengali translation (warm, distinct)
#   magenta → tone (sets mood context)
#   white   → example sentence (neutral, readable)
#
# HOW IT CONNECTS:
#   → Called by display_slangs_node in app/agent/nodes.py (the final pipeline step)
#   → Receives List[SlangWord] from the state — works whether data came from
#     cache (file_handler.py) or from the LLM (slang_agent.py)
#   → app/main.py sets sys.stdout encoding to UTF-8 before this runs,
#     which is required for Bengali characters to display correctly
# ──────────────────────────────────────────────────────────────────────────────

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# A single shared Console instance used for all output in this file.
# Rich uses this to handle styling, width detection, and rendering.
console = Console()


def display_slangs(slangs):
    """
    Prints all slangs to the terminal as styled panels.
    Called as the final step in the LangGraph pipeline (display_slangs_node).

    Each slang is rendered as a bordered card:
    ┌──────────────────────────────────────┐
    │ Word                                 │
    │ Meaning : ...                        │
    │ Bengali : ...                        │
    │ Tone    : ...                        │
    │ Example : ...                        │
    └──────────────────────────────────────┘
    """
    # Print a header banner at the top
    console.print(Panel.fit("Daily Aesthetic Slang Drop", style="bold blue"))
    console.print()

    for slang in slangs:
        # Build styled text line by line for each slang card
        content = Text()
        content.append(f"{slang.word}\n", style="bold cyan")        # slang word — bold, stands out
        content.append("Meaning : ", style="bold white")
        content.append(f"{slang.meaning}\n", style="green")
        content.append("Banglish: ", style="bold white")
        content.append(f"{slang.bengali}\n", style="yellow")
        content.append("Tone    : ", style="bold white")
        content.append(f"{slang.tone}\n", style="magenta")
        content.append("Example : ", style="bold white")
        content.append(slang.example, style="white")

        # Wrap the content in a panel (bordered card) and print it
        console.print(Panel(content, border_style="dim blue", padding=(0, 1)))
        console.print()  # blank line between cards for spacing
