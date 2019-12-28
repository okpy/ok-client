
from colorama import Fore, Style

def print_error(text):
    print(Fore.RED + text + Style.RESET_ALL)

def print_warning(text):
    print(Fore.YELLOW + text + Style.RESET_ALL)

def print_success(text):
    print(Fore.GREEN + text + Style.RESET_ALL)
