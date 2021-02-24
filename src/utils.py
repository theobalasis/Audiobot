from sys import stderr

def eprint(message: str) -> None:
    """Print a message to the standard error stream

    Parameters
    ----------
    message : str
        The message to print
    """
    print(message, file=stderr)
