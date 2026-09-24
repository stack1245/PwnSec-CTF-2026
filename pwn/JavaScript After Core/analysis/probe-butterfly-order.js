let holder = {};
for (let i = 0; i < 16; ++i) {
    let a = new Array(8);
    for (let j = 0; j < 8; ++j)
        a[j] = i + j + 0.1;
    holder["jac" + i] = a;
}
print(generateHeapSnapshotForGCDebugging());
