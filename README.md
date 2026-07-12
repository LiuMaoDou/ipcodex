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
