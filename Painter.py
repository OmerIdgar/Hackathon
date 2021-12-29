class Painter:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    SERVER = '\033[96m'  # CYAN


class Style:
    BRIGHT = '\033[1m'
    DIM = '\033[2m'
    NORMAL = '\033[22m'
    RESET = '\033[0m'


def OK_message(string):
    return f"{Painter.OK}{Style.BRIGHT}{string}{Style.RESET}"


def WARNING_message(string):
    return f"{Painter.WARNING}{Style.BRIGHT}{string}{Style.RESET}"


def FAIL_message(string):
    return f"{Painter.FAIL}{Style.BRIGHT}{string}{Style.RESET}"


def SERVER_message(string):
    return f"{Painter.SERVER}{Style.BRIGHT}{string}{Style.RESET}"
