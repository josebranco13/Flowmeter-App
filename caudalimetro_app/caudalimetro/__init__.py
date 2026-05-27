from __future__ import annotations

if __package__:
    from .app import CaudalimetroApp
else:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from caudalimetro.app import CaudalimetroApp

__all__ = ["CaudalimetroApp"]


if __name__ == "__main__":
    app = CaudalimetroApp()
    app.mainloop()
