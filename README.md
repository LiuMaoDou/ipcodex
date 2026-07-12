# IPCodex

IPCodex is an offline Huawei VRP configuration parser. The first MVP parses
`display current-configuration` output into a lossless configuration tree and
a typed semantic JSON model.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest -q
```

## Parse a Huawei VRP Configuration

```bash
ipcodex parse samples/huawei/ce_leaf_minimal.cfg --output build/leaf01.json
```

The output contains:

- a lossless configuration tree with source line evidence;
- typed semantic objects for the MVP command set;
- unknown commands with current-view context;
- unresolved object references;
- structural and semantic parsing coverage.

## Add a Huawei Command

1. Add or update a `CommandSpec` in
   `src/ipcodex/schema/huawei_vrp/commands.yaml`.
2. Add parameter decoding only when the parameter type is not already present in
   `src/ipcodex/schema/types.py`.
3. Add a focused matcher test.
4. Add a semantic handler and focused semantic test when the command changes the
   typed device model.
5. Update the appropriate golden fixture and inspect the complete JSON diff.

## Add a Huawei Configuration View

1. Add a `ViewSpec` to `src/ipcodex/schema/huawei_vrp/views.yaml`.
2. Declare every allowed parent explicitly.
3. Add a CST test covering opening, nesting, and `#`-separator closure.
4. Add a malformed-parent test proving the view is not accepted in an invalid
   context.
