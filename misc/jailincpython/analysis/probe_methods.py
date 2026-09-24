class Seed:
    pass


args = [False, None, Seed, {}, [], lambda: False, "%jailincpython", Seed | None]

for name in dir(Seed):
    try:
        function = getattr(Seed, name)
    except Exception:
        continue
    if not callable(function):
        continue
    for arg in args:
        class A:
            pass

        try:
            A.__class_getitem__ = function
            result = A[arg]
        except Exception:
            continue
        result_type = type(result).__name__
        if result_type not in {"bool", "int", "str", "NoneType", "NotImplementedType"}:
            rendered = repr(result)
            if len(rendered) > 180:
                rendered = rendered[:177] + "..."
            print(name, type(function).__name__, type(arg).__name__, result_type, rendered)
