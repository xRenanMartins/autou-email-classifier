"""
Teste simples para verificar se o pytest está funcionando.
"""


def test_simple():
    """Teste simples que sempre passa."""
    assert True


def test_math():
    """Teste de matemática básica."""
    assert 2 + 2 == 4
    assert 3 * 3 == 9


def test_strings():
    """Teste de strings."""
    assert "hello" + " " + "world" == "hello world"
    assert len("test") == 4


class TestSimpleClass:
    """Classe de teste simples."""

    def test_instance(self):
        """Teste de instância."""
        assert self is not None

    def test_method(self):
        """Teste de método."""
        result = self.simple_method()
        assert result == "success"

    def simple_method(self):
        """Método simples para teste."""
        return "success"
