import sys

from Cython.Build import cythonize
from setuptools import Extension, setup

if sys.platform == "win32":
  compile_args, link_args = ["/O2", "/openmp"], []
else:
  compile_args, link_args = ["-O3", "-fopenmp", "-ffast-math"], ["-fopenmp"]
  if sys.platform == "darwin":
    cc, ld = ["O3", "-ffast-math"], []

setup(
  ext_modules=cythonize(
    Extension(
      "rpc_solver",
      ["rpc_solver.pyx"],
      extra_compile_args=compile_args,
      extra_link_args=link_args,
    ),
    compiler_directives={"language_level": 3},
  )
)
