import importlib.util,unittest
from pathlib import Path
p=Path('/root/tokenoskobi_clean_v1/tools/tokenoskobi_product_slice_02_server.py');s=importlib.util.spec_from_file_location('m',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class T(unittest.TestCase):
 def test_address(self):self.assertTrue(m.ADDR.fullmatch('0x'+'a'*40));self.assertFalse(m.ADDR.fullmatch('0x12'))
 def test_uint(self):self.assertEqual(m.uint('0x12'),18)
 def test_text(self):self.assertEqual(m.text('0x'+b'TKN'.ljust(32,b'\0').hex()),'TKN')
 def test_block(self):self.assertEqual(m.decide({'code_exists':False},{'selected_pool':None},{},{'fresh':False},{'public_rpc_ok':1,'hybrid_ready':False})['decision'],'BLOCK')
 def test_authority(self):self.assertTrue(all(v is False for v in m.CFG['authority'].values()))
if __name__=='__main__':unittest.main()
