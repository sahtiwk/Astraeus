import pytest
from unittest.mock import Mock
from src.projects import project_directory,clear_history
from src.jobs import JobManager


def test_project_names_are_confined(tmp_path):
    assert project_directory(tmp_path,'team_1')==tmp_path/'projects/team_1'
    for name in ['../escape','a/b','','x'*65]:
        with pytest.raises(ValueError):project_directory(tmp_path,name)


def test_clear_is_blocked_by_live_jobs(tmp_path):
    jobs=JobManager(tmp_path/'jobs.db');vectors=Mock()
    jid=jobs.store.submit('key',{})
    with pytest.raises(ValueError):clear_history(vectors,jobs)
    vectors.collection.delete.assert_not_called()
    jobs.cancel(jid)
    vectors.collection.get.side_effect=[{'ids':['a']},{'ids':[]}]
    clear_history(vectors,jobs)
    vectors.collection.delete.assert_called_once_with(ids=['a'])
    assert jobs.store.get(jid) is None
