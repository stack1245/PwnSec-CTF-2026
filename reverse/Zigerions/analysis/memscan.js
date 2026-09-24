function scanPattern(label, pattern) {
  let hits = 0;
  for (const range of Process.enumerateRanges('r--').concat(Process.enumerateRanges('rw-'), Process.enumerateRanges('r-x'))) {
    try {
      for (const match of Memory.scanSync(range.base, range.size, pattern)) {
        hits++;
        let context = '';
        try { context = match.address.readCString(256); } catch (_) {}
        send({event: 'memory-hit', label, address: match.address.toString(), mainBase: Process.mainModule.base.toString(), rva: match.address.sub(Process.mainModule.base).toString(), context});
      }
    } catch (_) {}
  }
  send({event: 'memory-scan-complete', label, hits});
}

function scanBraceStrings() {
  const seen = new Set();
  for (const range of Process.enumerateRanges('r--').concat(Process.enumerateRanges('rw-'), Process.enumerateRanges('r-x'))) {
    try {
      for (const match of Memory.scanSync(range.base, range.size, '7b')) {
        const startLimit = match.address.sub(96).compare(range.base) < 0 ? range.base : match.address.sub(96);
        const endLimit = match.address.add(160).compare(range.base.add(range.size)) > 0 ? range.base.add(range.size) : match.address.add(160);
        const bytes = new Uint8Array(startLimit.readByteArray(endLimit.sub(startLimit).toInt32()));
        const brace = match.address.sub(startLimit).toInt32();
        let left = brace;
        while (left > 0 && bytes[left - 1] >= 32 && bytes[left - 1] < 127) left--;
        let right = brace;
        while (right < bytes.length && bytes[right] >= 32 && bytes[right] < 127) right++;
        if (right - left >= 6) {
          let value = '';
          for (let i = left; i < right; i++) value += String.fromCharCode(bytes[i]);
          if (!seen.has(value)) { seen.add(value); send({event: 'brace-string', value}); }
        }
      }
    } catch (_) {}
  }
  send({event: 'brace-scan-complete', hits: seen.size});
}

const shellExecute = Module.findGlobalExportByName('ShellExecuteA');
if (shellExecute !== null) {
  Interceptor.attach(shellExecute, {
    onEnter(args) {
      send({event: 'ShellExecuteA', file: args[2].isNull() ? null : args[2].readCString()});
      scanPattern('ascii-psctf', '70 73 63 74 66 7b');
      scanPattern('utf16-psctf', '70 00 73 00 63 00 74 00 66 00 7b 00');
      scanPattern('gameboy-logo', 'ce ed 66 66 cc 0d 00 0b 03 73 00 83 00 0c 00 0d 00 08 11 1f 88 89 00 0e dc cc 6e e6 dd dd d9 99 bb bb 67 63 6e 0e ec cc dd dc 99 9f bb b9 33 3e');
      scanBraceStrings();
    }
  });
}
