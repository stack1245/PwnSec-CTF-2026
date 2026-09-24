<?php
$n = (int)($argv[1] ?? 1);
$list = new SplDoublyLinkedList();
$payload = 'i:0;:O:8:"stdClass":2:{s:1:"a";i:11;s:1:"b";i:22;}:R:' . $n . ';';
try {
    $list->unserialize($payload);
    var_dump($list[0], $list[1]);
} catch (Throwable $e) {
    echo $e->getMessage(), "\n";
}
