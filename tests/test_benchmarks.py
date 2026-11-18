import importlib.util
from pathlib import Path


def test_generator_is_seeded_and_line_numbers_are_real(tmp_path):
    spec=importlib.util.spec_from_file_location('generator',Path(__file__).parent/'generate_mock_data.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    a=tmp_path/'a.log';b=tmp_path/'b.log'
    truth=module.generate_mock_logs(str(a),num_lines=30,anomaly_frequency=10,seed=7)
    other=module.generate_mock_logs(str(b),num_lines=30,anomaly_frequency=10,seed=7)
    assert truth==other and a.read_bytes()==b.read_bytes()
    lines=a.read_text().splitlines()
    assert len(lines)==42
    for incident in truth:
        incident_lines=lines[incident['start_line']-1:incident['end_line']]
        assert len(incident_lines)==5
        assert incident_lines[0].startswith(incident['start_ts'])
        assert incident_lines[-1].startswith(incident['end_ts'])
