const createFileW = Module.findGlobalExportByName('CreateFileW');
const writeFile = Module.findGlobalExportByName('WriteFile');
const closeHandle = Module.findGlobalExportByName('CloseHandle');
const targets = new Map();

if (createFileW) Interceptor.attach(createFileW, {
  onEnter(args) { this.path = args[0].isNull() ? '' : args[0].readUtf16String(); },
  onLeave(retval) {
    if (this.path.toLowerCase().includes('aura.gb')) {
      targets.set(retval.toString(), this.path);
      send({event: 'open', handle: retval.toString(), path: this.path});
    }
  }
});

if (writeFile) Interceptor.attach(writeFile, {
  onEnter(args) {
    const handle = args[0].toString();
    if (!targets.has(handle)) return;
    const size = args[2].toUInt32();
    const trace = Thread.backtrace(this.context, Backtracer.ACCURATE).map(DebugSymbol.fromAddress).map(String);
    send({event: 'write', handle, buffer: args[1].toString(), size, trace});
  }
});

if (closeHandle) Interceptor.attach(closeHandle, {
  onEnter(args) { targets.delete(args[0].toString()); }
});
