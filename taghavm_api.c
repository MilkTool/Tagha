
#include <stdio.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "tagha.h"

void Tagha_init(struct TaghaVM *vm)
{
	if( !vm )
		return;
	
	vm->m_pScript = NULL;
	
	vm->m_pmapNatives = malloc(sizeof(Map_t));
	if( !vm->m_pmapNatives )
		printf("[%sTagha Init Error%s]: **** %sUnable to initialize Native Map%s ****\n", KRED, RESET, KGRN, RESET);
	else map_init(vm->m_pmapNatives);
}

static bool is_c_file(const char *filename)
{
	if( !filename )
		return false;
	
	const char *p = filename;
	// iterate to end of string and then check backwards.
	while( *p )
		p++;
	return( (*(p-1)=='c' or *(p-1)=='C') and (*(p-2)=='.') );
}
static bool is_tbc_file(const char *filename)
{
	if( !filename )
		return false;
	
	const char *p = filename;
	// iterate to end of string and then check backwards.
	while( *p )
		p++;
	return( (*(p-3)=='t' and *(p-2)=='b' and *(p-1)=='c') or (*(p-3)=='T' and *(p-2)=='B' and *(p-1)=='C') and *(p-4)=='.' );
}


void Tagha_load_script_by_name(struct TaghaVM *restrict vm, char *restrict filename)
{
	if( !vm )
		return;
	
	// allocate our script.
	vm->m_pScript = TaghaScript_from_file(filename);
	
	struct TaghaScript *script = vm->m_pScript;
	
	// do some initial libc setup for our script.
	// set up our standard I/O streams
	// and global self-referencing script pointer
	// Downside is that the script side host var MUST be a pointer.
	if( script and script->m_pmapGlobals ) {
		TaghaScript_bind_global_ptr(script, "stdin", stdin);
		TaghaScript_bind_global_ptr(script, "stderr", stderr);
		TaghaScript_bind_global_ptr(script, "stdout", stdout);
		TaghaScript_bind_global_ptr(script, "myself", script);
	}
}


void Tagha_free(struct TaghaVM *vm)
{
	if( !vm )
		return;
	
	if( vm->m_pScript ) {
		TaghaScript_free(vm->m_pScript), vm->m_pScript=NULL;
	}
	
	// since the VMs native hashmap has nothing allocated,
	// we just free the hashmap's internal data and then the hashmap itself.
	if( vm->m_pmapNatives ) {
		map_free(vm->m_pmapNatives);
		gfree((void **)&vm->m_pmapNatives);
	}
}


bool Tagha_register_natives(struct TaghaVM *vm, struct NativeInfo arrNatives[])
{
	if( !vm or !arrNatives )
		return false;
	else if( !vm->m_pmapNatives )
		return false;
	
	for( NativeInfo_t *natives = arrNatives ; natives->pFunc and natives->strName ; natives++ )
		map_insert(vm->m_pmapNatives, natives->strName, (uintptr_t)natives->pFunc);
	return true;
}

void Tagha_call_script_func(struct TaghaVM *restrict vm, const char *restrict strFunc)
{
	// We need the VM system in order to call scripts, why?
	// Because the exec function needs the VM system in order to check for native functions.
	if( !vm or !vm->m_pScript or !strFunc )
		return;
	
	struct TaghaScript *script = vm->m_pScript;
	if( !script->m_pmapFuncs ) {
		TaghaScript_PrintErr(script, __func__, "Cannot call functions from host using a NULL function table!");
		return;
	}
	else if( ((script->m_pSP-script->m_pMemory)-16) >= script->m_uiMemsize ) {
		TaghaScript_PrintErr(script, __func__, "stack overflow!");
		return;
	}
	
	struct FuncTable *pFuncTable = (struct FuncTable *)(uintptr_t) map_find(script->m_pmapFuncs, strFunc);
	if( !pFuncTable ) {
		TaghaScript_PrintErr(script, __func__, "Function \'%s\' doesn't exist!", strFunc);
		return;
	}
	
	// save return address.
	script->m_pSP -= 8;
	*(uint64_t *)script->m_pSP = (uintptr_t)script->m_pIP+1;
	
	// jump to the function entry address.
	script->m_pIP = script->m_pText + pFuncTable->m_uiEntry;
	pFuncTable = NULL;
	
	/* Save bp in a separate variable so that we can remember what stack frame we began with.
	 * When the stack frame reverts back to saved bp variable, that means the function ended in the frame it first began.
	 * This is so the VM can appropriately call recursive functions or else
	 * the first 'ret' opcode would kill the entire call process.
	 * Not a big deal for non-recursive function but script function calling should accomodate for all types of functions.
	*/
	uint8_t *oldBP = script->m_pBP;
	
	// push bp and copy sp to bp.
	script->m_pSP -= 8;
	*(uint64_t *)script->m_pSP = (uintptr_t)script->m_pBP;
	script->m_pBP = script->m_pSP;
	
	Tagha_exec(vm, oldBP);
	oldBP = NULL;
	//TaghaScript_debug_print_instrs(script);
}

Script_t *Tagha_get_script(const struct TaghaVM *vm)
{
	return !vm ? NULL : vm->m_pScript;
}

void Tagha_set_script(struct TaghaVM *vm, struct TaghaScript *script)
{
	if( !vm )
		return;
	vm->m_pScript = script;
}

void gfree(void **ptr)
{
	if( *ptr )
		free(*ptr);
	*ptr = NULL;
}

// Code by sourcemod/AlliedModders LLC
#define LADJUST			0x00000001		/* left adjustment */
#define ZEROPAD			0x00000002		/* zero (as opposed to blank) pad */
#define UPPERDIGITS		0x00000004		/* make alpha digits uppercase */
#define NOESCAPE		0x00000008		/* do not escape strings (they are only escaped if a database connection is provided) */
#define to_digit(c)		((c) - '0')
#define is_digit(c)		((unsigned)to_digit(c) <= 9)

// minor edit is removing database string AND 'maxlen' is changed from a reference to a pointer.
static bool AddString(char **buf_p, size_t *maxlen, const char *string, int width, int prec, int flags)
{
	int size = 0;
	char *buf;
	static char nlstr[] = {'(','n','u','l','l',')','\0'};

	buf = *buf_p;

	if (string == NULL)
	{
		string = nlstr;
		prec = -1;
		flags |= NOESCAPE;
	}

	if (prec >= 0)
	{
		for (size = 0; size < prec; size++) 
		{
			if (string[size] == '\0')
			{
				break;
			}
		}
	}
	else
	{
		while (string[size++]);
		size--;
	}

	if (size > (int)*maxlen)
	{
		size = *maxlen;
	}

	width -= size;
	*maxlen -= size;

	while (size--)
	{
		*buf++ = *string++;
	}

	while ((width-- > 0) && *maxlen)
	{
		*buf++ = ' ';
		--*maxlen;
	}

	*buf_p = buf;
	return true;
}

#include <float.h>
void AddFloat(char **buf_p, size_t *maxlen, double fval, int width, int prec, int flags)
{
	int digits;					// non-fraction part digits
	double tmp;					// temporary
	char *buf = *buf_p;			// output buffer pointer
	int val;					// temporary
	int sign = 0;				// 0: positive, 1: negative
	int fieldlength;			// for padding
	int significant_digits = 0;	// number of significant digits written
	const int MAX_SIGNIFICANT_DIGITS = 16;
	
	double pow(double base, double exponent);
	double log10(double x);

	if (fval != fval)
	{
		AddString(buf_p, maxlen, "NaN", width, prec, flags | NOESCAPE);
		return;
	}

	// default precision
	if (prec < 0)
	{
		prec = 6;
	}

	// get the sign
	if (fval < 0)
	{
		fval = -fval;
		sign = 1;
	}

	// compute whole-part digits count
	//digits = (int)log10(fval) + 1;

	// Only print 0.something if 0 < fval < 1
	if (digits < 1)
	{
		digits = 1;
	}

	// compute the field length
	fieldlength = digits + prec + ((prec > 0) ? 1 : 0) + sign;

	// minus sign BEFORE left padding if padding with zeros
	if (sign && *maxlen && (flags & ZEROPAD))
	{
		*buf++ = '-';
		--*maxlen;
	}

	// right justify if required
	if ((flags & LADJUST) == 0)
	{
		while ((fieldlength < width) && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			width--;
			--*maxlen;
		}
	}

	// minus sign AFTER left padding if padding with spaces
	if (sign && maxlen && !(flags & ZEROPAD))
	{
		*buf++ = '-';
		--*maxlen;
	}

	// write the whole part
	//tmp = pow(10.0, digits-1);
	while ((digits--) && *maxlen)
	{
		if (++significant_digits > MAX_SIGNIFICANT_DIGITS)
		{
			*buf++ = '0';
		}
		else
		{
			val = (int)(fval / tmp);
			*buf++ = '0' + val;
			fval -= val * tmp;
			tmp *= 0.1;
		}
		--*maxlen;
	}

	// write the fraction part
	if (*maxlen && prec)
	{
		*buf++ = '.';
		--*maxlen;
	}

	//tmp = pow(10.0, prec);

	fval *= tmp;
	while (prec-- && *maxlen)
	{
		if (++significant_digits > MAX_SIGNIFICANT_DIGITS)
		{
			*buf++ = '0';
		}
		else
		{
			tmp *= 0.1;
			val = (int)(fval / tmp);
			*buf++ = '0' + val;
			fval -= val * tmp;
		}
		--*maxlen;
	}

	// left justify if required
	if (flags & LADJUST)
	{
		while ((fieldlength < width) && *maxlen)
		{
			// right-padding only with spaces, ZEROPAD is ignored
			*buf++ = ' ';
			width--;
			--*maxlen;
		}
	}

	// update parent's buffer pointer
	*buf_p = buf;
}

void AddBinary(char **buf_p, size_t *maxlen, uint64_t val, int width, int flags)
{
	char text[64];
	int digits;
	char *buf;

	digits = 0;
	do
	{
		if (val & 1)
		{
			text[digits++] = '1';
		}
		else
		{
			text[digits++] = '0';
		}
		val >>= 1;
	} while (val);

	buf = *buf_p;

	if (!(flags & LADJUST))
	{
		while (digits < width && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			width--;
			--*maxlen;
		}
	}

	while (digits-- && *maxlen)
	{
		*buf++ = text[digits];
		width--;
		--*maxlen;
	}

	if (flags & LADJUST)
	{
		while (width-- && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			--*maxlen;
		}
	}

	*buf_p = buf;
}

void AddUInt(char **buf_p, size_t *maxlen, uint64_t val, int width, int flags)
{
	char text[64];
	int digits;
	char *buf;

	digits = 0;
	do
	{
		text[digits++] = '0' + val % 10;
		val /= 10;
	} while (val);

	buf = *buf_p;

	if (!(flags & LADJUST))
	{
		while (digits < width && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			width--;
			--*maxlen;
		}
	}

	while (digits-- && *maxlen)
	{
		*buf++ = text[digits];
		width--;
		--*maxlen;
	}

	if (flags & LADJUST)
	{
		while (width-- && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			--*maxlen;
		}
	}

	*buf_p = buf;
}

void AddInt(char **buf_p, size_t *maxlen, int64_t val, int width, int flags)
{
	char text[64];
	int digits;
	int signedVal;
	char *buf;
	uint64_t unsignedVal;

	digits = 0;
	signedVal = val;
	if (val < 0)
	{
		/* we want the unsigned version */
		unsignedVal = llabs(val);
	}
	else
	{
		unsignedVal = val;
	}

	do
	{
		text[digits++] = '0' + unsignedVal % 10;
		unsignedVal /= 10;
	} while (unsignedVal);

	if (signedVal < 0)
	{
		text[digits++] = '-';
	}

	buf = *buf_p;

	if (!(flags & LADJUST))
	{
		while ((digits < width) && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			width--;
			--*maxlen;
		}
	}

	while (digits-- && *maxlen)
	{
		*buf++ = text[digits];
		width--;
		--*maxlen;
	}

	if (flags & LADJUST)
	{
		while (width-- && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			--*maxlen;
		}
	}

	*buf_p = buf;
}

void AddHex(char **buf_p, size_t *maxlen, uint64_t val, int width, int flags)
{
	char text[64];
	int digits;
	char *buf;
	char digit;
	int hexadjust;

	if (flags & UPPERDIGITS)
	{
		hexadjust = 'A' - '9' - 1;
	}
	else
	{
		hexadjust = 'a' - '9' - 1;
	}

	digits = 0;
	do 
	{
		digit = ('0' + val % 16);
		if (digit > '9')
		{
			digit += hexadjust;
		}

		text[digits++] = digit;
		val /= 16;
	} while(val);

	buf = *buf_p;

	if (!(flags & LADJUST))
	{
		while (digits < width && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			width--;
			--*maxlen;
		}
	}

	while (digits-- && *maxlen)
	{
		*buf++ = text[digits];
		width--;
		--*maxlen;
	}

	if (flags & LADJUST)
	{
		while (width-- && *maxlen)
		{
			*buf++ = (flags & ZEROPAD) ? '0' : ' ';
			--*maxlen;
		}
	}

	*buf_p = buf;
}

int32_t gnprintf(char *buffer,
			  size_t maxlen,
			  const char *format,
			  void *params[],
			  uint32_t numparams,
			  uint32_t *restrict curparam)
{
	if (!buffer || !maxlen)
	{
		return -1;
	}

	int arg = 0;
	char *buf_p;
	char ch;
	int flags;
	int width;
	int prec;
	int n;
	char sign;
	const char *fmt;
	size_t llen = maxlen - 1;

	buf_p = buffer;
	fmt = format;

	while (true)
	{
		// run through the format string until we hit a '%' or '\0'
		for (ch = *fmt; llen && ((ch = *fmt) != '\0') && (ch != '%'); fmt++)
		{
			*buf_p++ = ch;
			llen--;
		}
		if ((ch == '\0') || (llen <= 0))
		{
			goto done;
		}

		// skip over the '%'
		fmt++;

		// reset formatting state
		flags = 0;
		width = 0;
		prec = -1;
		sign = '\0';

rflag:
		ch = *fmt++;
reswitch:
		switch(ch)
		{
			case '-':
			{
				flags |= LADJUST;
				goto rflag;
			}
			case '.':
			{
				n = 0;
				while(is_digit((ch = *fmt++)))
				{
					n = 10 * n + (ch - '0');
				}
				prec = (n < 0) ? -1 : n;
				goto reswitch;
			}
			case '0':
			{
				flags |= ZEROPAD;
				goto rflag;
			}
			case '1' ... '9':
			{
				n = 0;
				do
				{
					n = 10 * n + (ch - '0');
					ch = *fmt++;
				} while(is_digit(ch));
				width = n;
				goto reswitch;
			}
			case 'c':
			{
				if (!llen)
				{
					goto done;
				}
				char *c = (char *)params[*curparam];
				++*curparam;
				*buf_p++ = *c;
				llen--;
				arg++;
				break;
			}
			case 'b':
			{
				int64_t *value = (int64_t *)params[*curparam];
				++*curparam;
				AddBinary(&buf_p, &llen, *value, width, flags);
				arg++;
				break;
			}
			case 'd': case 'i':
			{
				int32_t *value = (int32_t *)params[*curparam];
				++*curparam;
				AddInt(&buf_p, &llen, *value, width, flags);
				arg++;
				break;
			}
			case 'u':
			{
				uint32_t *value = (uint32_t *)params[*curparam];
				++*curparam;
				AddUInt(&buf_p, &llen, *value, width, flags);
				arg++;
				break;
			}
			case 'f':
			{
				double *value = (double *)params[*curparam];
				++*curparam;
				AddFloat(&buf_p, &llen, *value, width, prec, flags);
				arg++;
				break;
			}
			case 's':
			{
				const char *str = (const char *)params[*curparam];
				++*curparam;
				AddString(&buf_p, &llen, str, width, prec, flags);
				arg++;
				break;
			}
			case 'X':
			{
				uint32_t *value = (uint32_t *)params[*curparam];
				++*curparam;
				flags |= UPPERDIGITS;
				AddHex(&buf_p, &llen, *value, width, flags);
				arg++;
				break;
			}
			case 'x':
			{
				uint32_t *value = (uint32_t *)params[*curparam];
				++*curparam;
				AddHex(&buf_p, &llen, *value, width, flags);
				arg++;
				break;
			}
			case '%':
			{
				if (!llen)
				{
					goto done;
				}
				*buf_p++ = ch;
				llen--;
				break;
			}
			case '\0':
			{
				if (!llen)
				{
					goto done;
				}
				*buf_p++ = '%';
				llen--;
				goto done;
			}
			default:
			{
				if (!llen)
				{
					goto done;
				}
				*buf_p++ = ch;
				llen--;
				break;
			}
		}
	}

done:
	*buf_p = '\0';
	
	return (maxlen - llen - 1);
}
/////////////////////////////////////////////////////////////////////////////////









