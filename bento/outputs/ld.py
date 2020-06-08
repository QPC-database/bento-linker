from .. import outputs
from ..box import Memory
import io
import textwrap
import itertools as it
import collections as co

@outputs.output
class LDOutput(outputs.Output):
    """
    Name of file to target for a linkerscript.
    """
    __argname__ = "ld"
    __arghelp__ = __doc__
    @classmethod
    def __argparse__(cls, parser, **kwargs):
        outputs.Output.__argparse__(parser, **kwargs)
        parser.add_argument('--emit_sections', type=bool,
            help='Enable/disable linker sections, not emitting sections '
                'makes it possible to include the generated linkerscript '
                'in a custom linkerscript.')
        defineparser = parser.add_set('--define')
        defineparser.add_argument('define',
            help='Add custom symbols to the linkerscript. For example: '
                '--define.__HeapLimit=__heap_end.')

    def __init__(self, path=None, emit_sections=None, define={}):
        super().__init__(path)
        self.emit_sections = (
            emit_sections if emit_sections is not None else True)
        self._defines = co.OrderedDict(sorted(
            (k, getattr(v, 'define', v)) for k, v in define.items()))

        def buildmemory(out, memory):
            out.pushattrs(
                prefix=out.get('prefix', ''),
                memory='%(prefix)s' + memory.name,
                mode=''.join(sorted(memory.mode)),
                addr=memory.addr,
                size=memory.size)
            out.writef('%(MEMORY)-16s (%(MODE)-3s) : '
                'ORIGIN = %(addr)#010x, '
                'LENGTH = %(size)#010x')

        self.decls = outputs.OutputField(self)
        self.memories = outputs.OutputField(self, {Memory: buildmemory},
            indent=4,
            memory=None,
            mode='rwx',
            addr=0,
            size=0)
        self.sections = outputs.OutputField(self,
            indent=4,
            section=None,
            memory=None,
            align=4)

    def default_build_parent(self, parent, box):
        # create memories + sections for subboxes?
        for memory in box.memories:
            self.memories.append(memory, prefix='box_%(box)s_')

            if self.emit_sections:
                out = self.sections.append(
                    section='.box.%(box)s.' + memory.name,
                    memory='box_%(box)s_' + memory.name,
                    noload='(NOLOAD)'*('w' in memory.mode))
                out.printf('%(section)s %(noload)s: {')
                with out.pushindent():
                    out.printf('__%(memory)s_start = .;')
                    out.printf('KEEP(*(%(section)s*))')
                out.printf('} > %(MEMORY)s')
                out.printf('. = ORIGIN(%(MEMORY)s) + '
                    'LENGTH(%(MEMORY)s);')
                out.printf('__%(memory)s_end = .;')

    def default_build_box(self, box):
        if self._defines:
            out = self.decls.append(doc='User defined symbols')
            for k, v in self._defines.items():
                out.write('%-16s = %s;' % (k, v))

        for memory in box.memoryslices:
            self.memories.append(memory)

        # The rest of this only deals with sections
        if not self.emit_sections:
            return

        constants = self.decls.append(doc='overridable constants')

        out = self.sections.append(
            section='.text',
            memory=box.text.memory.name)
        out.printf('%(section)s : {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__text_start = .;')
            out.printf('*(.text*)')
            out.printf('*(.rodata*)')
            out.printf('*(.glue_7*)')
            out.printf('*(.glue_7t*)')
            out.printf('*(.eh_frame*)')
            out.printf()
            out.printf('KEEP(*(SORT_NONE(.init)))')
            out.printf('KEEP(*(SORT_NONE(.init*)))')
            out.printf('KEEP(*(SORT_NONE(.fini)))')
            out.printf('KEEP(*(SORT_NONE(.fini*)))')
            out.printf()
            out.printf('. = ALIGN(4);')
            out.printf('PROVIDE_HIDDEN(__preinit_array_start = .);')
            out.printf('KEEP(*(SORT(.preinit_array)))')
            out.printf('PROVIDE_HIDDEN(__preinit_array_end = .);')
            out.printf()
            out.printf('. = ALIGN(4);')
            out.printf('PROVIDE_HIDDEN(__init_array_start = .);')
            out.printf('KEEP(*(SORT(.init_array.*)))')
            out.printf('PROVIDE_HIDDEN(__init_array_end = .);')
            out.printf()
            out.printf('. = ALIGN(4);')
            out.printf('PROVIDE_HIDDEN(__fini_array_start = .);')
            out.printf('KEEP(*(SORT(.fini_array.*)))')
            out.printf('PROVIDE_HIDDEN(__fini_array_end = .);')
            out.printf()
            out.printf('KEEP(*crtbegin.o(.ctors))')
            out.printf('KEEP(*crtbegin?.o(.ctors))')
            out.printf('KEEP(*(EXCLUDE_FILE(*crtend?.o *crtend.o) .ctors))')
            out.printf('KEEP(*(SORT(.ctors.*)))')
            out.printf()
            out.printf('KEEP(*crtbegin.o(.dtors))')
            out.printf('KEEP(*crtbegin?.o(.dtors))')
            out.printf('KEEP(*(EXCLUDE_FILE(*crtend?.o *crtend.o) .dtors))')
            out.printf('KEEP(*(SORT(.dtors.*)))')
            out.printf()
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__text_end = .;')
        out.printf('} > %(MEMORY)s')
        out.printf()
        out.printf('.ARM.extab : {')
        with out.indent():
            out.printf('*(.ARM.extab* .gnu.linkonce.armextab.*)')
        out.printf('} > %(MEMORY)s')
        out.printf()
        out.printf('.ARM.exidx : {')
        with out.indent():
            out.printf('__exidx_start = .;')
            out.printf('*(.ARM.exidx* .gnu.linkonce.armexidx.*)')
            out.printf('__exidx_end = .;')
        out.printf('} > %(MEMORY)s')
        out.printf()
        out.printf('__data_init_start = .;')

        # write out ram sections
        if box.stack:
            constants.printf('%(symbol)-16s = DEFINED(%(symbol)s) '
                '? %(symbol)s : %(value)#010x;',
                symbol='__stack_min',
                value=box.stack.size)
            out = self.sections.append(
                section='.stack',
                memory=box.stack.memory.name)
            out.printf('%(section)s (NOLOAD) : {')
            with out.pushindent():
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__stack_start = .;')
            out.printf('} > %(MEMORY)s')
            out.printf('. += __stack_min;')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__stack_end = .;')

        out = self.sections.append(
            section='.data',
            memory=box.data.memory.name,
            initmemory=box.text.memory.name)
        out.printf('%(section)s : AT(__data_init_start) {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__data_start = .;')
            out.printf('*(.data*)')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__data_end = .;')
        out.printf('} > %(MEMORY)s')
        out.printf()
        out.printf('__data_init_end = '
            'LOADADDR(%(section)s) + SIZEOF(%(section)s);')
        out.printf('ASSERT(__data_init_end <= '
            'ORIGIN(%(INITMEMORY)s) + LENGTH(%(INITMEMORY)s),')
        out.printf('    "Not enough memory in %(INITMEMORY)s for data")')

        out = self.sections.append(
            section='.bss',
            memory=box.bss.memory.name)
        out.printf('%(section)s (NOLOAD) : {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__bss_start = .;')
            out.printf('__bss_start__ = .;')
            out.printf('*(.bss*)')
            out.printf('*(COMMON)')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__bss_end = .;')
            out.printf('__bss_end__ = .;')
        out.printf('} > %(MEMORY)s')

        if box.heap:
            constants.printf('%(symbol)-16s = DEFINED(%(symbol)s) '
                '? %(symbol)s : %(value)#010x;',
                symbol='__heap_min',
                value=box.heap.size)
            out = self.sections.append(
                section='.heap',
                memory=box.heap.memory.name)
            out.printf('%(section)s (NOLOAD) : {')
            with out.pushindent():
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__end__ = .;')
                out.printf('PROVIDE(end = .);')
                out.printf('__heap_start = .;')
            out.printf('} > %(MEMORY)s')
            out.printf('. += ORIGIN(%(MEMORY)s) + LENGTH(%(MEMORY)s);')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__heap_end = .;')
            out.printf('__heap_limit = .;')
            out.printf()
            out.printf('ASSERT(__heap_end - __heap_start > __heap_min,')
            out.printf('    "Not enough memory in %(MEMORY)s for heap")')

    def build(self, box):
        self.printf('/***** AUTOGENERATED *****/')
        self.printf()

        if self.decls:
            for decl in self.decls:
                if 'doc' in decl:
                    for line in textwrap.wrap(decl['doc'], width=71):
                        self.print('/* %s */' % line)
                self.print(decl.getvalue().strip())
                self.print()

        if self.memories:
            self.print('MEMORY {')
            # order memories based on address
            for memory in sorted(self.memories, key=lambda m: m['addr']):
                if memory['mode']:
                    if 'doc' in memory:
                        for line in textwrap.wrap(
                                memory['doc'], width=78-10):
                            self.print(4*' ' + '/* %s */' % line)
                    self.print(4*' ' + memory.getvalue().strip())
            self.print('}')
            self.print('')

        assert self.emit_sections or not self.sections
        if self.sections:
            self.print('SECTIONS {')
            # order sections based on memories' address
            sections = self.sections
            i = 0
            for memory in sorted(self.memories, key=lambda m: m['addr']):
                if any(section['memory'] == memory['memory']
                        for section in sections):
                    self.print(4*' ' + '/* %s sections */'
                        % memory['memory'].upper())
                nsections = []
                for section in sections:
                    if section['memory'] == memory['memory']:
                        if 'doc' in section:
                            for line in textwrap.wrap(
                                    section['doc'], width=78-10):
                                self.print(4*' ' + '/* %s */' % line)
                        self.print(4*' ' + section.getvalue().strip())
                        if i < len(self.sections)-1:
                            self.print()
                            i += 1
                    else:
                        nsections.append(section)
                sections = nsections
            # write any sections without a valid memory?
            if sections:
                self.print(4*' ' + '/* misc sections */')
                for section in sections:
                    if 'doc' in section:
                        for line in textwrap.wrap(
                                section['doc'], width=78-10):
                            self.print(4*' ' + '/* %s */' % line)
                    self.print(4*' ' + section.getvalue().strip())
                    if i < len(self.sections)-1:
                        self.print()
                        i += 1
            self.print('}')
            self.print()

