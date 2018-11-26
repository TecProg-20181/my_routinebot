import pytest
from handletask import HandleTask

def test_task_condition():
    a = HandleTask()
    assert a.task_condition('DOING', 'DOING') == True