from .. import outputs
from ..box import Fn
import io
import textwrap

#@outputs.output('sys')
#@outputs.output('box')
#class HeaderOutput(outputs.Output):
#    """
#    Name of header file to generate containing the imported functions.
#    """
#    __argname__ = "header_glue"
#    __arghelp__ = __doc__
#
#    def __init__(self, sys, box, path):
#        self._includes = []
#        self._decls = []
#        super().__init__(sys, box, path)
#
#        if box:
#            self.format(gaurd='__BOX_%s_H' % box.name.upper())
#        else:
#            self.format(gaurd='__BOX_H')
#
#    def append_include(self, fmt=None, **kwargs):
#        include = fmt % self.mkformat(**kwargs)
#        if not include.startswith('"') and not include.startswith('<'):
#            include = '"%s"' % include
#        if include not in self._includes:
#            self._includes.append(include)
#
#    def append_decl(self, fmt=None, **kwargs):
#        outf = self.mkfield(**kwargs)
#        self._decls.append(outf)
#        if fmt is not None:
#            outf.writef(fmt)
#        return outf
#
#    def build(self, outf):
#        outf.writef('////// AUTOGENERATED //////\n')
#        outf.writef('#ifndef %(gaurd)s\n' % self.mkformat())
#        outf.writef('#define %(gaurd)s\n' % self.mkformat())
#        for include in self._includes:
#            outf.writef('#include %s\n' % include)
#        outf.writef('\n')
#        for decl in self._decls:
#            outf.writef(decl.getvalue())
#            outf.writef('\n')
#        outf.writef('#endif\n')
#
def buildinclude(outf, include):
    if not (include.startswith('"') or include.startswith('<')):
        include = '"%s"' % include
    outf.writef(include)

def buildfn(outf, fn):
    if fn.doc:
        outf.pushattrs(doc=fn.doc)
    if outf.get('attrs', False):
        outf.writef('%(attrs)s ')
    outf.writef('%(fn)s;', fn=fn.repr_c())

@outputs.output('sys')
@outputs.output('box')
class HeaderGlueOutput_(outputs.Output_):
    """
    Name of header file to generate containing the imported functions.
    """
    __argname__ = "header_glue_"
    __arghelp__ = __doc__

    def __init__(self, path=None):
        super().__init__(path)
        self.includes = outputs.OutputField_(self, {str: buildinclude})
        self.decls = outputs.OutputField_(self, {Fn: buildfn})

    def box(self, box):
        super().box(box)
        self.pushattrs(gaurd='__BOX_%(BOX)s_H' if box.isbox() else '__BOX_H')

        # always need standard types
        self.includes.append("<sys/types.h>")

        # TODO always have this?
        if box.boxes:
            self.decls.append('//// box hooks ////')
            for subbox in box.boxes:
                with self.pushattrs(box=subbox.name):
                    self.decls.append(
                        'void __box_%(box)s_init(void);',
                        doc='box %(box)s initialization')
                    # TODO handle this differently?
                    # TODO use setter?
                    # TODO expect export?
                    self.decls.append(
                        'extern void '
                        '__box_%(box)s_fault_handler(uint32_t addr);',
                        doc='function to call on bad address')
    #                    if box.imports:
    #                        self.decls.append('\n//// box %(box)s imports ////')
    #                    for import_ in box.imports:
    #                        self.decls.append('extern %(fn)s;',
    #                            fn=import_.repr_c(), doc=import_.doc)
    #                    if box.exports:
    #                        self.decls.append('\n//// box %(box)s exports ////')
    #                    for export in box.exports:
    #                        self.decls.append('%(fn)s;',
    #                            fn=export.repr_c(), doc=export.doc)

        if box.imports:
            self.decls.append('//// box imports ////')
            for import_ in box.imports:
                self.decls.append(import_)
        if box.exports:
            self.decls.append('//// box exports ////')
            for export in box.exports:
                self.decls.append(export, attrs='extern')

    def build(self, box):
        self.write('////// AUTOGENERATED //////\n')
        self.write('#ifndef %(gaurd)s\n' % self)
        self.write('#define %(gaurd)s\n' % self)
        includes = set()
        for include in self.includes:
            includes.add(include.getvalue())
        for include in sorted(includes):
            self.write('#include %s\n' % include)
        self.write('\n')

        for decl in self.decls:
            if decl.getvalue().startswith(4*'/'):
                self.write('\n')
            if decl.get('doc', None) is not None:
                for line in textwrap.wrap(decl['doc'] % decl, width=77):
                    self.write('// %s\n' % line)
            self.write(decl.getvalue().strip())
            self.write('\n\n')

        self.write('\n')
        self.write('#endif\n')
    
