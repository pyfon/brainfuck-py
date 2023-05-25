#!/usr/bin/env python3

import argparse
import sys

class Tape:
    """ An infinite 1D array for memory & program store """
    def __init__(self, initial_tape_len=4096):
        self._storage = bytearray(initial_tape_len)
        self._ptr = 0

    def __iter__(self):
        return self

    def __next__(self):
        """ Iterates from ptr onwards """
        ret = self.cur_elem
        self.ptr += 1
        return ret

    @property
    def ptr(self):
        return self._ptr

    @ptr.setter
    def ptr(self, n):
        """ Move the ptr to <n>, ensuring tape is large enough """
        if n < 0:
            raise IndexError("Tried to set tape pointer < 0")
        self._ptr = n
        while len(self._storage) <= self._ptr:
            self._storage.extend(bytearray(len(self._storage) + 1))

    @property
    def cur_elem(self):
        """ The current element ptr points to """
        return self._storage[self.ptr]

    @cur_elem.setter
    def cur_elem(self, elem):
        self._storage[self.ptr] = elem % 256 # Byte wrapping

    def load(self, data):
        """ Load data into storage """
        self._storage = bytearray(data)
        self.ptr = 0

class BrainfuckSyntaxError(Exception):
    pass

class BfTuringMachine:
    def __init__(self):
        self._memory = Tape()
        self._program = Tape()
        self._bracket_stack = list()
        self._bf_cmds = {
            '>': lambda: self._shift_data_ptr(1),
            '<': lambda: self._shift_data_ptr(-1),
            '+': lambda: self._add_to_current_byte(1),
            '-': lambda: self._add_to_current_byte(-1),
            '.': self._current_byte_out,
            ',': self._read_byte_and_store,
            '[': self._left_bracket,
            ']': self._right_bracket,
        }

    def _shift_data_ptr(self, n):
        """ Shift data pointer by <n> """
        self._memory.ptr += n

    def _add_to_current_byte(self, n):
        """ Add <n> to the byte at the data pointer """
        self._memory.cur_elem += n

    def _current_byte_out(self):
        sys.stdout.buffer.write(self._memory.cur_elem.to_bytes(1, sys.byteorder))
        sys.stdout.buffer.flush()

    def _read_byte_and_store(self):
        char = sys.stdin.read(1)
        if len(char):
            self._memory.cur_elem = ord(char)
        else:
            # EOF, this interpreter sets the cell to 0.
            self._memory.cur_elem = 0

    def _left_bracket(self):
        self._bracket_stack.append(self._program.ptr)
        if self._memory.cur_elem != 0:
            return
        # Skip past matching ]
        self._bracket_stack.pop()
        nested_brackets = 0
        next(self._program) # Skip current [
        for cmd in self._program:
            if cmd not in b'[]':
                continue
            if cmd == ord('['):
                nested_brackets += 1
                continue
            # cmd is ]
            if nested_brackets:
                nested_brackets -= 1
                continue
            # Matching ] found.
            # Iteration has skipped past the ] already, rewind it
            # in anticipation of it being stepped for the next instruction.
            self._program.ptr -= 1
            return
        # We should've found a matching ] and returned. Panic!
        raise BrainfuckSyntaxError("Unmatched [")

    def _right_bracket(self):
        if not self._bracket_stack:
            raise BrainfuckSyntaxError("Unmatched ]")
        if self._memory.cur_elem == 0:
            self._bracket_stack.pop()
            return
        self._program.ptr = self._bracket_stack[-1]

    def load_program(self, program: str):
        to_load = bytearray()
        for c in program:
            if c not in self._bf_cmds.keys():
                continue
            to_load.append(ord(c))
        self._program.load(to_load)

    def start_program(self):
        while self._program.cur_elem != 0:
            self._bf_cmds[chr(self._program.cur_elem)]()
            self._program.ptr += 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "filename",
        nargs='?',
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Brainfuck Program File"
    )
    args = parser.parse_args()

    turing_machine = BfTuringMachine()
    try:
        turing_machine.load_program(args.filename.read())
        turing_machine.start_program()
    except BrainfuckSyntaxError as e:
        print(f"{args.filename.name}: Syntax Error: {e}")
    except IndexError as e:
        print(f"{args.filename.name}: Index Error: {e}")

if __name__ == '__main__':
    main()
