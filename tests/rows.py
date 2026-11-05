"""Die festen und frischen Instanzen der Vergleiche für test_claims.py, parallel gerechnet (ein Prozess je Kern, höchstens vier) und je Größe nur einmal.

Zeiten stehen in den Zeilen, aber nie in den Tests; die Parallelität ändert nur die gemessenen Sekunden."""

import multiprocessing
import os
from concurrent.futures import ProcessPoolExecutor

import avw_evaluation as E

_FIND: dict = {}
_PROVE: dict = {}


def _workers() -> int:
    return max(1, min(4, os.cpu_count() or 1))


def _find_job(job):
    return E.find_row(*job)


def _prove_job(job):
    return E.prove_row(*job)


def _map(fn, jobs):
    with ProcessPoolExecutor(max_workers=_workers(), mp_context=multiprocessing.get_context("spawn")) as ex:
        return list(ex.map(fn, jobs, chunksize=1))


def find_rows(n: int, fresh: bool = False) -> list:
    """Alle Zeilen der Größe `n` (feste oder frische Instanzen) in der Reihenfolge von `E.find_jobs`."""
    if (n, fresh) not in _FIND:
        _FIND[(n, fresh)] = _map(_find_job, E.find_jobs(n, fresh))
    return _FIND[(n, fresh)]


def prove_rows(n: int) -> list:
    if n not in _PROVE:
        import avw_constants as C

        jobs = [(f, n, s) for f in C.FAMILIES for s in range(C.FIXED_SEED0, C.FIXED_SEED0 + C.SEEDS_PROVE[n])]
        _PROVE[n] = _map(_prove_job, jobs)
    return _PROVE[n]
