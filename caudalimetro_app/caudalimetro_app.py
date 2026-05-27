"""
Aplicação de aquisição de caudais para dispositivo industrial.

Ponto de entrada da aplicação. A implementação está dividida na pasta
`caudalimetro/` para ser mais fácil encontrar cada responsabilidade.
"""

from __future__ import annotations

from caudalimetro import CaudalimetroApp


def main() -> None:
    app = CaudalimetroApp()
    app.mainloop()


if __name__ == "__main__":
    main()
