import os
import builtins
import collections as c
import itertools as it
import string

RUNTIMES = c.OrderedDict()
def runtime(cls):
    assert cls.__argname__ not in RUNTIMES
    RUNTIMES[cls.__argname__] = cls
    return cls

class Runtime:
    """A bento-box runtime."""
    __argname__ = "runtime"
    __arghelp__ = __doc__

    def __init__(self):
        self.name = self.__argname__

    def __lt__(self, other):
        return self.name < other.name

    def box(self, box):
        pass
#        for name, output in box.outputs.items():
#            if not hasattr(self, 'build_' + output.name):
#                if hasattr(output, 'default_build'):
#                    setattr(self, 'build_' + output.name,
#                        output.default_build)
#                else:
#                    setattr(self, 'build_' + output.name,
#                        lambda output, *args, **kwargs: None)
#
#        parent = box.getparent()
#        if parent:
#            for name, output in parent.outputs.items():
#                if not hasattr(self, 'build_parent_' + output.name):
#                    if hasattr(output, 'default_build'):
#                        setattr(self, 'build_parent_' + output.name,
#                            output.default_build)
#                    else:
#                        setattr(self, 'build_parent_' + output.name,
#                            lambda output, *args, **kwargs: None)
#
#        root = box.getroot()
#        if root:
#            for name, output in root.outputs.items():
#                if not hasattr(self, 'build_root_' + output.name):
#                    if hasattr(output, 'default_build'):
#                        setattr(self, 'build_root_' + output.name,
#                            output.default_build)
#                    else:
#                        setattr(self, 'build_root_' + output.name,
#                            lambda output, *args, **kwargs: None)
    



#    def __getattr__(self, name):
#        # intercept build_* calls, dynamically provide defaults
#        if name.startswith('build_root_'):
#            def build(output, *args, **kwargs):
#                if output and hasattr(output, 'default_build_root'):
#                    return output.default_build_root(*args, **kwargs)
#            return build
#
#        if name.startswith('build_parent_'):
#            def build(output, *args, **kwargs):
#                if output and hasattr(output, 'default_build_parent'):
#                    return output.default_build_parent(*args, **kwargs)
#            return build
#
#        if name.startswith('build_'):
#            def build(output, *args, **kwargs):
#                if output and hasattr(output, 'default_build'):
#                    return output.default_build_parent(*args, **kwargs)
#            return build
#
#
#
#        if name.startswith('build_'):
#            def build(output, *args, **kwargs):
#                nname = 'default_' + name[:-len(output.name)-1]
#                print(nname)
#                if output and hasattr(output, nname):
#                    return getattr(output, nname)(*args, **kwargs)
#            return build
#
#        return super().__getattr__(name)

    def build(self, box):
        root = box.getroot()
        if root:
            for name, output in root.outputs.items():
                with output.pushattrs(root=root.name, box=box.name):
                    getattr(self, 'build_root_' + name)(output, root, box)

        parent = box.getparent()
        if parent:
            for name, output in parent.outputs.items():
                with output.pushattrs(parent=parent.name, box=box.name):
                    getattr(self, 'build_parent_' + name)(output, parent, box)

        for name, output in box.outputs.items():
                getattr(self, 'build_' + name)(output, box)

# if build rule doesn't exist, fall back to output defaults, or noop
from ..outputs import OUTPUTS
for Output in OUTPUTS['box'].values():
    if hasattr(Output, 'default_build_root'):
        setattr(Runtime, 'build_root_' + Output.__argname__,
            lambda self, output, *args, **kwargs:
                output.default_build_root(*args, **kwargs))
    else:
        setattr(Runtime, 'build_root_' + Output.__argname__,
            lambda self, output, *args, **kwargs: None)

    if hasattr(Output, 'default_build_parent'):
        setattr(Runtime, 'build_parent_' + Output.__argname__,
            lambda self, output, *args, **kwargs:
                output.default_build_parent(*args, **kwargs))
    else:
        setattr(Runtime, 'build_parent_' + Output.__argname__,
            lambda self, output, *args, **kwargs: None)

    if hasattr(Output, 'default_build'):
        setattr(Runtime, 'build_' + Output.__argname__,
            lambda self, output, *args, **kwargs:
                output.default_build(*args, **kwargs))
    else:
        setattr(Runtime, 'build_' + Output.__argname__,
            lambda self, output, *args, **kwargs: None)


# Runtime class imports
# These must be imported here, since they depend on the above utilities
from .mpu_protect import MPUProtectRuntime
from .noop import NoOpRuntime
from .wasm3 import Wasm3Runtime
