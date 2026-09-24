function hook(name, callbacks) {
  const address = Module.findGlobalExportByName(name);
  if (address === null) {
    send({ event: "missing", name });
    return;
  }
  Interceptor.attach(address, callbacks);
  send({ event: "hooked", name, address: address.toString() });
}

hook("ShellExecuteA", {
  onEnter(args) {
    send({
      event: "ShellExecuteA",
      operation: args[1].isNull() ? null : args[1].readCString(),
      file: args[2].isNull() ? null : args[2].readCString(),
      parameters: args[3].isNull() ? null : args[3].readCString(),
      directory: args[4].isNull() ? null : args[4].readCString(),
      show: args[5].toInt32(),
    });
  },
});

hook("WTSSendMessageW", {
  onEnter(args) {
    send({
      event: "WTSSendMessageW",
      title: args[2].isNull() ? null : args[2].readUtf16String(args[3].toInt32() / 2),
      message: args[4].isNull() ? null : args[4].readUtf16String(args[5].toInt32() / 2),
    });
  },
});

hook("MessageBoxW", {
  onEnter(args) {
    send({
      event: "MessageBoxW",
      text: args[1].isNull() ? null : args[1].readUtf16String(),
      caption: args[2].isNull() ? null : args[2].readUtf16String(),
    });
  },
});

hook("ExitProcess", {
  onEnter(args) {
    send({ event: "ExitProcess", code: args[0].toUInt32() });
  },
});

function suppressDelete(name, returnType, argumentType, readPath, successValue) {
  const address = Module.findGlobalExportByName(name);
  if (address === null) {
    send({ event: "missing", name });
    return;
  }
  Interceptor.replace(address, new NativeCallback(function (path) {
    let value = null;
    try {
      value = path.isNull() ? null : readPath(path);
    } catch (error) {
      value = `<unreadable: ${error}>`;
    }
    send({ event: "suppressed-delete", name, path: value });
    return successValue;
  }, returnType, [argumentType]));
  send({ event: "replaced", name, address: address.toString() });
}

suppressDelete("DeleteFileA", "bool", "pointer", (path) => path.readCString(), 1);
suppressDelete("DeleteFileW", "bool", "pointer", (path) => path.readUtf16String(), 1);
suppressDelete("remove", "int", "pointer", (path) => path.readCString(), 0);
suppressDelete("_unlink", "int", "pointer", (path) => path.readCString(), 0);
