#
# C header/source file outputer
# 
# Copyright (c) 2020, Arm Limited. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
#
from .. import outputs
from ..box import Fn
import io
import textwrap
import itertools as it

@outputs.output
class HOutput(outputs.Output):
    """
    Name of header file to generate containing the imported functions.
    """
    __argname__ = "h"
    __arghelp__ = __doc__

    def __init__(self, path=None):
        super().__init__(path)

        self.includes = outputs.OutputField(self)
        self.decls = outputs.OutputField(self)

    @staticmethod
    def repr_arg(arg, name=None):
        name = name if name is not None else arg.name
        return ''.join([
            'const ' if arg.isconst() else '',
            'void'      if arg.prim() == 'u8' and arg.isptr() else
            'char'      if arg.prim() == 'i8' and arg.isptr() else
            'bool'      if arg.prim() == 'bool' else
            'int32_t'   if arg.prim() == 'err32' else
            'int64_t'   if arg.prim() == 'err64' else
            'ssize_t'   if arg.prim() == 'errsize' else
            'int'       if arg.prim().startswith('err') else
            'ssize_t'   if arg.prim() == 'isize' else
            'size_t'    if arg.prim() == 'usize' else
            'int%s_t'  % arg.prim()[1:] if arg.prim().startswith('i') else
            'uint%s_t' % arg.prim()[1:] if arg.prim().startswith('u') else
            'float'     if arg.prim() == 'f32' else
            'double'    if arg.prim() == 'f64' else
            '???',
            ' ' if name else '',
            '*' if arg.isptr() else '',
            name if name else ''])

    @staticmethod
    def repr_fn(fn, name=None, attrs=[]):
        return ''.join(it.chain(
            (attr + ('\n' if attr.startswith('__') else ' ')
                for attr in it.chain(
                    (['__attribute__((noreturn))']
                        if fn.isnoreturn() and (
                            name is None or '*' not in name) else
                        []) +
                    attrs)), [
            '%s ' % HOutput.repr_arg(fn.rets[0], '') if fn.rets else
            'void ',
            name if name is not None else fn.alias,
            '(',
            ', '.join(HOutput.repr_arg(arg, name)
                for arg, name in zip(fn.args, fn.argnames()))
            if fn.args else
            'void',
            ')']))

    @staticmethod
    def repr_fnptr(fn, name=None, attrs=[]):
        return HOutput.repr_fn(fn,
            '(*%s)' % (name if name is not None else fn.alias),
            attrs)

    def box(self, box):
        super().box(box)
        self.pushattrs(gaurd='__BOX_%(BOX)s_H')

    # overridable
    def _build_imports(self, box):
        for i, import_ in enumerate(
                import_.postbound() for import_ in box.imports
                if import_.source == box):
            if i == 0:
                self.decls.append('//// box imports ////')
            self.decls.append('%(fn)s;',
                fn=self.repr_fn(import_),
                doc=import_.doc)

    # overridable
    def _build_exports(self, box):
        for i, export in enumerate(
                export.prebound() for export in box.exports
                if export.source == box):
            if i == 0:
                self.decls.append('//// box exports ////')
            self.decls.append('%(fn)s;',
                fn=self.repr_fn(export, attrs=['extern']),
                doc=export.doc)

    def build_prologue(self, box):
        # always need standard types
        self.includes.append("<stdint.h>")
        self.includes.append("<stdbool.h>")
        self.includes.append("<sys/types.h>")

        # imports/exports declared here
        self._build_imports(box)
        self._build_exports(box)

        # functions we can expect from runtimes
        if box.boxes:
            self.decls.append('//// box hooks ////')
        for subbox in box.boxes:
            with self.pushattrs(box=subbox.name):
                self.decls.append(
                    'int __box_%(box)s_init(void);',
                    doc='Initialize box %(box)s. Resets the box to its '
                        'initial state if already initialized.')
                self.decls.append(
                    'int __box_%(box)s_clobber(void);',
                    doc='Mark the box %(box)s as needing to be reinitialized.')
                self.decls.append(
                    'void *__box_%(box)s_push(size_t size);',
                    doc='Allocate size bytes on the box\'s data stack. May '
                        'return NULL if a stack overflow would occur.')
                self.decls.append(
                    'void __box_%(box)s_pop(size_t size);',
                    doc='Deallocate size bytes on the box\'s data stack.')

    def getvalue(self):
        self.seek(0)
        self.printf('////// AUTOGENERATED //////')
        self.printf('#ifndef %(gaurd)s')
        self.printf('#define %(gaurd)s')

        includes = set()
        for include in self.includes:
            include = str(include)
            if not (include.startswith('"') or include.startswith('<')):
                include = '"%s"' % include
            includes.add(include)
        for include in sorted(includes):
            self.printf('#include %(include)s', include=include)

        self.print()

        for decl in self.decls:
            if 'doc' in decl:
                for line in textwrap.wrap(decl['doc'], width=78-3):
                    self.print('// %s' % line)
            self.print(decl.getvalue().strip())
            self.print()

        self.printf('#endif')

        return super().getvalue()


@outputs.output
class COutput(HOutput):
    """
    Name of C file to target for building a jumptable.
    """
    __argname__ = "c"
    __arghelp__ = __doc__
    @classmethod
    def __argparse__(cls, parser, **kwargs):
        super().__argparse__(parser, **kwargs)
        parser.add_argument('--no_stdlib_hooks', type=bool,
            help='Enable/disable the stdlib hooks that connect box hooks to '
                'the C standard library.')
        parser.add_argument('--printf', choices=['minimal', 'std'],
            help='Select the printf implementation to use in the '
                'box. By default, boxes provide a non-standard minimal '
                'printf to reduce a code cost that is duplicated across boxes '
                'If this isn\'t wanted, --printf=std provides the printf found '
                'in the stdlib. Can be one of the following: {%(choices)s}. '
                'Defaults to minimal.')

    def __init__(self, path, no_stdlib_hooks=None, printf=None):
        super().__init__(path)
        self.no_stdlib_hooks = no_stdlib_hooks or False
        self.printf_impl = printf if printf is not None else 'minimal'

    def getvalue(self):
        self.seek(0)
        self.printf('////// AUTOGENERATED //////')

        includes = set()
        for include in self.includes:
            include = str(include)
            if not (include.startswith('"') or include.startswith('<')):
                include = '"%s"' % include
            includes.add(include)
        out = self.decls.insert(0)
        for include in sorted(includes):
            out.print('#include %s' % include)

        for decl in self.decls:
            if 'doc' in decl:
                for line in textwrap.wrap(decl['doc'], width=78-3):
                    self.print('// %s' % line)
            self.print(decl.getvalue().strip())
            self.print()

        return outputs.Output.getvalue(self)
