"""
Pruebas simples para demostrar el funcionamiento básico de pytest
"""

def test_suma():
    assert 1 + 1 == 2

def test_multiplicacion():
    assert 2 * 3 == 6

class TestOperaciones:
    def test_resta(self):
        assert 5 - 2 == 3
    
    def test_division(self):
        assert 6 / 2 == 3
        
    def test_division_entera(self):
        assert 7 // 2 == 3