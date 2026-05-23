#!/usr/bin/env python3
"""Filter an OpenAPI spec to selected paths and their referenced schemas.

Usage:
    curl -s http://... | python3 scripts/filter_openapi.py /path/one /path/two
"""
import json
import sys


def collect_refs(obj, schemas, collected):
    if isinstance(obj, dict):
        if "$ref" in obj:
            name = obj["$ref"].split("/")[-1]
            if name not in collected and name in schemas:
                collected.add(name)
                collect_refs(schemas[name], schemas, collected)
        for v in obj.values():
            collect_refs(v, schemas, collected)
    elif isinstance(obj, list):
        for item in obj:
            collect_refs(item, schemas, collected)


def main():
    selected = set(sys.argv[1:])
    spec = json.load(sys.stdin)
    all_schemas = spec.get("components", {}).get("schemas", {})

    filtered_paths = {}
    collected = set()

    for path, methods in spec.get("paths", {}).items():
        if path in selected:
            filtered_paths[path] = methods
            collect_refs(methods, all_schemas, collected)

    json.dump(
        {
            "openapi": spec["openapi"],
            "info": spec["info"],
            "paths": filtered_paths,
            "components": {"schemas": {k: v for k, v in all_schemas.items() if k in collected}},
        },
        sys.stdout,
        indent=2,
    )


if __name__ == "__main__":
    main()
