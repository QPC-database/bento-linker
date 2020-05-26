from .. import outputs
from ..box import Memory
import io
import textwrap
import itertools as it

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

@outputs.output
class PartialLDOutput(outputs.Output):
    """
    Name of file to target for a partial linkerscript. This is the minimal
    additions needed for a bento box and should be imported into a traditional
    linkerscript to handle the normal program sections.
    """
    __argname__ = "partial_ld"
    __arghelp__ = __doc__

    def __init__(self, path=None):
        super().__init__(path)
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

            out = self.sections.append(
                section='.box.%(box)s.' + memory.name,
                memory='box_%(box)s_' + memory.name)
            out.printf('%(section)s : {')
            with out.pushindent():
                out.printf('__%(memory)s = .;')
                out.printf('KEEP(*(%(section)s*))')
                out.printf('. = ORIGIN(%(MEMORY)s) + '
                    'LENGTH(%(MEMORY)s);')
                out.printf('__%(memory)s_end = .;')
            out.printf('} > %(MEMORY)s')

    def build(self, box):
        # TODO docs?
        self.write('/***** AUTOGENERATED *****/\n')
        self.write('\n')
        if self.decls:
            for decl in self.decls:
                if 'doc' in decl:
                    for line in textwrap.wrap(decl['doc'], width=72):
                        self.write('/* %s */\n' % line)
                self.write(decl.getvalue().strip())
                self.write('\n\n')
        if self.memories:
            self.write('MEMORY {\n')
            # order memories based on address
            for memory in sorted(self.memories, key=lambda m: m['addr']):
                if memory['mode']:
                    if 'doc' in memory:
                        for line in textwrap.wrap(memory['doc'], width=68):
                            self.write(4*' '+'/* %s */\n' % line)
                    self.write(4*' ')
                    self.write(memory.getvalue().strip())
                    self.write('\n')
            self.write('}\n')
            self.write('\n')
        if self.sections:
            self.write('SECTIONS {\n')
            # order sections based on memories' address
            sections = self.sections
            for memory in sorted(self.memories, key=lambda m: m['addr']):
                if any(section['memory'] == memory['memory']
                        for section in sections):
                    self.write('    /* %s sections */\n'
                        % memory['memory'].upper())
                nsections = []
                for section in sections:
                    if section['memory'] == memory['memory']:
                        if 'doc' in section:
                            for line in textwrap.wrap(section['doc'],
                                    width=68):
                                self.write(4*' '+'/* %s */\n' % line)
                        self.write(4*' ')
                        self.write(section.getvalue().strip())
                        self.write('\n\n')
                    else:
                        nsections.append(section)
                sections = nsections
            # write any sections without a valid memory?
            if sections:
                self.write('    /* misc sections */\n')
                for section in sections:
                    if 'doc' in section:
                        for line in textwrap.wrap(section['doc'],
                                width=68):
                            self.write(4*' '+'/* %s */\n' % line)
                    self.write(4*' ')
                    self.write(section.getvalue().strip())
                    self.write('\n\n')
            self.write('}\n')
            self.write('\n')

@outputs.output
class LDOutput(PartialLDOutput):
    """
    Name of file to target for the linkerscript.
    """
    __argname__ = "ld"
    __arghelp__ = __doc__

    def default_build_box(self, box):
        for memory in box.memories:
            for slice in memory - it.chain.from_iterable(
                    subbox.memories for subbox in box.boxes):
                self.memories.append(slice)

        if box.issys():
            self.decls.insert(0, 'ENTRY(Reset_Handler)')
        constants = self.decls.append(doc='overridable constants')

        # write out rom sections
        # need interrupt vector?
        if box.issys() and box.isr_vector:
            memory, _, _ = box.consume('rx', section=box.isr_vector)
            constants.printf('%(symbol)-24s = DEFINED(%(symbol)s) '
                '? %(symbol)s \n%()24s : %(value)#010x;',
                symbol='__isr_vector_min',
                value=box.isr_vector.size)
            out = self.sections.append(
                section='.isr_vector',
                memory=memory.name)
            out.printf('.isr_vector : {')
            with out.pushindent():
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__isr_vector = .;')
                out.printf('KEEP(*(.isr_vector))')
                out.printf('. = __isr_vector +'
                    '__isr_vector_min;')
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__isr_vector_end = .;')
            out.printf('} > %(MEMORY)s')

        memory, _, _ = box.consume('rx', section=box.text)
        out = self.sections.append(
            section='.text',
            memory=memory.name)
        out.printf('%(section)s : {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__text = .;')
            out.printf('*(.text*)')
            out.printf('*(.rodata*)')
            out.printf('*(.glue_7*)')
            out.printf('*(.glue_7t*)')
            out.printf('*(.eh_frame*)')
            out.printf('KEEP(*(.init*))')
            out.printf('KEEP(*(.fini*))') # TODO oh boy there's a lot of other things
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__text_end = .;')
            out.printf('__data_init = .;')
        out.printf('} > %(MEMORY)s')

        # write out ram sections
        if box.stack:
            memory, _, _ = box.consume('rw', section=box.stack)
            constants.printf('%(symbol)-24s = DEFINED(%(symbol)s) '
                '? %(symbol)s \n%()24s : %(value)#010x;',
                symbol='__stack_min',
                value=box.stack.size)
            out = self.sections.append(
                section='.stack',
                memory=memory.name)
            out.printf('%(section)s (NOLOAD) : {')
            with out.pushindent():
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__stack = .;')
                out.printf('. += __stack_min;')
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__stack_end = .;')
            out.printf('} > %(MEMORY)s')

        memory, _, _ = box.consume('rw', section=box.data)
        out = self.sections.append(
            section='.data',
            memory=memory.name)
        out.printf('%(section)s : AT(__data_init) {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__data = .;')
            out.printf('*(.data*)')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__data_end = .;')
        out.printf('} > %(MEMORY)s')

        memory, _, _ = box.consume('rw', section=box.bss)
        out = self.sections.append(
            section='.bss',
            memory=memory.name)
        out.printf('%(section)s (NOLOAD) : {')
        with out.pushindent():
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__bss = .;')
            # TODO hm
            out.printf('__bss_start__ = .;')
            out.printf('*(.bss*)')
            out.printf('*(COMMON)')
            out.printf('. = ALIGN(%(align)d);')
            out.printf('__bss_end = .;')
            out.printf('__bss_end__ = .;')
        out.printf('} > %(MEMORY)s')

        if box.heap:
            memory, _, _ = box.consume('rw', section=box.heap)
            constants.printf('%(symbol)-24s = DEFINED(%(symbol)s) '
                '? %(symbol)s \n%()24s : %(value)#010x;',
                symbol='__heap_min',
                value=box.heap.size)
            out = self.sections.append(
                section='.heap',
                memory=memory.name)
            out.printf('%(section)s (NOLOAD) : {')
            with out.pushindent():
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__end__ = .;')
                out.printf('PROVIDE(end = .);')
                out.printf('__heap = .;')
                # TODO need all these?
                out.printf('__HeapBase = .;')
                out.printf('. += ORIGIN(%(MEMORY)s) + LENGTH(%(MEMORY)s);')
                out.printf('. = ALIGN(%(align)d);')
                out.printf('__heap_end = .;')
                # TODO need all these?
                out.printf('__HeapLimit = .;')
                out.printf('__heap_limit = .;')
            out.printf('} > %(MEMORY)s')
            out.printf('ASSERT(__heap_end - __heap > __heap_min,')
            out.printf('    "Not enough memory for heap")')
