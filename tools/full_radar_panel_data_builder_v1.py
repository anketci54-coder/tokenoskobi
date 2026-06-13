#!/usr/bin/env python3
"""
full_radar_panel_data_builder_v1.py

Generic reusable full radar panel data builder.
This skeleton is dry-run safe by design.
It uses read-only DB access, builds in-memory panel products, and does not perform network access.
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PanelProductContract:
    file: str
    purpose: str
    contract_version: str = "full_radar_panel_data_v1"


@dataclass
class PanelBuildResult:
    ok: bool
    product_count: int
    validation_error_count: int
    products: List[Dict[str, Any]]
    warnings: List[str]


class ReadOnlyDBAdapter:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)

    def count_or_none(self, table_name: str) -> Optional[int]:
        with self.connect() as con:
            try:
                return con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            except Exception:
                return None


class PanelQualityValidator:
    forbidden_user_visible_fields = {
        "token_uid",
        "pair_uid",
        "raw_hash",
        "debug_id",
        "internal_id",
        "secret",
        "private_key",
    }

    required_top_level = {"meta", "product", "items", "quality"}

    def validate(self, product: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        missing = self.required_top_level - set(product.keys())
        if missing:
            errors.append("missing_top_level:" + ",".join(sorted(missing)))

        meta = product.get("meta", {})
        if "generated_at_utc" not in meta:
            errors.append("missing_meta_generated_at_utc")
        if "data_contract_version" not in meta:
            errors.append("missing_meta_data_contract_version")
        if "is_mock" not in meta:
            errors.append("missing_meta_is_mock")

        visible_text = json.dumps(product.get("items", []), ensure_ascii=False)
        for forbidden in self.forbidden_user_visible_fields:
            if forbidden in visible_text:
                errors.append("forbidden_user_visible_field:" + forbidden)

        return errors


class PanelDataBuilder:
    def __init__(self, db_path: str):
        self.db = ReadOnlyDBAdapter(db_path)
        self.validator = PanelQualityValidator()
        self.contracts = [
            PanelProductContract("full_radar_main_panel_data_v1.json", "Ana beyin paneli"),
            PanelProductContract("critical_alerts_data_v1.json", "Kritik uyarılar"),
            PanelProductContract("tracked_candidates_data_v1.json", "Takipteki adaylar"),
            PanelProductContract("active_paper_positions_data_v1.json", "Aktif paper işlemler"),
            PanelProductContract("economic_calendar_data_v1.json", "Ekonomik takvim"),
            PanelProductContract("wallet_whale_radar_data_v1.json", "Balina / cüzdan radar"),
            PanelProductContract("token_lifecycle_data_v1.json", "Token lifecycle"),
            PanelProductContract("morgue_autopsy_data_v1.json", "Morg / otopsi"),
            PanelProductContract("risk_mev_data_v1.json", "Risk / MEV"),
            PanelProductContract("fusion_decision_data_v1.json", "Fusion kararları"),
            PanelProductContract("ai_calibration_summary_data_v1.json", "AI kalibrasyon özeti"),
        ]

    def now_utc(self) -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def read_module_summary(self, adapter_name: str) -> Dict[str, Any]:
        return {
            "adapter": adapter_name,
            "status": "planned",
            "count": None,
            "freshness_status": "NO_REAL_DATA_IN_DRYRUN",
        }

    def build_product(self, contract: PanelProductContract) -> Dict[str, Any]:
        return {
            "meta": {
                "generated_at_utc": self.now_utc(),
                "data_contract_version": contract.contract_version,
                "is_mock": True,
                "source": "FULL_RADAR_PANEL_DATA_BUILDER_V1_DRYRUN",
                "freshness_status": "DRYRUN_ONLY",
            },
            "product": asdict(contract),
            "items": [],
            "quality": {
                "has_meta": True,
                "has_contract_version": True,
                "has_mock_flag": True,
                "has_no_debug_uid_exposure": True,
                "stale_to_main_panel_blocked": True,
            },
        }

    def build_all_products(self) -> PanelBuildResult:
        products: List[Dict[str, Any]] = []
        errors: List[str] = []

        for contract in self.contracts:
            product = self.build_product(contract)
            errors.extend(self.validator.validate(product))
            products.append(product)

        return PanelBuildResult(
            ok=(len(errors) == 0),
            product_count=len(products),
            validation_error_count=len(errors),
            products=products,
            warnings=[],
        )

    def write_staging_files_only_when_approved(self, *_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("Writing is disabled in this dry-run-safe builder skeleton.")


def load_config() -> Dict[str, Any]:
    return {
        "mode": "dryrun_safe",
        "network_enabled": False,
        "db_write_enabled": False,
        "active_panel_apply_enabled": False,
    }


def main() -> int:
    cfg = load_config()
    builder = PanelDataBuilder("/root/tokenoskobi_clean_v1/data/tokenoskobi_clean_v1.sqlite")
    result = builder.build_all_products()
    summary = {
        "ok": result.ok,
        "product_count": result.product_count,
        "validation_error_count": result.validation_error_count,
        "config": cfg,
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
