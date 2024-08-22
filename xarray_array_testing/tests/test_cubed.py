from typing import ContextManager
from contextlib import nullcontext

import pytest
import hypothesis.strategies as st
from hypothesis import note
import numpy as np
import numpy.testing as npt

from xarray_array_testing.base import DuckArrayTestMixin
from xarray_array_testing.creation import CreationTests
from xarray_array_testing.reduction import ReductionTests

import cubed
import cubed.random


def cubed_random_array(shape: tuple[int], dtype: np.dtype) -> cubed.Array:
    """
    Generates a random cubed array
    
    Supports integer and float dtypes.
    """
    # TODO hypothesis doesn't like us using random inside strategies
    rng = np.random.default_rng()
    
    if np.issubdtype(dtype, np.integer):
        arr = rng.integers(low=0, high=+3, size=shape, dtype=dtype)
        return cubed.from_array(arr)
    else:
        # TODO generate general chunking pattern
        ca = cubed.random.random(size=shape, chunks=shape)
        return cubed.array_api.astype(ca, dtype)


def random_cubed_arrays_fn(
    *, shape: tuple[int, ...], dtype: np.dtype,
) -> st.SearchStrategy[cubed.Array]:
    return st.builds(cubed_random_array, shape=st.just(shape), dtype=st.just(dtype))


class CubedTestMixin(DuckArrayTestMixin):
    @property
    def xp(self) -> type[cubed.array_api]:
        return cubed.array_api

    @property
    def array_type(self) -> type[cubed.Array]:
        return cubed.Array

    @staticmethod
    def array_strategy_fn(*, shape, dtype) -> st.SearchStrategy[cubed.Array]:
        return random_cubed_arrays_fn(shape=shape, dtype=dtype)

    @staticmethod
    def assert_equal(a: cubed.Array, b: cubed.Array):
        npt.assert_equal(a.compute(), b.compute())



class TestCreationCubed(CreationTests, CubedTestMixin):
    pass


class TestReductionCubed(ReductionTests, CubedTestMixin):
    @staticmethod
    def expected_errors(op, **parameters) -> ContextManager:
        var = parameters.get('variable')

        note(f"op = {op}")
        note(f"dtype = {var.dtype}")
        note(f"is_integer = {cubed.array_api.isdtype(var.dtype, 'integral')}")

        if op == 'mean' and cubed.array_api.isdtype(var.dtype, "integral") or var.dtype == np.dtype('float16'):
            return pytest.raises(TypeError, match='Only real floating-point dtypes are allowed in mean')
        else:
            return nullcontext()
