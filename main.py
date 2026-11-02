"""
Abre la interfaz gráfica del sistema:  python main.py   (o  python main.py --web)

El código está en src/veterinaria; este archivo sólo lo agrega al path de Python.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from veterinaria.main import main  # noqa: E402

if __name__ == "__main__":
    main()
