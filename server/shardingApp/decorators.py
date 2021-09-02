import functools
import time
from typing import Callable


def timeit(func: Callable):
	''' 
	Decorator function that times a function call
	Stores last_time attribute as time taken to run

	Arguments
		func -- Function to run

	Returns
		Wrapped function
	'''
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		start = time.perf_counter()
		ret = func(*args, **kwargs)
		end = time.perf_counter()
		wrapper.last_time = end - start
		return ret
	wrapper.last_time = 0
	return wrapper


class classproperty(property):
	'''
	Decorator getter function for class attribute. Useful for forcing single point of truth

	Arguments
		cls -- Instance of caller
		owner -- Class of caller
	'''
	def __get__(self, cls, owner):
		return classmethod(self.fget).__get__(None, owner)()