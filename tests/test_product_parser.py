from product_parser import product_from_attempts,product_parts

def test_generic_brand_strength_form():
    candidates,evidence=product_from_attempts([{'source':'original','page':1,'text':'Demomed™\n25 mg/10 mg\ntablets'}])
    assert candidates==['Demomed 25 mg/10 mg tablets'] and evidence

def test_combine_same_page_with_source():
    candidates,evidence=product_from_attempts([
        {'source':'original','page':1,'text':'Demomed™\nA25 mg/10 mg\ntablets'},
        {'source':'product_region','page':1,'text':'1 Demomed |\n4 25 mg/10 mg yp'}])
    assert candidates==['Demomed 25 mg/10 mg tablets']
    assert any(e['source']=='product_region' and e['field']=='strength' for e in evidence)

def test_no_cross_page_glue():
    candidates,_=product_from_attempts([
        {'source':'original','page':1,'text':'Demomed\n25 mg/10 mg'},
        {'source':'original','page':2,'text':'tablets'}])
    assert not candidates

def test_no_fixing_ocr_digits():
    parts=product_parts('Demomed\nA25 mg/10 mg\ntablets')
    assert parts['strength']==[]

def test_conflicting_strength_not_selected():
    candidates,_=product_from_attempts([
        {'source':'original','page':1,'text':'Demomed\n25 mg\ntablets'},
        {'source':'product_region','page':1,'text':'Demomed\n75 mg\ntablets'}])
    assert not candidates
