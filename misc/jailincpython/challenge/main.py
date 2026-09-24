#!/usr/bin/python3
import re

pattern = re.compile(
    r'^(?:[^\[\]"\'0-9()]+|\[[^\[\]"\'0-9()]*\])*$'
)

class hint_A():
    ...

hint_B = "%jailincpython"

def main():
    user_input = input("~ ")
    if (not bool(pattern.fullmatch(user_input))
        or user_input.count('.') > 2
        or not user_input.isascii()
        or len(user_input) > 800):
        print("Nope!!")
        exit()

    print(eval(user_input, {'globals': {}, '__builtins__': {"hint_A":hint_A, "hint_B":hint_B}}, {}))

if __name__ == "__main__":
    main()