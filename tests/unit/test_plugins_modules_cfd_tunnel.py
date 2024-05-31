from ...plugins.modules import cfd_tunnel

def test_cfd_tunnel():
    val = cfd_tunnel.testing()
    assert val == "Hello World"
