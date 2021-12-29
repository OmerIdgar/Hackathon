class Painter:
    OK = '\033[92m'  # GREEN
    WARNING = '\033[93m'  # YELLOW
    FAIL = '\033[91m'  # RED
    WELCOME = '\033[96m'  # CYAN
    QUESTION = '\033[95m'  # MAGENTA


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
    return string
    ques_list = string.split("\n")
    if len(ques_list) > 1:
        for i in range(len(ques_list) - 1):
            ques_list[i] = f"{Painter.WELCOME}{Style.BRIGHT}{string}{Style.RESET}"
        ques_list[-1] = f"{Painter.QUESTION}{Style.BRIGHT}{string}{Style.RESET}"
    else:
        for i in range(len(ques_list)):
            ques_list[i] = f"{Painter.WELCOME}{Style.BRIGHT}{string}{Style.RESET}"
    return "\n".join(ques_list)