To run tests to check visual correctness of rendering:

1. create and activate a virtual environment
2. put your fonts in the `fonts` directory
3. install the requirements and run the tests

```bash
$ cd tests/
$ mkdir fonts/
$ cp /path/to/fonts fonts/ -r
$ pip install -e ..
$ python ./run_tests.py
```

The results will be in the `tests/output` directory.
