"""C14.4 opportunistic dispatch over already-authorized remote work."""
from .contracts import RemoteWorkManifest, invalid, text


def dispatch_eligible_work(
        manifests: tuple[RemoteWorkManifest, ...], *,
        available_workers: tuple[str, ...]) -> tuple[tuple[str, str], ...]:
    """Return deterministic assignments; an empty swarm never blocks local work."""
    if (type(manifests) is not tuple
            or any(type(item) is not RemoteWorkManifest for item in manifests)
            or type(available_workers) is not tuple
            or any(not text(worker) for worker in available_workers)):
        invalid("BAMF_C14_DISPATCH_INPUT_INVALID")
    if not available_workers:
        return ()
    workers = tuple(sorted(set(available_workers)))
    ordered = tuple(sorted(manifests, key=lambda item: item.digest))
    return tuple(
        (workers[index % len(workers)], manifest.digest)
        for index, manifest in enumerate(ordered))
