from importlib import import_module
from pathlib import Path


def run_tests(test_dir: str, pattern: str = "test_*.py") -> None:
    for path in Path(test_dir).glob(pattern):
        module = import_module(f"{test_dir}.{path.stem}")
        for name in dir(module):
            f = getattr(module, name)
            if name.startswith("test_") and callable(f):
                print(name)
                f()


run_tests("tests")
