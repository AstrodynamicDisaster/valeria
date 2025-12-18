from typing import Any, List, Dict
from collections import Counter
import json


def compare_json(a: Any, b: Any,
                 ignore_array_order: bool = False,
                 object_list_key: str | None = None) -> List[str]:
    """
    Compare two JSON objects and return a list of differences.
    Args:
        a: The first JSON object.
        b: The second JSON object.
        ignore_array_order: Whether to ignore the order of arrays.
        object_list_key: The key to use to group objects in arrays.
    Returns:
        A list of differences.
    """
    diffs: List[str] = []
    _compare(a, b, path="", diffs=diffs,
             ignore_array_order=ignore_array_order,
             object_list_key=object_list_key)
    return diffs


def _compare(a: Any, b: Any, path: str,
             diffs: List[str],
             ignore_array_order: bool,
             object_list_key: str | None):
    # dict vs dict
    if isinstance(a, dict) and isinstance(b, dict):
        all_keys = set(a.keys()) | set(b.keys())
        for key in sorted(all_keys):
            new_path = f"{path}.{key}" if path else str(key)
            if key not in a:
                diffs.append(f"{new_path}: key missing in first JSON")
            elif key not in b:
                diffs.append(f"{new_path}: key missing in second JSON")
            else:
                _compare(a[key], b[key], new_path, diffs,
                         ignore_array_order, object_list_key)

    # list vs list
    elif isinstance(a, list) and isinstance(b, list):
        if ignore_array_order:
            # Caso especial: lista de objetos con una clave identificadora (p.ej. "concepto")
            if (
                object_list_key
                and all(isinstance(x, dict) and object_list_key in x for x in a + b)
            ):
                _compare_object_lists_by_key(a, b, path, diffs,
                                             ignore_array_order, object_list_key)
            else:
                _compare_lists_unordered(a, b, path, diffs)
        else:
            _compare_lists_ordered(a, b, path, diffs,
                                   ignore_array_order, object_list_key)

    # primitivos o tipos distintos
    else:
        if type(a) is not type(b):
            diffs.append(
                f"{path}: type mismatch {type(a).__name__} vs {type(b).__name__} "
                f"({a!r} vs {b!r})"
            )
        elif a != b:
            diffs.append(f"{path}: value mismatch {a!r} vs {b!r}")


def _compare_lists_ordered(a: List[Any], b: List[Any], path: str,
                           diffs: List[str],
                           ignore_array_order: bool,
                           object_list_key: str | None):
    max_len = max(len(a), len(b))
    for i in range(max_len):
        new_path = f"{path}[{i}]"
        if i >= len(a):
            diffs.append(f"{new_path}: missing in first JSON, second has {b[i]!r}")
        elif i >= len(b):
            diffs.append(f"{new_path}: first JSON has {a[i]!r}, missing in second JSON")
        else:
            _compare(a[i], b[i], new_path, diffs,
                     ignore_array_order, object_list_key)


def _compare_lists_unordered(a: List[Any], b: List[Any], path: str,
                             diffs: List[str]):
    """Compare lists as multisets (order-insensitive, count-sensitive)."""
    def canon(x: Any) -> str:
        return json.dumps(x, sort_keys=True, ensure_ascii=False)

    ca = Counter(canon(x) for x in a)
    cb = Counter(canon(x) for x in b)

    all_items = set(ca.keys()) | set(cb.keys())
    for key in sorted(all_items):
        na, nb = ca.get(key, 0), cb.get(key, 0)
        if na != nb:
            item = json.loads(key)
            diffs.append(
                f"{path}: element {item!r} count mismatch {na} vs {nb}"
            )


def _compare_object_lists_by_key(a: List[Dict], b: List[Dict], path: str,
                                 diffs: List[str],
                                 ignore_array_order: bool,
                                 key: str):
    """
    Compare lists of objects grouping by a key (e.g. "concepto").
    Treat the list as a dict {concepto -> object}.
    """
    map_a = {item[key]: item for item in a}
    map_b = {item[key]: item for item in b}

    all_keys = set(map_a.keys()) | set(map_b.keys())
    for k in sorted(all_keys):
        new_path = f"{path}[{key}={k}]"
        if k not in map_a:
            diffs.append(f"{new_path}: missing in first JSON")
        elif k not in map_b:
            diffs.append(f"{new_path}: missing in second JSON")
        else:
            _compare(map_a[k], map_b[k], new_path, diffs,
                     ignore_array_order, key)




