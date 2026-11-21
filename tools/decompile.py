"""Decompile routines of r2k.exe by address, from a Ghidra project kept outside the repository.

Answers: "what does the routine at this address in Response-2000's binary do?", the question
CLAUDE.md allows the binary to be read for. Prints Ghidra's C for each address given (the
function containing it), and with --calls the routines it calls and those that call it.
An argument d:ADDRESS prints the double stored at that address instead (a constant the
decompiler shows as DAT_...); s:HEX lists the functions with an instruction that uses that
scalar (to find who writes a field at a known offset); r:ADDRESS lists the functions that
refer to that address (who uses a constant); v:VALUE lists where a double of that value is
stored and who refers to each place (to find the routine behind a constant seen in output).

Needs, none of it in the repository:
* Ghidra (12.x, headless) at $GHIDRA_HOME, with a JDK 21 on the path;
* a Ghidra project in which r2k.exe 1.9.7 (SHA-256 bbf4bc59...4e74) has been imported and
  analysed: by default ~/ghidra-projects/r2k (project r2k, program r2k.exe).

    python tools/decompile.py 0041e840 00417290 --calls > OUTSIDE_THE_REPO/out.c

The project is opened read-only and not analysed again. The output is Response's code in
another form: keep it out of the repository; record the rule taken from it in docs/kernel.md.

The Ghidra side is a GhidraScript in Java (written to a temporary folder at each run): Java
scripts run in headless Ghidra as installed, where Python ones need PyGhidra set up.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

JAVA = r"""
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.Function;
import java.io.PrintWriter;
import java.util.TreeSet;

public class R2cDecompile extends GhidraScript {
    private java.util.TreeMap<String, Integer> users(Address d) {
        java.util.TreeMap<String, Integer> hits = new java.util.TreeMap<>();
        for (ghidra.program.model.symbol.Reference r : getReferencesTo(d)) {
            Function g = getFunctionContaining(r.getFromAddress());
            hits.merge(g == null ? "? " + r.getFromAddress() : g.getEntryPoint().toString(), 1, Integer::sum);
        }
        return hits;
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        boolean calls = false;
        try (PrintWriter out = new PrintWriter(args[0], "UTF-8")) {
            DecompInterface dec = new DecompInterface();
            dec.openProgram(currentProgram);
            for (int i = 1; i < args.length; i++) {
                if (args[i].equals("--calls")) { calls = true; continue; }
                if (args[i].startsWith("s:")) {
                    // functions with an instruction that uses this scalar (a structure offset, say)
                    long want = Long.parseLong(args[i].substring(2), 16);
                    java.util.TreeMap<String, Integer> hits = new java.util.TreeMap<>();
                    ghidra.program.model.listing.InstructionIterator it = currentProgram.getListing().getInstructions(true);
                    while (it.hasNext()) {
                        ghidra.program.model.listing.Instruction ins = it.next();
                        for (int k = 0; k < ins.getNumOperands(); k++)
                            for (Object o : ins.getOpObjects(k))
                                if (o instanceof ghidra.program.model.scalar.Scalar
                                        && ((ghidra.program.model.scalar.Scalar) o).getUnsignedValue() == want) {
                                    Function g = getFunctionContaining(ins.getAddress());
                                    String key = (g == null ? "?" : g.getEntryPoint().toString()) + " " + ins.getMnemonicString();
                                    hits.merge(key, 1, Integer::sum);
                                }
                    }
                    out.println("// scalar 0x" + args[i].substring(2) + " used in: " + hits);
                    continue;
                }
                if (args[i].startsWith("r:")) {
                    // functions that refer to this address (who uses a constant or a string)
                    Address d = currentProgram.getAddressFactory().getAddress(args[i].substring(2));
                    out.println("// " + d + " referred to from: " + users(d));
                    continue;
                }
                if (args[i].startsWith("v:")) {
                    // where a double of this value is stored, and who refers to each place
                    byte[] pat = java.nio.ByteBuffer.allocate(8).order(java.nio.ByteOrder.LITTLE_ENDIAN)
                            .putDouble(Double.parseDouble(args[i].substring(2))).array();
                    ghidra.program.model.mem.Memory mem = currentProgram.getMemory();
                    Address at = mem.getMinAddress();
                    while ((at = mem.findBytes(at, pat, null, true, monitor)) != null) {
                        out.println("// double " + args[i].substring(2) + " at " + at + ", referred to from: " + users(at));
                        at = at.add(1);
                    }
                    continue;
                }
                if (args[i].startsWith("d:")) {
                    Address d = currentProgram.getAddressFactory().getAddress(args[i].substring(2));
                    out.println("// double at " + d + " = " + getDouble(d));
                    continue;
                }
                Address a = currentProgram.getAddressFactory().getAddress(args[i]);
                Function f = getFunctionContaining(a);
                if (f == null) { out.println("// " + args[i] + ": no function here\n"); continue; }
                out.println("// ==== " + f.getEntryPoint() + " " + f.getName() + " (asked: "
                            + args[i] + ", " + f.getBody().getNumAddresses() + " bytes)");
                if (calls) {
                    TreeSet<String> s = new TreeSet<>();
                    for (Function g : f.getCalledFunctions(monitor)) s.add(g.getEntryPoint() + " " + g.getName());
                    out.println("// calls: " + String.join(", ", s));
                    s.clear();
                    for (Function g : f.getCallingFunctions(monitor)) s.add(g.getEntryPoint() + " " + g.getName());
                    out.println("// called by: " + String.join(", ", s));
                }
                DecompileResults r = dec.decompileFunction(f, 300, monitor);
                if (r.decompileCompleted()) out.println(r.getDecompiledFunction().getC());
                else out.println("// decompilation failed: " + r.getErrorMessage() + "\n");
            }
            dec.dispose();
        }
    }
}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("addresses", nargs="+", help="addresses as the decompiler shows them, e.g. 004ad9c0; d:0052e5b8 for a constant")
    ap.add_argument("--calls", action="store_true", help="also list callees and callers")
    ap.add_argument("--project", default=str(Path.home() / "ghidra-projects" / "r2k"),
                    help="Ghidra project, as folder/name (default ~/ghidra-projects/r2k)")
    ap.add_argument("--program", default="r2k.exe")
    a = ap.parse_args(argv)
    home = os.environ.get("GHIDRA_HOME")
    if not home:
        print("GHIDRA_HOME is not set", file=sys.stderr)
        return 2
    proj = Path(a.project).expanduser()
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "R2cDecompile.java").write_text(JAVA)
        out = Path(tmp) / "out.c"
        cmd = [str(Path(home).expanduser() / "support" / "analyzeHeadless"), str(proj.parent), proj.name,
               "-process", a.program, "-noanalysis", "-readOnly", "-scriptPath", tmp,
               "-postScript", "R2cDecompile.java", str(out)]
        cmd += (["--calls"] if a.calls else []) + a.addresses
        r = subprocess.run(cmd, capture_output=True, text=True)
        if not out.exists():
            sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
            return 1
        sys.stdout.write(out.read_text())
    return 0


if __name__ == "__main__":
    sys.exit(main())
