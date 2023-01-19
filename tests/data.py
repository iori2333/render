from pathlib import Path
from typing import List


class Font:

    FontDirs = [Path("fonts")]
    FontPaths = [
        path for dir in FontDirs for path in dir.glob("*")
        if path.suffix.lower() in (".ttf", ".otf", ".ttc")
    ]
    FontDict = {
        path.stem.replace("-", "").replace(" ", ""): path
        for path in FontPaths
    }

    @classmethod
    def fonts(cls) -> List[Path]:
        return list(cls.FontDict.values())

    @classmethod
    def get(cls, name: str) -> Path:
        return cls.FontDict.get(name, cls.one())

    @classmethod
    def rand(cls) -> Path:
        import random
        return random.choice(cls.FontPaths)

    @classmethod
    def one(cls) -> Path:
        return cls.FontPaths[0]


Output = Path(__file__).parent / "output"
Output.mkdir(exist_ok=True)

__all__ = ["Font", "Output"]
