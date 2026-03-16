"""Windows compatibility patch for POSIX signals.

CrewAI references POSIX-only signals (SIGHUP, SIGQUIT, etc.) that don't
exist on Windows. This module must be imported before any CrewAI import.
"""
import signal

_POSIX_SIGNALS = [
    'SIGHUP', 'SIGTSTP', 'SIGQUIT', 'SIGALRM', 'SIGUSR1',
    'SIGUSR2', 'SIGCHLD', 'SIGCONT', 'SIGSTOP', 'SIGTTIN', 'SIGTTOU',
]

for _sig in _POSIX_SIGNALS:
    if not hasattr(signal, _sig):
        setattr(signal, _sig, 1)
