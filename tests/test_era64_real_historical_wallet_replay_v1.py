from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.era64_real_historical_wallet_replay_v1 import (
    as_timestamp,
    bounded_graph_events,
    extract_relation,
    extract_trade,
    inspect_database,
    replay_trade_groups,
    run,
    valid_wallet,
)

A="0x"+"1"*40
B="0x"+"2"*40
T="0x"+"3"*40


class Era64RealHistoricalReplayTests(unittest.TestCase):
    def make_db(self, root: Path) -> Path:
        path=root/"data"/"tokenoskobi_clean_v1.sqlite"
        path.parent.mkdir(parents=True,exist_ok=True)
        conn=sqlite3.connect(path)
        conn.execute("CREATE TABLE wallet_transfer_events(from_wallet TEXT,to_wallet TEXT,tx_hash TEXT,timestamp INTEGER,block_number INTEGER,amount REAL,token TEXT)")
        conn.execute("INSERT INTO wallet_transfer_events VALUES(?,?,?,?,?,?,?)",(A,B,"0xabc",1000,10,25.0,T))
        conn.execute("CREATE TABLE wallet_trade_events(wallet TEXT,token TEXT,side TEXT,tx_hash TEXT,quantity REAL,price REAL,fee REAL,gas REAL,timestamp INTEGER)")
        conn.execute("INSERT INTO wallet_trade_events VALUES(?,?,?,?,?,?,?,?,?)",(A,T,"BUY","0xbuy",2.0,10.0,0.1,0.1,1000))
        conn.execute("INSERT INTO wallet_trade_events VALUES(?,?,?,?,?,?,?,?,?)",(A,T,"SELL","0xsell",2.0,15.0,0.1,0.1,2000))
        conn.commit(); conn.close()
        return path

    def test_01_wallet_validation(self):
        self.assertEqual(valid_wallet(A),A)
        self.assertIsNone(valid_wallet("bad"))

    def test_02_timestamp_normalizes_milliseconds(self):
        self.assertEqual(as_timestamp(1_700_000_000_000),1_700_000_000)

    def test_03_relation_extracts_real_fields(self):
        row={"from_wallet":A,"to_wallet":B,"tx_hash":"0xabc","timestamp":1,"block_number":2,"amount":3,"token":T}
        event,gap=extract_relation("x.db","wallet_transfer_events",1,row)
        self.assertIsNone(gap); self.assertEqual(event["from_wallet"],A)

    def test_04_relation_missing_tx_is_rejected(self):
        row={"from_wallet":A,"to_wallet":B,"timestamp":1,"block_number":2,"amount":3}
        event,gap=extract_relation("x.db","wallet_transfer_events",1,row)
        self.assertIsNone(event); self.assertEqual(gap,"MISSING_RELATION_COLUMNS")

    def test_05_trade_requires_complete_cost_fields(self):
        row={"wallet":A,"token":T,"side":"BUY","tx_hash":"x","quantity":1,"price":1,"timestamp":1}
        event,gap=extract_trade("x.db","wallet_trade_events",1,row)
        self.assertIsNone(event); self.assertEqual(gap,"MISSING_COST_COMPLETE_TRADE_COLUMNS")

    def test_06_bounded_graph_respects_limits(self):
        events=[]
        for i in range(10):
            events.append({"from_wallet":A,"to_wallet":B,"relation_type":"TRANSFER","tx_hash":str(i),"evidence_id":str(i),"token":"T","amount":1,"timestamp":i,"block_number":i})
        self.assertEqual(len(bounded_graph_events(events,2,3)),3)

    def test_07_trade_replay_is_cost_adjusted(self):
        rows=[
            {"wallet":A,"token":"T","side":"BUY","tx_hash":"b","evidence_id":"1","quantity":1,"price":10,"fee":1,"gas":1,"timestamp":1},
            {"wallet":A,"token":"T","side":"SELL","tx_hash":"s","evidence_id":"2","quantity":1,"price":15,"fee":1,"gas":1,"timestamp":2},
        ]
        result=replay_trade_groups(rows,10)
        self.assertEqual(result["closed_cycle_count"],1)
        self.assertLess(result["cycles"][0]["pnl"],5)

    def test_08_oversell_group_fails_closed(self):
        rows=[{"wallet":A,"token":"T","side":"SELL","tx_hash":"s","evidence_id":"2","quantity":1,"price":15,"fee":0,"gas":0,"timestamp":2}]
        result=replay_trade_groups(rows,10)
        self.assertEqual(result["rejected_group_count"],1)

    def test_09_sqlite_is_read_only_and_real_replay_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); self.make_db(root)
            config={"database_candidates":["data/tokenoskobi_clean_v1.sqlite"],"maximum_tables_per_database":10,"maximum_rows_per_table":100,"maximum_graph_nodes":16,"maximum_graph_edges":16,"maximum_trade_groups":16}
            cfg=root/"config.json"; cfg.write_text(json.dumps(config),encoding="utf-8")
            summary,_=run(root,cfg)
            self.assertEqual(summary["status"],"REAL_HISTORICAL_REPLAY_VALIDATED")
            self.assertEqual(summary["closed_cycle_count"],1)

    def test_10_authority_and_source_are_safe(self):
        source=Path("tools/era64_real_historical_wallet_replay_v1.py").read_text(encoding="utf-8")
        for forbidden in ("requests.","urllib.","subprocess", "os.system", "shell=True", "eval(", "exec("):
            self.assertNotIn(forbidden,source)
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"x.sqlite"; sqlite3.connect(path).close()
            result=inspect_database(path,10,10)
            self.assertEqual(result["scanned_row_count"],0)


if __name__ == "__main__":
    unittest.main()
