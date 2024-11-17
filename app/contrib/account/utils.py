import random
import string


def rand_code(length: int) -> str:
    # Define the possible characters: letters and digits
    characters = string.ascii_letters + string.digits

    # Generate a random string using the specified characters
    random_string = ''.join(random.choice(characters) for _ in range(length))

    return random_string.upper()
