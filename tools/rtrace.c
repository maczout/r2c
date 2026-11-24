/* rtrace: run a Win32 program under the Windows debug API and log values each time it
   reaches chosen addresses. The program is not changed on disk and runs as it does without
   this: a breakpoint is put in its memory, the values are read when it is reached, and it
   carries on. tools/rtrace.py builds this (i686-w64-mingw32-gcc), runs Response-2000 under
   it inside r2x's worker (Wine), and reads the log.

       rtrace.exe SPEC LOG program [args...]

   SPEC: one line per address,  ADDRESS NAME term term ...  A term is KIND:EXPR. KIND is
   i (a 32-bit integer read at EXPR), d (a double read at EXPR) or r (the value of EXPR).
   EXPR is a sum or difference of registers (eax ... esp), hexadecimal numbers and [EXPR]
   (the 32-bit value stored at EXPR), e.g.  d:[edi+30c]+a8 . LOG gets NAME and the values,
   one line per time the address is reached. */
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#define MAXBP 64
static struct { DWORD addr; BYTE orig; char name[32]; char terms[600]; } bp[MAXBP];
static int nbp;
static HANDLE hproc;
static FILE *lg;

static DWORD rd32(DWORD a) { DWORD v = 0; SIZE_T n; ReadProcessMemory(hproc, (LPCVOID)a, &v, 4, &n); return v; }
static double rdd(DWORD a) { double v = 0; SIZE_T n; ReadProcessMemory(hproc, (LPCVOID)a, &v, 8, &n); return v; }

static const char *p;
static CONTEXT *cx;
static DWORD expr(void);
static DWORD atom(void) {
    DWORD v = 0;
    while (*p == ' ') p++;
    if (*p == '[') { p++; v = expr(); if (*p == ']') p++; v = rd32(v); }
    else if (isalpha((unsigned char)*p) && !isxdigit((unsigned char)p[0]) ) goto reg;
    else if (!strncmp(p, "eax", 3) || !strncmp(p, "ebx", 3) || !strncmp(p, "ecx", 3) || !strncmp(p, "edx", 3)
          || !strncmp(p, "esi", 3) || !strncmp(p, "edi", 3) || !strncmp(p, "ebp", 3) || !strncmp(p, "esp", 3)) {
reg:
        if (!strncmp(p, "eax", 3)) v = cx->Eax; else if (!strncmp(p, "ebx", 3)) v = cx->Ebx;
        else if (!strncmp(p, "ecx", 3)) v = cx->Ecx; else if (!strncmp(p, "edx", 3)) v = cx->Edx;
        else if (!strncmp(p, "esi", 3)) v = cx->Esi; else if (!strncmp(p, "edi", 3)) v = cx->Edi;
        else if (!strncmp(p, "ebp", 3)) v = cx->Ebp; else if (!strncmp(p, "esp", 3)) v = cx->Esp;
        p += 3;
    } else v = strtoul(p, (char **)&p, 16);
    if (*p == '*') { p++; v *= strtoul(p, (char **)&p, 16); }
    return v;
}
static DWORD expr(void) {
    DWORD v = atom();
    for (;;) {
        while (*p == ' ') p++;
        if (*p == '+') { p++; v += atom(); }
        else if (*p == '-') { p++; v -= atom(); }
        else break;
    }
    return v;
}

static void logbp(int k, CONTEXT *c) {
    char buf[600], *t;
    cx = c;
    strcpy(buf, bp[k].terms);
    fprintf(lg, "%s", bp[k].name);
    for (t = strtok(buf, " \t\r\n"); t; t = strtok(NULL, " \t\r\n")) {
        char kind = t[0];
        DWORD a;
        p = t + 2;
        a = expr();
        if (kind == 'i') fprintf(lg, " %ld", (long)(int)rd32(a));
        else if (kind == 'd') fprintf(lg, " %.10g", rdd(a));
        else fprintf(lg, " %ld", (long)(int)a);
    }
    fprintf(lg, "\n");
    fflush(lg);
}

static void arm(int k, int on) {
    BYTE b = on ? 0xCC : bp[k].orig; SIZE_T n;
    WriteProcessMemory(hproc, (LPVOID)bp[k].addr, &b, 1, &n);
    FlushInstructionCache(hproc, (LPCVOID)bp[k].addr, 1);
}

int main(int argc, char **argv) {
    STARTUPINFOA si; PROCESS_INFORMATION pi; DEBUG_EVENT ev; char cmd[4096] = "", line[700];
    FILE *sp; int i, pending = -1, installed = 0;
    if (argc < 4) return 2;
    sp = fopen(argv[1], "r"); lg = fopen(argv[2], "w");
    if (!sp || !lg) return 3;
    while (fgets(line, sizeof line, sp) && nbp < MAXBP) {
        int off = 0;
        if (line[0] == '#' || sscanf(line, "%lx %31s %n", &bp[nbp].addr, bp[nbp].name, &off) < 2) continue;
        strncpy(bp[nbp].terms, line + off, sizeof bp[nbp].terms - 1);
        nbp++;
    }
    for (i = 3; i < argc; i++) { strcat(cmd, "\""); strcat(cmd, argv[i]); strcat(cmd, "\" "); }
    memset(&si, 0, sizeof si); si.cb = sizeof si;
    if (!CreateProcessA(NULL, cmd, NULL, NULL, FALSE, DEBUG_ONLY_THIS_PROCESS, NULL, NULL, &si, &pi)) {
        fprintf(lg, "CreateProcess failed %lu\n", GetLastError()); return 4;
    }
    hproc = pi.hProcess;
    for (;;) {
        DWORD cont = DBG_CONTINUE;
        if (!WaitForDebugEvent(&ev, INFINITE)) break;
        if (ev.dwDebugEventCode == EXIT_PROCESS_DEBUG_EVENT) break;
        if (ev.dwDebugEventCode == CREATE_PROCESS_DEBUG_EVENT && !installed) {
            SIZE_T n;
            for (i = 0; i < nbp; i++) { ReadProcessMemory(hproc, (LPCVOID)bp[i].addr, &bp[i].orig, 1, &n); arm(i, 1); }
            installed = 1;
            fprintf(lg, "# %d breakpoints set\n", nbp); fflush(lg);
        }
        if (ev.dwDebugEventCode == EXCEPTION_DEBUG_EVENT) {
            DWORD code = ev.u.Exception.ExceptionRecord.ExceptionCode;
            DWORD at = (DWORD)ev.u.Exception.ExceptionRecord.ExceptionAddress;
            HANDLE th = OpenThread(THREAD_ALL_ACCESS, FALSE, ev.dwThreadId);
            CONTEXT c; c.ContextFlags = CONTEXT_FULL;
            if (code == EXCEPTION_BREAKPOINT) {
                for (i = 0; i < nbp; i++) if (bp[i].addr == at) break;
                if (i < nbp) {
                    GetThreadContext(th, &c);
                    c.Eip = at;
                    logbp(i, &c);
                    arm(i, 0);
                    c.EFlags |= 0x100;
                    SetThreadContext(th, &c);
                    pending = i;
                }
            } else if (code == EXCEPTION_SINGLE_STEP) {
                if (pending >= 0) { arm(pending, 1); pending = -1; }
            } else cont = DBG_EXCEPTION_NOT_HANDLED;
            CloseHandle(th);
        }
        ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, cont);
    }
    fprintf(lg, "# end\n"); fclose(lg);
    return 0;
}
