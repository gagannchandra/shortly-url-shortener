import random
import string

<<<<<<< HEAD
_CHARSET = string.ascii_letters + string.digits


def generate_short_code(length: int = 6) -> str:
    """Return a random alphanumeric code of the given length."""
    return "".join(random.choices(_CHARSET, k=length))
=======

CHARACTER_SET =string.ascii_letters + string.digits

def generate_short_code(length=6):
    
    generated_code = "".join(random.choices(CHARACTER_SET,k = length))
    return generated_code


if __name__ == '__main__':
    print("--- Testing generate_short_code ---")
    
    print("Generating 5 codes with default length (6):")
    for _ in range(5):
        print(generate_short_code())

    print("\\n" + '-'*20 + "\\n")
    
    print("Generting 1 code with custom lengh (10):")
    print(generate_short_code(10))
    
    print("\\n" + "-"*20 + "\\n")
>>>>>>> c72572e7540a87ddf6bb0bb72ca2a336761cb0e5
