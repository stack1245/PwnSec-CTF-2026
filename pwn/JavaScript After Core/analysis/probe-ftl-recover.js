let trigger = false;

function pivot() {
    if (!trigger)
        return;
    Object.defineProperty(Array.prototype, 0, {
        get() { return 42; },
        set(_) {},
        configurable: true
    });
}
noInline(pivot);

function opt(escape) {
    let a = new Array(8);
    a[0] = { marker: 0x1337 };
    a[1] = 2.2;
    a[2] = 3.3;
    a[3] = 4.4;
    a[4] = 5.5;
    a[5] = 6.6;
    a[6] = 7.7;
    a[7] = 8.8;
    pivot();
    if (escape)
        return a;
    return isFinalTier();
}
noInline(opt);

let finalAt = -1;
for (let i = 0; i < 2000000; ++i) {
    if (opt(false)) {
        finalAt = i;
        break;
    }
}
print("finalAt=" + finalAt + " dfg=" + numberOfDFGCompiles(opt));

trigger = true;
let confused = opt(true);
print("length=" + confused.length);
for (let i = 0; i < 12; ++i) {
    try { print(i + ":" + confused[i]); }
    catch (e) { print(i + ":ERR:" + e); }
}
