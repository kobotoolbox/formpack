from typing import Callable, Any

from formpack.schema import FormField

# Basic recursive depth-first traversal
def dft_recurse(
    root: FormField,
    tree: dict[str, list[FormField]],
    process_field: Callable[[FormField], Any]
):
    seen = set()
    result = [root]
    seen.add(root.path)
    for child in tree[root.path]:
        dft_recurse_inner(child, tree, process_field, result, seen)
    return result

def dft_recurse_inner(
    root: FormField,
    tree: dict[str, list[FormField]],
    process_field: Callable[[FormField], Any],
    result: list[Any],
    seen: set[str]
):
    if root.path in seen:
        return
    result.append(process_field(root))
    seen.add(root.path)
    for child in tree[root.path]:
        dft_recurse_inner(child, tree, process_field, result, seen)
