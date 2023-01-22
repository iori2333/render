import re
from importlib import import_module
from pathlib import Path


def setup():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-p", "--profile", action="store_true")
    parser.add_argument("-d",
                        "--dir",
                        default="tests",
                        type=Path,
                        help="test directory")
    parser.add_argument("-f",
                        "--file",
                        default=".*",
                        type=re.compile,
                        help="regex for file name (test_<regex>.py)")
    parser.add_argument("-m",
                        "--method",
                        default=".*",
                        type=re.compile,
                        help="regex for method name (test_<regex>)")
    return parser.parse_args()


def run_tests(
    test_dir: Path,
    file_pattern: re.Pattern,
    method_pattern: re.Pattern,
    profile: bool,
) -> None:
    functions = []
    for path in test_dir.glob(f"test_*.py"):
        if file_pattern.search(path.stem[5:]):
            module = import_module(f"{test_dir}.{path.stem}")
            for name in dir(module):
                f = getattr(module, name)
                if name.startswith("test_") and callable(f):
                    if method_pattern.search(name[5:]):
                        functions.append(f)
    if profile:
        import cProfile
        import pstats

        profiler = cProfile.Profile()
        for f in functions:
            print(f.__name__)
            with profiler:
                f()

        print("=" * 80)
        stat = pstats.Stats(profiler).sort_stats("cumulative")
        _, funcs = stat.get_print_list([])
        stat.print_title()
        for func in funcs:
            file, _, name = func
            file_posix = Path(file).as_posix()
            dir_posix = test_dir.absolute().as_posix()
            if file_posix.startswith(dir_posix) and name.startswith("test_"):
                stat.print_line(func)
        print("=" * 80)
        stat.print_stats()
    else:
        for f in functions:
            print(f.__name__)
            f()


def main():
    args = setup()
    run_tests(args.dir, args.file, args.method, args.profile)


if __name__ == "__main__":
    main()
