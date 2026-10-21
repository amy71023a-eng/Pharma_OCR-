import pytest
from llm_contract import validate_citations

def test_valid_citation():
    assert validate_citations({'answer':'文件內容摘要','source_ids':['S1'],'abstained':False},{'S1'}).source_ids==['S1']

@pytest.mark.parametrize('ids',[[],['S999']])
def test_no_fabricated_citations(ids):
    with pytest.raises(ValueError):validate_citations({'answer':'不可靠回答','source_ids':ids,'abstained':False},{'S1'})

def test_abstain_does_not_leak_unverified_answer():
    r=validate_citations({'answer':'猜測的內容','source_ids':[],'abstained':True},{'S1'})
    assert r.abstained and '猜測' not in r.answer

def test_malformed_response():
    with pytest.raises(ValueError):validate_citations({'answer':'x','source_ids':'S1','abstained':'false'},{'S1'})
