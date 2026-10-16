"""Temporary staging databases; never read or write a deployed database.

The canary fixture replays the checked-in 191-event capture. The historical
fixture uses three explicitly synthetic transfers and two synthetic receipts;
it exercises persistence, not the old 367-event production acceptance claim.
"""
import json
import tempfile
from contextlib import contextmanager, ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.legacy import era64g_bounded_staging_database_backfill_v1 as canary
from scripts.legacy import era64i_bounded_historical_wallet_event_backfill_v1 as historical
from scripts.legacy import era64j_historical_transfer_receipt_cost_enrichment_v1 as receipts

REPO = Path(__file__).resolve().parents[1]


@contextmanager
def canary_database():
    with tempfile.TemporaryDirectory(prefix="tokenoskobi_canary_test_") as directory:
        root = Path(directory)
        database = root / "runtime/era64g/wallet_events_staging_v1.sqlite3"
        with patch.object(canary, "ROOT", root):
            result = canary.import_events(
                REPO / "config/era64g_bounded_staging_database_backfill_v1.json",
                REPO / "data/replay/era64f_bounded_readonly_wallet_event_canary_v1.json",
                database,
            )
        control = root / "data/control/era64g_bounded_staging_database_backfill_v1.json"
        control.parent.mkdir(parents=True)
        control.write_text(json.dumps(result))
        yield SimpleNamespace(root=root, database=database)


@contextmanager
def historical_database():
    with ExitStack() as stack:
        root = Path(stack.enter_context(tempfile.TemporaryDirectory(
            prefix="tokenoskobi_historical_test_")))
        stack.enter_context(patch.object(historical, "ROOT", root))
        stack.enter_context(patch.object(receipts, "ROOT", root))
        database = root / "runtime/era64i/historical_wallet_transfer_staging_v1.sqlite3"
        token = "0x55d398326f99059ff775485246999027b3197955"
        addresses = ["0x" + char * 40 for char in ("0", "a", "b")]
        block_hash = "0x" + "1" * 64
        block = {"number": "0x64", "hash": block_hash, "timestamp": "0x6553f100"}
        events = []
        for index, (sender, recipient) in enumerate(((0, 1), (1, 2), (2, 1))):
            log = {
                "topics": [historical.TRANSFER_TOPIC,
                           "0x" + addresses[sender][2:].rjust(64, "0"),
                           "0x" + addresses[recipient][2:].rjust(64, "0")],
                "address": token, "transactionHash": "0x" + str(2 + index // 2) * 64,
                "blockHash": block_hash, "blockNumber": "0x64",
                "logIndex": hex(index), "data": hex(100 + index),
            }
            events.append(historical.build_event(log, block, "fixture.invalid"))
        scan = {"start_block": 100, "end_block": 100,
                "scanned_chunk_count": 1, "sampled_block_count": 1}
        first = historical.write_events(database, events, scan)
        second = historical.write_events(database, events, scan)
        assert first["inserted_event_count"] == 3
        assert second["inserted_event_count"] == 0
        assert second["deduplicated_event_count"] == 3
        total, sources = receipts.load_source_transactions(
            database, "era64i_historical_wallet_transfer_staging_v1", 10, 10)

        class FixtureRPC:
            last_endpoint_host = "fixture.invalid"

            def call(self, method, arguments):
                assert method == "eth_getTransactionReceipt"
                return {
                    "transactionHash": arguments[0], "blockHash": block_hash,
                    "blockNumber": "0x64", "gasUsed": hex(21000),
                    "effectiveGasPrice": hex(3), "status": "0x1",
                    "cumulativeGasUsed": hex(42000), "transactionIndex": "0x0",
                    "from": addresses[1], "to": addresses[2], "contractAddress": None,
                }

        enrichments = [receipts.fetch_enrichment(FixtureRPC(), source) for source in sources]
        first = receipts.write_enrichments(database, total, enrichments)
        second = receipts.write_enrichments(database, total, enrichments)
        assert first["inserted_receipt_count"] == 2
        assert second["inserted_receipt_count"] == 0
        assert second["deduplicated_receipt_count"] == 2
        yield SimpleNamespace(root=root, database=database)
