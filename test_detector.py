"""
=============================================================
data_validator.py - Data Schema & Quality Validator
Validates incoming IoT sensor data before processing
Author: Venkata Ganesh Kumar Nethuluri
=============================================================
"""

import logging
from typing import List, Dict, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ["sensor_id", "timestamp", "temperature"]

FIELD_TYPES = {
    "sensor_id":   str,
    "timestamp":   str,
    "temperature": (int, float),
    "humidity":    (int, float),
    "pressure":    (int, float),
    "vibration":   (int, float),
    "voltage":     (int, float),
}


class DataValidator:
    """Validates IoT sensor data for schema compliance and data quality."""

    def validate(self, records: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Validate a list of sensor records.
        Returns (valid_records, invalid_records).
        """
        valid = []
        invalid = []

        for record in records:
            is_valid, errors = self._validate_record(record)
            if is_valid:
                valid.append(record)
            else:
                invalid.append({"record": record, "errors": errors})
                logger.debug(f"Invalid record {record.get('sensor_id', 'unknown')}: {errors}")

        logger.info(f"Validation | Total: {len(records)} | Valid: {len(valid)} | Invalid: {len(invalid)}")
        return valid, invalid

    def _validate_record(self, record: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in record or record[field] is None:
                errors.append(f"Missing required field: '{field}'")

        # Check field types
        for field, expected_type in FIELD_TYPES.items():
            if field in record and record[field] is not None:
                if not isinstance(record[field], expected_type):
                    errors.append(f"Invalid type for '{field}': expected {expected_type}, got {type(record[field])}")

        # Check timestamp format
        if "timestamp" in record and record["timestamp"]:
            try:
                datetime.fromisoformat(str(record["timestamp"]).replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"Invalid timestamp format: '{record['timestamp']}'")

        # Check sensor_id not empty
        if "sensor_id" in record and record["sensor_id"] is not None:
            if str(record["sensor_id"]).strip() == "":
                errors.append("sensor_id cannot be empty")

        return len(errors) == 0, errors
