import unittest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from server import valid, records, purge

class RelayTests(unittest.TestCase):
    def setUp(self):
        self.x = dict(server='a'*64, uuid='ab2468b0-f0b6-4870-bda8-ff1c75f48125', token='b'*64,
                      name='TestUser', cosmetics=[dict(name='Wings',style='Raven')])
    def test_valid(self): self.assertTrue(valid(self.x))
    def test_bad_username(self):
        self.x['name']='bad\nname'; self.assertFalse(valid(self.x))
    def test_no_token(self):
        self.x.pop('token'); self.assertFalse(valid(self.x))
    def test_bad_cosmetic(self):
        self.x['cosmetics']=[{'name':'x'*100,'style':''}]; self.assertFalse(valid(self.x))
    def test_expiry(self):
        records[('a'*64,self.x['uuid'])]={'time':0}
        purge(50);self.assertEqual(len(records),0)

if __name__ == '__main__': unittest.main()
