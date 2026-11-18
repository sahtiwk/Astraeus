import hashlib
import pytest
from src import model_manager


def test_import_validates_before_copy(tmp_path,monkeypatch):
    source=tmp_path/'source.gguf';source.write_bytes(b'valid-model')
    spec={'file':'model.gguf','size':11,'sha256':hashlib.sha256(b'valid-model').hexdigest()}
    monkeypatch.setattr(model_manager,'manifest',lambda:{'models':{'test':spec}})
    dest=model_manager.install_model('test',tmp_path/'models',source)
    assert model_manager.verify(dest,spec)
    source.write_bytes(b'bad')
    with pytest.raises(ValueError):model_manager.install_model('test',tmp_path/'models',source)
    assert dest.read_bytes()==b'valid-model'


def test_hardware_detection():
    values=model_manager.hardware()
    assert values['ram_gib']>0 and values['available_gib']>=0


def test_complete_partial_download_promotes_without_network(tmp_path,monkeypatch):
    data=b'complete';target=tmp_path/'model.gguf'
    target.with_suffix('.gguf.partial').write_bytes(data)
    spec={'size':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    monkeypatch.setattr(model_manager.requests,'get',lambda *a,**k:pytest.fail('unexpected download'))
    assert model_manager.download('unused',target,spec)==target
    assert target.read_bytes()==data
