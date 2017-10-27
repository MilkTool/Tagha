#!/usr/bin/python3

import sys;
import ctypes;
import struct;

def enum(*sequential, **named) -> object:
	enums = dict(zip(sequential, range(len(sequential))), **named);
	return type('Enum', (), enums);

opcodes = enum('halt', 'pushq', 'pushl', 'pushs', 'pushb', 'pushsp', 'puship', 'pushbp', 'pushoffset', 'pushspadd', 'pushspsub', 'pushbpadd', 'pushbpsub', 'pushipadd', 'pushipsub', 'popq', 'popsp', 'popip', 'popbp', 'storespq', 'storespl', 'storesps', 'storespb', 'loadspq', 'loadspl', 'loadsps', 'loadspb', 'copyq', 'copyl', 'copys', 'copyb', 'addq', 'uaddq', 'addl', 'uaddl', 'addf', 'subq', 'usubq', 'subl', 'usubl', 'subf', 'mulq', 'umulq', 'mull', 'umull', 'mulf', 'divq', 'udivq', 'divl', 'udivl', 'divf', 'modq', 'umodq', 'modl', 'umodl', 'addf64', 'subf64', 'mulf64', 'divf64', 'andl', 'orl', 'xorl', 'notl', 'shll', 'shrl', 'andq', 'orq', 'xorq', 'notq', 'shlq', 'shrq', 'incq', 'incl', 'incf', 'decq', 'decl', 'decf', 'negq', 'negl', 'negf', 'incf64', 'decf64', 'negf64', 'ltq', 'ltl', 'ultq', 'ultl', 'ltf', 'gtq', 'gtl', 'ugtq', 'ugtl', 'gtf', 'cmpq', 'cmpl', 'ucmpq', 'ucmpl', 'compf', 'leqq', 'uleqq', 'leql', 'uleql', 'leqf', 'geqq', 'ugeqq', 'geql', 'ugeql', 'geqf', 'ltf64', 'gtf64', 'cmpf64', 'leqf64', 'geqf64', 'neqq', 'uneqq', 'neql', 'uneql', 'neqf', 'neqf64', 'jmp', 'jzq', 'jnzq', 'jzl', 'jnzl', 'call', 'calls', 'ret', 'retq', 'retl', 'rets', 'retb', 'reset', 'pushnataddr', 'callnat', 'callnats', 'nop');


g_dictLabels = {};


def is_potential_identifier(c:str) -> bool:
	return( (c >= 'a' and c <= 'z')
		or (c >= 'A' and c <= 'Z')
		or c == '_'
		or (c >= '0' and c <= '9')
		or c >= chr(255) );

def is_alphabetic(c:str) -> bool:
	return( (c >= 'a' and c <= 'z')
		or (c >= 'A' and c <= 'Z')
		or c == '_'
		or c >= chr(255) );

def is_whitespace(c:str) -> bool:
	return( c == '\t' or c == '\r' or c == '\v' or c == '\f' or c == '\n' );
	
def is_hex(c:str) -> bool:
	return( (c >= 'a' and c <= 'f') or (c >= 'A' and c <= 'F') or (c >= '0' and c <= '9') );

def is_octal(c:str) -> bool:
	return( c >= '0' and c <= '7' );

def is_numeric(c:str) -> bool:
	return( c >= '0' and c <= '9' );


def prep_file(filename:str) -> list:
	lstLines=[];
	with open(filename, 'r+') as objFile:
		strTok = "";
		for line in objFile.readlines():
			for char in line:
				if char==';':	# remove comments
					break;
				strTok += char;
			
			lstLines.append(strTok);
			strTok = "";
		
	return lstLines;


def asmlify(lines:list) -> list:
	iAddr=0;
	# first pass: resolve the label references.
	for line in lines:
		print(line);


def wrt_hdr(f, memsize:int) -> None:
	f.write(0xC0DE.to_bytes(2, byteorder='little'));
	f.write(memsize.to_bytes(4, byteorder='little'));

def wrt_hdr_natives(f, *natives) -> None:
	i = 0;
	numnatives = len(natives);
	f.write(numnatives.to_bytes(4, byteorder='little'));
	while i<numnatives:
		#f.write(natives[i].to_bytes(4, byteorder='little'));
		#print((len(natives[i])+1).to_bytes(4, byteorder='little'));
		f.write((len(natives[i])+1).to_bytes(4, byteorder='little'));
		f.write(natives[i].encode('utf-8'));
		f.write(0x0.to_bytes(1, byteorder='little'));
		i += 1;

def wrt_hdr_funcs(f, *funcs) -> None:
	i = 0;
	numfuncs = len(funcs) // 3;
	f.write(numfuncs.to_bytes(4, byteorder='little'));
	while i<numfuncs*3:
		strsize = len(funcs[i])+1;
		f.write(strsize.to_bytes(4, byteorder='little'));
		f.write(funcs[i].encode('utf-8'));
		f.write(0x0.to_bytes(1, byteorder='little'));
		i += 1;
		
		f.write(funcs[i].to_bytes(4, byteorder='little'));
		i += 1;
		
		f.write(funcs[i].to_bytes(4, byteorder='little'));
		i += 1;

def wrt_hdr_globals(f, *lGlobals) -> None:
	i = 0;
	numglobals = len(lGlobals) // 4;
	f.write(numglobals.to_bytes(4, byteorder='little'));
	
	while i<numglobals*4:
		strsize = len(lGlobals[i])+1;
		f.write(strsize.to_bytes(4, byteorder='little'));
		f.write(lGlobals[i].encode('utf-8'));
		f.write(0x0.to_bytes(1, byteorder='little'));
		i += 1;
		
		# write the stack address of this global var.
		f.write(lGlobals[i].to_bytes(4, byteorder='little'));
		i += 1;
		
		# write how many bytes this data takes up.
		bytecount = lGlobals[i];
		f.write(lGlobals[i].to_bytes(4, byteorder='little'));
		i += 1;
		
		# write the actual data
		if type(lGlobals[i]) == float:
			if bytecount==4:
				ba = bytearray(struct.pack("f", lGlobals[i]));
				n = int.from_bytes(ba, byteorder='little');
				f.write(n.to_bytes(bytecount, byteorder='little'));
			elif bytecount==8:
				ba = bytearray(struct.pack("d", lGlobals[i]));
				n = int.from_bytes(ba, byteorder='little');
				f.write(n.to_bytes(bytecount, byteorder='little'));
		elif type(lGlobals[i])==str:
			for x in lGlobals[i]:
				f.write(ord(x).to_bytes(1, byteorder='little'));
			f.write(0x0.to_bytes(1, byteorder='little'));
		else:
			f.write(lGlobals[i].to_bytes(bytecount, byteorder='little'));
		i += 1;

def wrt_hdr_footer(f, entry=0, modes=3) -> None:
	f.write(entry.to_bytes(8, byteorder='little'));
	# 1 for safemode, 2 for debugmode, 3 for both.
	f.write(modes.to_bytes(1, byteorder='little'));

def wrt_opcode(f, opcode:int) -> None:
	f.write(opcode.to_bytes(1, byteorder='little'));

def wrt_pushq(f, val:any) -> None:
	f.write(opcodes.pushq.to_bytes(1, byteorder='little'));
	if type(val) == float:
		ba = bytearray(struct.pack("d", val));
		i = int.from_bytes(ba, byteorder='little');
		f.write(i.to_bytes(8, byteorder='little'));
	else:
		f.write(val.to_bytes(8, byteorder='little'));

def wrt_pushl(f, val:any) -> None:
	f.write(opcodes.pushl.to_bytes(1, byteorder='little'));
	if type(val) == float:
		ba = bytearray(struct.pack("f", val));
		i = int.from_bytes(ba, byteorder='little');
		f.write(i.to_bytes(4, byteorder='little'));
	else:
		f.write(val.to_bytes(4, byteorder='little'));

def wrt_push_smaller(f, size:int, val:int) -> None:
	if size==2:
		f.write(opcodes.pushs.to_bytes(1, byteorder='little'));
		f.write(val.to_bytes(2, byteorder='little'));
	else:
		f.write(opcodes.pushb.to_bytes(1, byteorder='little'));
		f.write(val.to_bytes(1, byteorder='little'));

def wrt_1op_4byte(f, opcode:int, val:int) -> None:
	f.write(opcode.to_bytes(1, byteorder='little'));
	f.write(val.to_bytes(4, byteorder='little'));
	
def wrt_1op_8byte(f, opcode:int, val:int) -> None:
	f.write(opcode.to_bytes(1, byteorder='little'));
	f.write(val.to_bytes(8, byteorder='little'));

def wrt_callnat(f, index:int, argcount:int) -> None:
	f.write(opcodes.callnat.to_bytes(1, byteorder='little'));
	f.write(index.to_bytes(4, byteorder='little'));
	f.write(argcount.to_bytes(4, byteorder='little'));

def wrt_callnats(f, argcount:int) -> None:
	f.write(opcodes.callnats.to_bytes(1, byteorder='little'));
	f.write(argcount.to_bytes(4, byteorder='little'));


'''
unsigned i = 0x0a0b0c0d;
int main()
{
	return 0;
}
'''
with open('endian_test1.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc, 'i', 0, 4, 0x0a0b0c0d);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);

with open('float_test.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc, 'flTen', 0, 4, 10.0, 'flTwo', 4, 4, 2.0);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 4);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_opcode(tbc, opcodes.addf);
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);

'''
int main()
{
	puts("hello world\n");
}
'''
with open('hello_world.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'puts');
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc, 'str00001', 0, len('hello world\n')+1, 'hello world\n');
	wrt_hdr_footer(tbc, entry=0);
	
	# stack starts at 31, pushing 13 chars, left with 18.
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_callnat(tbc, 0, 1);
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);

with open('pointers.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc, 't0', 0, 4, 50000);
	wrt_hdr_footer(tbc, entry=0);
	
	# 687 in hex
	wrt_pushl(tbc, 687);
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_opcode(tbc, opcodes.storespl);
	wrt_opcode(tbc, opcodes.halt);

with open('test_func_call.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, "func", 2, 10);
	wrt_hdr_globals(tbc, 'fiveh', 0, 4, 500, 'two', 4, 4, 2);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10); #0-8
	wrt_opcode(tbc, opcodes.halt); #9
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 4);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_opcode(tbc, opcodes.addl);
	
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);

with open('test_call_opcodes.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'func1', 0, 20, 'func2', 0, 26);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 20);
	wrt_pushq(tbc, 26);
	wrt_opcode(tbc, opcodes.calls);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushl(tbc, 0x0a0b0c0d);
	wrt_opcode(tbc, opcodes.ret);
	
	wrt_pushl(tbc, 0xffff);
	wrt_opcode(tbc, opcodes.ret);

with open('test_retn_func.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'f', 1, 15);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_pushl(tbc, 9);
	wrt_1op_8byte(tbc, opcodes.call, 15);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_pushl(tbc, 6);
	wrt_opcode(tbc, opcodes.uaddl);
	wrt_opcode(tbc, opcodes.retl);

with open('test_recursion.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 0xffFFffF);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'recursive', 0, 10);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0, modes=1);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	wrt_1op_8byte(tbc, opcodes.call, 10);

with open('test_factorial_recurs.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 255);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'factorial', 1, 15);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	#unsigned int factorial(unsigned int i) {
	#	if( i<=1 )
	#		return 1;
	#	return i * factorial( i-1 );
	#}
	
	wrt_pushl(tbc, 7); #0-4
	wrt_1op_8byte(tbc, opcodes.call, 15); #5-13
	wrt_opcode(tbc, opcodes.halt); #14
	
	# load i
	wrt_pushq(tbc, 16); #15-23
	wrt_opcode(tbc, opcodes.pushbpadd); #24
	wrt_opcode(tbc, opcodes.loadspl); #25
	# load 1
	wrt_pushl(tbc, 1); #26-30
	# i <= 1 ?
	wrt_opcode(tbc, opcodes.uleql); #31
	wrt_1op_8byte(tbc, opcodes.jzl, 47); #32-40
	wrt_pushl(tbc, 1); #41-45
	wrt_opcode(tbc, opcodes.retl); #46
	
	wrt_pushq(tbc, 16); #47
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspl);
	
	# i-1
	wrt_pushl(tbc, 1);
	wrt_opcode(tbc, opcodes.usubl);
	
	# factorial( i-1 );
	wrt_1op_8byte(tbc, opcodes.call, 15);
	
	# load i
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspl);
	# i * result of factorial( i-1 );
	wrt_opcode(tbc, opcodes.umull);
	wrt_opcode(tbc, opcodes.retl);

with open('test_native.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'test');
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10); #0-8
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushspsub);
	wrt_opcode(tbc, opcodes.popsp);
	
	wrt_pushl(tbc, 50);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 100);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 300.0);
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_callnat(tbc, 0, 1);
	wrt_opcode(tbc, opcodes.ret);

with open('test_local_native_funcptr.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'test');
	wrt_hdr_funcs(tbc);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushspsub);
	wrt_opcode(tbc, opcodes.popsp);
	
	wrt_pushl(tbc, 50);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 100);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 300.0);
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_1op_4byte(tbc, opcodes.pushnataddr, 0);
	wrt_callnats(tbc, 1);
	wrt_opcode(tbc, opcodes.halt);

with open('test_multiple_natives.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'test', 'printHW');
	wrt_hdr_funcs(tbc);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushspsub);
	wrt_opcode(tbc, opcodes.popsp);
	
	wrt_pushl(tbc, 50);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 100);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushl(tbc, 300.0);
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_pushq(tbc, 12);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_callnat(tbc, 1, 0);
	wrt_callnat(tbc, 0, 1);
	wrt_opcode(tbc, opcodes.halt);

with open('test_int2chr.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, "main", 0, 10);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushl(tbc, 0x052A);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.loadspb);
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);


with open('test_printf.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, "printf");
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc, 'str00001', 0, len('\nnum==%i %f\n')+1, '\nnum==%i %f\n');
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushq(tbc, 300.0);
	wrt_pushl(tbc, 280);
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_callnat(tbc, 0, 3);
	wrt_opcode(tbc, opcodes.ret);

with open('test_fopen.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, "fopen", "fclose");
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc,
		'str00001', 0, len('./endian_test1.tbc')+1, './endian_test1.tbc',
		'str00002', 19, len('rb')+1, 'rb'
		);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 19);
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_callnat(tbc, 0, 2);
	wrt_callnat(tbc, 1, 1);
	wrt_opcode(tbc, opcodes.ret);

with open('test_malloc.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, "malloc", "free");
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10);
	wrt_opcode(tbc, opcodes.halt);
	
	wrt_pushl(tbc, 4);
	wrt_callnat(tbc, 0, 1);
	wrt_callnat(tbc, 1, 1);
	wrt_opcode(tbc, opcodes.ret);



''' FIRST MAJOR PROGRAM THAT RESEMBLES ACTUAL C
int i;
int f(void) {
	return i;
}
float e;

int main(void)
{
	int l = 5;
	printf( "%i\n", f()+l );
	return 0;
}
'''
with open('test_globalvars.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'printf');
	wrt_hdr_funcs(tbc, 'main', 0, 21, 'f', 0, 0);
	wrt_hdr_globals(tbc, 'i', 0, 4, 0, 'e', 4, 4, 0.0, 'str00001', 8, len('%i\n')+1, '%i\n');
	wrt_hdr_footer(tbc, entry=11);
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0); #0-8	push 'i''s address
	wrt_opcode(tbc, opcodes.loadspl); #9 load 'i' by address to TOS.
	wrt_opcode(tbc, opcodes.retl); #10		return 'i'
	
	wrt_1op_8byte(tbc, opcodes.call, 21); #11-19	call main
	wrt_opcode(tbc, opcodes.halt); #20	exit main
	
	wrt_pushl(tbc, 5); #25-29	int l=5;
	wrt_1op_8byte(tbc, opcodes.call, 0); #30-38		call 'f'
	wrt_opcode(tbc, opcodes.addl); # f() + l
	wrt_1op_8byte(tbc, opcodes.pushoffset, 8);	# load string literal
	wrt_callnat(tbc, 0, 2);	# call printf
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);	# return 0;



'''
void f() {
}

int main()
{
	void (*z)(void);
	callfunc(z);
	return 0;
}
'''
with open('test_funcptr_native.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'callfunc');
	wrt_hdr_funcs(tbc, 'main', 0, 16, 'f', 1, 0);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=6);
	
	wrt_pushl(tbc, 0); #0-4	push 'f''s func address
	wrt_opcode(tbc, opcodes.retl); #5		return 0
	
	wrt_1op_8byte(tbc, opcodes.call, 16); #6-14	call main
	wrt_opcode(tbc, opcodes.halt); #15	exit main
	
	wrt_pushq(tbc, 0); #16
	wrt_callnat(tbc, 0, 1);
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);	# return 0;

'''
int i;
int f(void) {
	return i;
}
float e;

int main(void)
{
	int l = 5;
	printf( "%i\n", f()+l );
	return 0;
}
'''
with open('test_loadgbl.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'getglobal');
	wrt_hdr_funcs(tbc, 'main', 0, 6);
	wrt_hdr_globals(tbc, 'i', 0, 4, 4294967196);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10); #0-8	call main
	wrt_opcode(tbc, opcodes.halt); #9	exit main
	
	#wrt_pushl(tbc, 16-4);	# load string literal
	wrt_callnat(tbc, 0, 0);	# call 'getglobal'
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);	# return 0;

'''
void f() {
}

int main()
{
	void (*z)(void);
	callfunc(z);
	return 0;
}
'''
with open('test_call_func_by_name.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc, 'callfuncname');
	wrt_hdr_funcs(tbc, 'main', 0, 16, 'f', 1, 0);
	wrt_hdr_globals(tbc, 'str00001', 0, len('f')+1, 'f');
	wrt_hdr_footer(tbc, entry=6);
	
	wrt_pushl(tbc, 0); #0-4	push 'f''s func address
	wrt_opcode(tbc, opcodes.retl); #5	return 0
	
	wrt_1op_8byte(tbc, opcodes.call, 16); #6-14	call main
	wrt_opcode(tbc, opcodes.halt); #15	exit main
	
	wrt_1op_8byte(tbc, opcodes.pushoffset, 0);
	wrt_callnat(tbc, 0, 1);
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);	# return 0;

'''
test GCC-style assembler generated code.
main:
        pushq   %rbp
        movq    %rsp, %rbp
        movl    $5, -4(%rbp)
        movb    $-1, -5(%rbp)
        movl    $0, %eax
        popq    %rbp
        ret
'''
with open('test_gcc_style_asm.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 64);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'main', 0, 10);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10); #0-8	call main
	wrt_opcode(tbc, opcodes.halt); #9	exit main
	
	wrt_pushq(tbc, 16);		# reserve stack space for local vars. assembly rbp is allowed to go below 
	wrt_opcode(tbc, opcodes.pushspsub);
	wrt_opcode(tbc, opcodes.popsp);
	
	wrt_pushl(tbc, 5);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_push_smaller(tbc, 1, 123);
	wrt_pushq(tbc, 5);
	wrt_opcode(tbc, opcodes.pushbpsub);
	wrt_opcode(tbc, opcodes.storespb);
	
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl);	# return 0;


'''
test a game-like type of vector calculation.

void vec_invert(vec3_t v)	/* float v[3] */
{
	v[0] = -v[0];
	v[1] = -v[1];
	v[2] = -v[2];
}

int main()
{
	float v[3] = { 2.f, 3.f, 4.f };
	vec_invert(v);
	return 0;
}
'''
#'''
with open('test_3d_vecs.tbc', 'wb+') as tbc:
	wrt_hdr(tbc, 128);
	wrt_hdr_natives(tbc);
	wrt_hdr_funcs(tbc, 'main', 0, 10, 'VecInverse', 1, 94);
	wrt_hdr_globals(tbc);
	wrt_hdr_footer(tbc, entry=0);
	
	wrt_1op_8byte(tbc, opcodes.call, 10); #0-8	call main
	wrt_opcode(tbc, opcodes.halt); #9	exit main
	
# main:
	wrt_pushq(tbc, 16);		#10-18 reserve stack space for local vars.
	wrt_opcode(tbc, opcodes.pushspsub); #19
	wrt_opcode(tbc, opcodes.popsp); #20
	
	wrt_pushl(tbc, 2.0); #21-25
	wrt_pushq(tbc, 16); #26-34
	wrt_opcode(tbc, opcodes.pushbpsub); #35
	wrt_opcode(tbc, opcodes.storespl); #36
	
	wrt_pushl(tbc, 3.0); #37-41
	wrt_pushq(tbc, 12); #42-50
	wrt_opcode(tbc, opcodes.pushbpsub); #51
	wrt_opcode(tbc, opcodes.storespl); #52
	
	wrt_pushl(tbc, 4.0); #53-57
	wrt_pushq(tbc, 8); #58-66
	wrt_opcode(tbc, opcodes.pushbpsub); #67
	wrt_opcode(tbc, opcodes.storespl); #68
	
	wrt_pushq(tbc, 16); #69-77
	wrt_opcode(tbc, opcodes.pushbpsub); #78
	wrt_1op_8byte(tbc, opcodes.call, 94);
	
	wrt_pushl(tbc, 0);
	wrt_opcode(tbc, opcodes.retl); # return 0;
	
# vec_invert:
	# v[0] = -v[0];
	# load up old bp address
	wrt_pushq(tbc, 16); #98
	wrt_opcode(tbc, opcodes.pushbpadd);
	# deref old bp addr and load up the vector's addr
	# remember that tagha is 64-bit so addr of an addr is load/store spq
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_opcode(tbc, opcodes.loadspl); # vector's data itself.
	
	# negate it
	wrt_opcode(tbc, opcodes.negf);
	
	# re-retrieve the addr and store the negated result.
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_opcode(tbc, opcodes.storespl);
	
	# v[1] = -v[1];
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.uaddq);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_opcode(tbc, opcodes.negf);
	
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_pushq(tbc, 4);
	wrt_opcode(tbc, opcodes.uaddq);
	wrt_opcode(tbc, opcodes.storespl);
	
	# v[2] = -v[2];
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.uaddq);
	wrt_opcode(tbc, opcodes.loadspl);
	wrt_opcode(tbc, opcodes.negf);
	
	wrt_pushq(tbc, 16);
	wrt_opcode(tbc, opcodes.pushbpadd);
	wrt_opcode(tbc, opcodes.loadspq);
	wrt_pushq(tbc, 8);
	wrt_opcode(tbc, opcodes.uaddq);
	wrt_opcode(tbc, opcodes.storespl);
	
	wrt_opcode(tbc, opcodes.ret);
#'''





