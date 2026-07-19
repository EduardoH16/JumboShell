# JumboShell 🐘

JumboShell is a terminal tool built for Tufts CS students.

It runs on top of your normal terminal and gives you a smarter interface.

---

## What it does

- **SSH login with saved credentials** — log in to `homework.cs.tufts.edu` once and JumboShell remembers your UTLN and password securely.
- **Split-screen diff viewer** — run `diff file1 file2` and get a proper side-by-side view with removed lines highlighted red on the left and added lines highlighted green on the right.
- **Unit test viewer** — run `unit_test` and get a clean pass/fail list. Each test shows whether it passed valgrind too.
- **Valgrind summary** — run `valgrind ./yourprogram` and get a plain-English summary at the bottom.
- **Themes** — pick between Dark, Light, Grey, and High Contrast. Your choice is saved and applied every time you open JumboShell.
- **Full terminal** — everything else just works like a normal terminal. You can run interactive programs, use Ctrl+C, navigate command history with the arrow keys, and so on.

---

## Setup

### Requirements

- Python 3.10 or newer
- Git

Everything else gets installed automatically on first run.

---

### Mac

Open Terminal (Applications → Utilities → Terminal, or Cmd+Space and type "terminal").

```bash
# 1. Clone the repo
git clone https://github.com/EduardoH16/JumboShell.git
cd JumboShell

# 2. Make the launcher executable
chmod +x jumboshell.sh

# 3. Run it (first run installs dependencies automatically)
./jumboshell.sh
```

To make `jumboshell` a command you can run from anywhere:

```bash
echo "alias jumboshell='bash ~/Documents/GitHub/JumboShell/jumboshell.sh'" >> ~/.zshrc
source ~/.zshrc
```

After that, just type `jumboshell` in any terminal window to launch it.

---

### Linux

Open your terminal emulator of choice.

```bash
# 1. Clone the repo
git clone https://github.com/EduardoH16/JumboShell.git
cd JumboShell

# 2. Make the launcher executable
chmod +x jumboshell.sh

# 3. Run it (first run installs dependencies automatically)
./jumboshell.sh
```

To make `jumboshell` a command you can run from anywhere:

```bash
echo "alias jumboshell='bash ~/Documents/GitHub/JumboShell/jumboshell.sh'" >> ~/.bashrc
source ~/.bashrc
```

---

### Windows (WSL)

JumboShell is designed to run inside WSL (Windows Subsystem for Linux). 

Once WSL is open:

```bash
# 1. Clone the repo
cd /mnt/c/Users/Name/Documents/GitHub
git clone https://github.com/EduardoH16/JumboShell.git
cd JumboShell

# 2. Run it (first run installs dependencies automatically)
bash jumboshell.sh
```

To make `jumboshell` a command you can run from anywhere in WSL:

```bash
echo "alias jumboshell='bash /mnt/c/Users/Name/Documents/GitHub/JumboShell/jumboshell.sh'" >> ~/.bashrc
source ~/.bashrc
```

After that, open WSL and type `jumboshell`.

---

## Usage

Once you're in, log in with your Tufts UTLN and password. JumboShell saves your credentials after the first successful login so you won't have to enter them again.

From there, use it like a normal terminal. A few things to know:

| Command | What happens |

| `diff file1 file2` | Opens the Diff tab with a side-by-side view |
| `unit_test` | Opens the Unit Tests tab with pass/fail results |
| `valgrind ./program` | Runs normally, then shows a summary at the bottom of the Terminal tab |
| `logout` | Logs you out and clears your saved credentials |
| Arrow keys | Navigate command history |
| Ctrl+C | Interrupts the current program |

The **Theme** button in the top-right lets you switch between Dark, Light, Grey, and High Contrast. Your choice is saved automatically.

---

## Notes

- All SSH communication goes through `paramiko`. Your password is stored in your OS keychain (macOS Keychain on Mac, GNOME Keyring on Linux, Windows Credential Manager on WSL), not in any file.
- JumboShell works with `g++`, `clang++`, and `gcc` output — compiler errors just print to the terminal tab like normal.
- Interactive programs work fine. Use Ctrl+C to interrupt them.
