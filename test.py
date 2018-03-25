import unittest

from KSPUtils.ConfigNode import ConfigNode


class MyTestCase(unittest.TestCase):
    def test_something(self):
        # create
        n = ConfigNode('test')
        n.AddValue('a', 1)
        n.AddValue('b', 2)
        n1 = n.AddNode('sub')
        n1.AddValue('c', 3)
        n1.AddValue('d', 4)
        print()
        n
        print()
        # parse
        n2 = ConfigNode('parsed')
        n2.Parse(str(n) + str(n))
        print()
        n2
        print()
        # get
        print()
        n['a']
        print()
        n.GetValue('b')
        print()
        n.GetNode('sub')


if __name__ == '__main__':
    unittest.main()
