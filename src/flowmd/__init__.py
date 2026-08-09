"""flowMD — Convertisseur local de PDF vers Markdown, Word et Excel (fr/ar/en)."""

import os

# Les modèles Docling activent torch.compile, qui exige un compilateur C++
# (cl.exe / MSVC) absent des Windows standards → « InvalidCxxCompiler ».
# Le mode interprété de PyTorch donne les mêmes résultats : on désactive la
# compilation à la volée (surchargeable en définissant la variable à 0).
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")

__version__ = "0.1.0"
