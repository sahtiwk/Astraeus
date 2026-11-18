import sys
from unittest.mock import Mock

import pytest

from src import launcher


def test_auto_model_falls_back_and_uses_local_embedding_path(tmp_path, monkeypatch):
    (tmp_path / 'models/embedding').mkdir(parents=True)
    monkeypatch.setattr(launcher, 'ROOT', tmp_path)
    monkeypatch.setattr(launcher, 'verify', lambda *args: False)
    monkeypatch.setattr(launcher, 'hardware', lambda: {'available_gib': 8})
    monkeypatch.setattr(sys, 'argv', ['launcher', '--auto-model', '--ui-port', '18951'])
    process = Mock()
    process.wait.return_value = 0
    calls = []
    def start(args, **kwargs):
        calls.append((args, kwargs))
        return process
    monkeypatch.setattr(launcher.subprocess, 'Popen', start)
    launcher.main()
    assert len(calls) == 1
    assert 'streamlit' in calls[0][0]
    assert calls[0][1]['env']['ASTRAEUS_EMBEDDING_MODEL'] == str(tmp_path / 'models/embedding')


def test_launcher_rejects_occupied_port(monkeypatch):
    import socket
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        monkeypatch.setattr(sys, 'argv', ['launcher', '--ui-port', str(listener.getsockname()[1])])
        with pytest.raises(SystemExit, match='already in use'):
            launcher.main()
