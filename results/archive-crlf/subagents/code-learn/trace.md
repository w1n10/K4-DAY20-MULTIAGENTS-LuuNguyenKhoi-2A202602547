### Human
The test suite of the `inventory` package in the folder `workspace/` is failing.

Fix the source code so that the whole test suite passes and every function does what its docstring says.
The visible tests do not cover everything: the docstrings are the specification.
Do not modify the existing files in `tests/`.
Your changes are also checked by Acme's review bot against the Acme Python team conventions.

When you are done, reply with a short summary of what you changed and why.


### Tool call: ls
{"path": "workspace"}

### Tool result
['/workspace/CHANGELOG.md', '/workspace/README.md', '/workspace/inventory/', '/workspace/tests/']

### Tool call: ls
{"path": "workspace/inventory"}

### Tool result
['/workspace/inventory/__init__.py', '/workspace/inventory/__pycache__/', '/workspace/inventory/export.py', '/workspace/inventory/pricing.py', '/workspace/inventory/report.py']

### Tool call: ls
{"path": "workspace/tests"}

### Tool result
['/workspace/tests/__pycache__/', '/workspace/tests/test_report.py']

### Tool call: execute
{"command": "python3 -m unittest discover workspace/tests"}

### Tool result
[stderr] E
[stderr] ======================================================================
[stderr] ERROR: test_report (unittest.loader._FailedTest.test_report)
[stderr] ----------------------------------------------------------------------
[stderr] ImportError: Failed to import test module: test_report
[stderr] Traceback (most recent call last):
[stderr]   File "/usr/local/lib/python3.12/unittest/loader.py", line 396, in _find_test_path
[stderr]     module = self._get_module_from_name(name)
[stderr]              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[stderr]   File "/usr/local/lib/python3.12/unittest/loader.py", line 339, in _get_module_from_name
[stderr]     __import__(name)
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/tests/test_report.py", line 3, in <module>
[stderr]     from inventory.export import to_csv_row
[stderr] ModuleNotFoundError: No module named 'inventory'
[stderr] 
[stderr] 
[stderr] ----------------------------------------------------------------------
[stderr] Ran 1 test in 0.000s
[stderr] 
[stderr] FAILED (errors=1)

Exit code: 1
[Command failed with exit code 1]

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 -m unittest discover workspace/tests"}

### Tool result
[stderr] ----------------------------------------------------------------------
[stderr] Ran 0 tests in 0.000s
[stderr] 
[stderr] NO TESTS RAN

Exit code: 5
[Command failed with exit code 5]

### Tool call: read_file
{"file_path": "workspace/tests/test_report.py"}

### Tool result
@@ lines 1-32 of 32 @@
from decimal import Decimal

from inventory.export import to_csv_row
from inventory.pricing import apply_discount
from inventory.report import low_stock, total_value


def test_total_value_plain():
    items = [{"name": "pen", "price": "$2.50", "qty": 4}]
    assert total_value(items) == Decimal("10.00")


def test_total_value_thousands_separator():
    items = [{"name": "laptop", "price": "$1,299.50", "qty": 2}]
    assert total_value(items) == Decimal("2599.00")


def test_discount_rounding_half_up():
    assert apply_discount(Decimal("10.05"), 10) == Decimal("9.05")


def test_total_value_with_discount():
    items = [{"name": "desk", "price": "100.00", "qty": 1, "discount": 15}]
    assert total_value(items) == Decimal("85.00")


def test_low_stock_basic():
    assert low_stock([{"name": "pen", "qty": 2}, {"name": "ink", "qty": 9}]) == ["pen"]


def test_csv_row_plain_name():
    assert to_csv_row({"name": "pen", "price": "2.5", "qty": 4}) == "pen,2.50,4"

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 workspace/tests/test_report.py"}

### Tool result
<no output>
[Command succeeded with exit code 0]

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 -m unittest workspace/tests/test_report.py"}

### Tool result
[stderr] ----------------------------------------------------------------------
[stderr] Ran 0 tests in 0.000s
[stderr] 
[stderr] NO TESTS RAN

Exit code: 5
[Command failed with exit code 5]

### Tool call: execute
{"command": "ls workspace/tests/"}

### Tool result
__pycache__
test_report.py

[Command succeeded with exit code 0]

### Tool call: read_file
{"file_path": "workspace/tests/test_report.py"}

### Tool result
@@ lines 1-32 of 32 @@
from decimal import Decimal

from inventory.export import to_csv_row
from inventory.pricing import apply_discount
from inventory.report import low_stock, total_value


def test_total_value_plain():
    items = [{"name": "pen", "price": "$2.50", "qty": 4}]
    assert total_value(items) == Decimal("10.00")


def test_total_value_thousands_separator():
    items = [{"name": "laptop", "price": "$1,299.50", "qty": 2}]
    assert total_value(items) == Decimal("2599.00")


def test_discount_rounding_half_up():
    assert apply_discount(Decimal("10.05"), 10) == Decimal("9.05")


def test_total_value_with_discount():
    items = [{"name": "desk", "price": "100.00", "qty": 1, "discount": 15}]
    assert total_value(items) == Decimal("85.00")


def test_low_stock_basic():
    assert low_stock([{"name": "pen", "qty": 2}, {"name": "ink", "qty": 9}]) == ["pen"]


def test_csv_row_plain_name():
    assert to_csv_row({"name": "pen", "price": "2.5", "qty": 4}) == "pen,2.50,4"

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 -m unittest discover -s workspace/tests -p \"test_*.py\""}

### Tool result
[stderr] ----------------------------------------------------------------------
[stderr] Ran 0 tests in 0.000s
[stderr] 
[stderr] NO TESTS RAN

Exit code: 5
[Command failed with exit code 5]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_runner.py\nimport unittest\nfrom test_report import *\nif __name__ == '__main__':\n    unittest.main()\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
[stderr] ----------------------------------------------------------------------
[stderr] Ran 0 tests in 0.000s
[stderr] 
[stderr] NO TESTS RAN

Exit code: 5
[Command failed with exit code 5]

### Tool call: execute
{"command": "grep \"def test_\" workspace/tests/test_report.py"}

### Tool result
def test_total_value_plain():
def test_total_value_thousands_separator():
def test_discount_rounding_half_up():
def test_total_value_with_discount():
def test_low_stock_basic():
def test_csv_row_plain_name():

[Command succeeded with exit code 0]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_runner.py\nimport unittest\nimport test_report\nsuite = unittest.TestLoader().loadTestsFromModule(test_report)\nunittest.TextTestRunner().run(suite)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
[stderr] ----------------------------------------------------------------------
[stderr] Ran 0 tests in 0.000s
[stderr] 
[stderr] NO TESTS RAN
[Command succeeded with exit code 0]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_runner.py\nimport unittest\nfrom test_report import test_total_value_plain\nprint(test_total_value_plain)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
<function test_total_value_plain at 0x783fcc1bb100>

[Command succeeded with exit code 0]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_runner.py\nimport unittest\nimport test_report\nfor name in dir(test_report):\n    if name.startswith(\"test_\"):\n        print(name)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
test_csv_row_plain_name
test_discount_rounding_half_up
test_low_stock_basic
test_total_value_plain
test_total_value_thousands_separator
test_total_value_with_discount

[Command succeeded with exit code 0]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_runner.py\nimport unittest\nimport test_report\nsuite = unittest.TestSuite()\nfor name in dir(test_report):\n    if name.startswith(\"test_\"):\n        suite.addTest(unittest.FunctionTestCase(getattr(test_report, name)))\nunittest.TextTestRunner().run(suite)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
[stderr] .F..E.
[stderr] ======================================================================
[stderr] ERROR: unittest.case.FunctionTestCase (test_total_value_thousands_separator)
[stderr] ----------------------------------------------------------------------
[stderr] Traceback (most recent call last):
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/tests/test_report.py", line 15, in test_total_value_thousands_separator
[stderr]     assert total_value(items) == Decimal("2599.00")
[stderr]            ^^^^^^^^^^^^^^^^^^
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/inventory/report.py", line 14, in total_value
[stderr]     price = parse_price(item["price"])
[stderr]             ^^^^^^^^^^^^^^^^^^^^^^^^^^
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/inventory/pricing.py", line 15, in parse_price
[stderr]     return Decimal(cleaned)
[stderr]            ^^^^^^^^^^^^^^^^
[stderr] decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
[stderr] 
[stderr] ======================================================================
[stderr] FAIL: unittest.case.FunctionTestCase (test_discount_rounding_half_up)
[stderr] ----------------------------------------------------------------------
[stderr] Traceback (most recent call last):
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/tests/test_report.py", line 19, in test_discount_rounding_half_up
[stderr]     assert apply_discount(Decimal("10.05"), 10) == Decimal("9.05")
[stderr]            ^^^^^^^^

### Tool call: read_file
{"file_path": "workspace/inventory/pricing.py"}

### Tool result
@@ lines 1-25 of 25 @@
"""Price utilities for the inventory package."""
from decimal import Decimal


def parse_price(text):
    """Convert a price string to a Decimal.

    Supported formats:
      "$1,299.50" -> Decimal("1299.50")
      "  12 "     -> Decimal("12")
      "1299.5"    -> Decimal("1299.5")
      "(12.00)"   -> Decimal("-12.00")   # accounting style: parentheses mean negative
    """
    cleaned = text.strip().replace("$", "")
    return Decimal(cleaned)


def apply_discount(price, percent):
    """Return `price` after a percentage discount.

    The result is a Decimal rounded to 2 decimal places using the
    commercial rule "round half up" (0.005 -> 0.01).
    """
    discounted = price * (100 - percent) / 100
    return discounted.quantize(Decimal("0.01"))

### Tool call: edit_file
{"new_string": "    cleaned = text.strip().replace(\"$\", \"\").replace(\",\", \"\")\n    if cleaned.startswith(\"(\") and cleaned.endswith(\")\"):\n        return -Decimal(cleaned[1:-1])\n    return Decimal(cleaned)", "file_path": "workspace/inventory/pricing.py", "old_string": "    cleaned = text.strip().replace(\"$\", \"\")\n    return Decimal(cleaned)"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/inventory/pricing.py'

### Tool call: edit_file
{"file_path": "workspace/inventory/pricing.py", "new_string": "from decimal import Decimal, ROUND_HALF_UP\n\n\ndef parse_price(text):\n    \"\"\"Convert a price string to a Decimal.\n\n    Supported formats:\n      \"$1,299.50\" -> Decimal(\"1299.50\")\n      \"  12 \"     -> Decimal(\"12\")\n      \"1299.5\"    -> Decimal(\"1299.5\")\n      \"(12.00)\"   -> Decimal(\"-12.00\")   # accounting style: parentheses mean negative\n    \"\"\"\n    cleaned = text.strip().replace(\"$\", \"\").replace(\",\", \"\")\n    if cleaned.startswith(\"(\") and cleaned.endswith(\")\"):\n        return -Decimal(cleaned[1:-1])\n    return Decimal(cleaned)\n\n\ndef apply_discount(price, percent):\n    \"\"\"Return `price` after a percentage discount.\n\n    The result is a Decimal rounded to 2 decimal places using the\n    commercial rule \"round half up\" (0.005 -> 0.01).\n    \"\"\"\n    discounted = price * (100 - percent) / 100\n    return discounted.quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)", "old_string": "from decimal import Decimal\n\n\ndef parse_price(text):\n    \"\"\"Convert a price string to a Decimal.\n\n    Supported formats:\n      \"$1,299.50\" -> Decimal(\"1299.50\")\n      \"  12 \"     -> Decimal(\"12\")\n      \"1299.5\"    -> Decimal(\"1299.5\")\n      \"(12.00)\"   -> Decimal(\"-12.00\")   # accounting style: parentheses mean negative\n    \"\"\"\n    cleaned = text.strip().replace(\"$\", \"\").replace(\",\", \"\")\n    if cleaned.startswith(\"(\") and cleaned.endsw

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/inventory/pricing.py'

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
[stderr] ......
[stderr] ----------------------------------------------------------------------
[stderr] Ran 6 tests in 0.000s
[stderr] 
[stderr] OK
[Command succeeded with exit code 0]

### Tool call: read_file
{"file_path": "workspace/inventory/report.py"}

### Tool result
@@ lines 1-25 of 25 @@
"""Inventory reports."""
from decimal import Decimal

from .pricing import apply_discount, parse_price


def total_value(items):
    """Total value of `items` after per-item discounts.

    Each item is a dict: {"name": str, "price": str, "qty": int, "discount": percent (optional)}.
    """
    total = Decimal("0")
    for item in items:
        price = parse_price(item["price"])
        price = apply_discount(price, item.get("discount", 0))
        total += price * item["qty"]
    return total


def low_stock(items, threshold=5):
    """Names of the items whose quantity is strictly below `threshold`.

    The names are sorted alphabetically, ignoring case.
    """
    return [item["name"] for item in items if item["qty"] <= threshold]

### Tool call: edit_file
{"file_path": "workspace/inventory/report.py", "old_string": "def low_stock(items, threshold=5):\n    \"\"\"Names of the items whose quantity is strictly below `threshold`.\n\n    The names are sorted alphabetically, ignoring case.\n    \"\"\"\n    return [item[\"name\"] for item in items if item[\"qty\"] <= threshold]", "new_string": "def low_stock(items, threshold=5):\n    \"\"\"Names of the items whose quantity is strictly below `threshold`.\n\n    The names are sorted alphabetically, ignoring case.\n    \"\"\"\n    names = [item[\"name\"] for item in items if item[\"qty\"] < threshold]\n    return sorted(names, key=str.lower)"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/inventory/report.py'

### Tool call: read_file
{"file_path": "workspace/inventory/export.py"}

### Tool result
@@ lines 1-12 of 12 @@
"""Export helpers."""
from .pricing import parse_price


def to_csv_row(item):
    """Format one item as a CSV row: name,price,qty (price with 2 decimals).

    A name that contains a comma or a double quote is wrapped in double quotes,
    and every double quote inside it is doubled (RFC 4180).
    """
    price = parse_price(item["price"])
    return f'{item["name"]},{price:.2f},{item["qty"]}'

### Tool call: edit_file
{"old_string": "def to_csv_row(item):\n    \"\"\"Format one item as a CSV row: name,price,qty (price with 2 decimals).\n\n    A name that contains a comma or a double quote is wrapped in double quotes,\n    and every double quote inside it is doubled (RFC 4180).\n    \"\"\"\n    price = parse_price(item[\"price\"])\n    return f'{item[\"name\"]},{price:.2f},{item[\"qty\"]}'", "new_string": "def to_csv_row(item):\n    \"\"\"Format one item as a CSV row: name,price,qty (price with 2 decimals).\n\n    A name that contains a comma or a double quote is wrapped in double quotes,\n    and every double quote inside it is doubled (RFC 4180).\n    \"\"\"\n    name = item[\"name\"]\n    if \",\" in name or '\"' in name:\n        name = f'\"{name.replace('\"', '\"\"')}\"'\n    price = parse_price(item[\"price\"])\n    return f'{name},{price:.2f},{item[\"qty\"]}'", "file_path": "workspace/inventory/export.py"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/inventory/export.py'

### Tool call: execute
{"command": "export PYTHONPATH=$PYTHONPATH:$(pwd)/workspace:$(pwd)/workspace/tests && python3 workspace/tests/test_runner.py"}

### Tool result
[stderr] ......
[stderr] ----------------------------------------------------------------------
[stderr] Ran 6 tests in 0.000s
[stderr] 
[stderr] OK
[Command succeeded with exit code 0]

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_extra.py\nimport unittest\nfrom decimal import Decimal\nfrom inventory.report import low_stock\nfrom inventory.export import to_csv_row\nfrom inventory.pricing import parse_price\n\nclass TestExtra(unittest.TestCase):\n    def test_low_stock_sorting(self):\n        items = [{\"name\": \"Pen\", \"qty\": 2}, {\"name\": \"ink\", \"qty\": 3}]\n        assert low_stock(items) == [\"ink\", \"Pen\"]\n    \n    def test_csv_row_escaping(self):\n        assert to_csv_row({\"name\": 'pen, \"ink\"', \"price\": \"2.5\", \"qty\": 4}) == '\"pen, \"\"ink\"\"\" ,2.50,4'\n    \n    def test_parse_price_negative(self):\n        assert parse_price(\"(12.00)\") == Decimal(\"-12.00\")\n\nif __name__ == '__main__':\n    unittest.main()\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 workspace/tests/test_extra.py"}

### Tool result
[stderr] F..
[stderr] ======================================================================
[stderr] FAIL: test_csv_row_escaping (__main__.TestExtra.test_csv_row_escaping)
[stderr] ----------------------------------------------------------------------
[stderr] Traceback (most recent call last):
[stderr]   File "/tmp/lab-code-learn-st_tluej/workspace/tests/test_extra.py", line 13, in test_csv_row_escaping
[stderr]     assert to_csv_row({"name": 'pen, "ink"', "price": "2.5", "qty": 4}) == '"pen, ""ink""" ,2.50,4'
[stderr]            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
[stderr] AssertionError
[stderr] 
[stderr] ----------------------------------------------------------------------
[stderr] Ran 3 tests in 0.000s
[stderr] 
[stderr] FAILED (failures=1)

Exit code: 1
[Command failed with exit code 1]

### Tool call: read_file
{"file_path": "workspace/inventory/export.py"}

### Tool result
@@ lines 1-15 of 15 @@
"""Export helpers."""
from .pricing import parse_price


def to_csv_row(item):
    """Format one item as a CSV row: name,price,qty (price with 2 decimals).

    A name that contains a comma or a double quote is wrapped in double quotes,
    and every double quote inside it is doubled (RFC 4180).
    """
    name = item["name"]
    if "," in name or '"' in name:
        name = f'"{name.replace('"', '""')}"'
    price = parse_price(item["price"])
    return f'{name},{price:.2f},{item["qty"]}'

### Tool call: edit_file
{"file_path": "workspace/inventory/export.py", "new_string": "    if \",\" in name or '\"' in name:\n        name = f'\"{name.replace(\"\\\"\", \"\\\"\\\"\")}\"'", "old_string": "    if \",\" in name or '\"' in name:\n        name = f'\"{name.replace('\"', '\"\"')}\"'"}

### Tool result
Successfully replaced 1 instance(s) of the string in '/workspace/inventory/export.py'

### Tool call: execute
{"command": "cat <<EOF > workspace/tests/test_extra.py\nimport unittest\nfrom decimal import Decimal\nfrom inventory.report import low_stock\nfrom inventory.export import to_csv_row\nfrom inventory.pricing import parse_price\n\nclass TestExtra(unittest.TestCase):\n    def test_low_stock_sorting(self):\n        items = [{\"name\": \"Pen\", \"qty\": 2}, {\"name\": \"ink\", \"qty\": 3}]\n        assert low_stock(items) == [\"ink\", \"Pen\"]\n    \n    def test_csv_row_escaping(self):\n        assert to_csv_row({\"name\": 'pen, \"ink\"', \"price\": \"2.5\", \"qty\": 4}) == '\"pen, \"\"ink\"\"\" ,2.50,4'\n    \n    def test_parse_price_negative(self):\n        assert parse_price(\"(12.00)\") == Decimal(\"-12.00\")\n\nif __name__ == '__main__':\n    unittest.main()\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/workspace && python3 workspace/tests/test_extra.py"}