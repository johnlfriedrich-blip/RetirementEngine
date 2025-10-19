import multiprocessing

try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    # This can happen if set_start_method is called multiple times,
    # e.g., in interactive environments or when tests are run in a specific way.
    # We can safely ignore it if it's already set.
    pass
