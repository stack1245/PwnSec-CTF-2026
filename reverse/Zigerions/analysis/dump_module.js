const shellExecute = Module.findGlobalExportByName('ShellExecuteA');
if (shellExecute !== null) Interceptor.attach(shellExecute, {
  onEnter(args) {
    const module = Process.mainModule;
    send({event: 'module-dump', base: module.base.toString(), size: module.size}, module.base.readByteArray(module.size));
  }
});
