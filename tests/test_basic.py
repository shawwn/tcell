import unittest

import tcell

cells = tcell.scheme_empty_cell_table()

class TestCase(unittest.TestCase):
    def test_get(self):
        foo = tcell.scheme_make_thread_cell("foo", True)
        self.assertEqual("foo", tcell.scheme_thread_cell_get(foo, cells))

    def test_set(self):
        foo = tcell.scheme_make_thread_cell("foo", True)
        self.assertEqual("foo", tcell.scheme_thread_cell_get(foo, cells))
        tcell.scheme_thread_cell_set(foo, cells, "foo2")
        self.assertEqual("foo2", tcell.scheme_thread_cell_get(foo, cells))

    def test_inherit(self):
        inherited = tcell.scheme_make_thread_cell("inherited", True)
        noinherit = tcell.scheme_make_thread_cell("noinherit", False)
        self.assertEqual("inherited", tcell.scheme_thread_cell_get(inherited, cells))
        self.assertEqual("noinherit", tcell.scheme_thread_cell_get(noinherit, cells))
        cells2 = tcell.scheme_inherit_cells(cells)
        self.assertEqual("inherited", tcell.scheme_thread_cell_get(inherited, cells2))
        self.assertEqual("noinherit", tcell.scheme_thread_cell_get(noinherit, cells2))
        # cells modified after cells2 have been created shouldn't inherit a new value
        tcell.scheme_thread_cell_set(inherited, cells, "new value")
        tcell.scheme_thread_cell_set(noinherit, cells, "new value")
        self.assertEqual("inherited", tcell.scheme_thread_cell_get(inherited, cells2))
        self.assertEqual("noinherit", tcell.scheme_thread_cell_get(noinherit, cells2))
        cells3 = tcell.scheme_inherit_cells(cells)
        self.assertEqual("new value", tcell.scheme_thread_cell_get(inherited, cells3))
        self.assertEqual("noinherit", tcell.scheme_thread_cell_get(noinherit, cells3))
        self.assertEqual("new value", tcell.scheme_thread_cell_get(inherited, cells))
        self.assertEqual("new value", tcell.scheme_thread_cell_get(noinherit, cells))


if __name__ == '__main__':
    unittest.main()
