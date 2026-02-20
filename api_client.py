"""
=============================================================
s3_uploader.py - AWS S3 Upload Manager
Uploads clean IoT data to S3 with partitioned storage
Author: Venkata Ganesh Kumar Nethuluri
=============================================================
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class S3Uploader:
    """Manages upload of IoT sensor data to AWS S3 with partitioned paths."""

    def __init__(self):
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "iot-pipeline-data")
        self.aws_region  = os.getenv("AWS_REGION", "ap-south-1")

        self.s3_client = boto3.client("s3", region_name=self.aws_region)
        logger.info(f"S3Uploader initialized | Bucket: {self.bucket_name} | Region: {self.aws_region}")

    def upload(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload data to S3 with date-partitioned path.
        Path format: clean-data/year=YYYY/month=MM/day=DD/HH-MM-SS.json
        """
        if not data:
            logger.warning("No data to upload")
            return {"status": "skipped", "reason": "empty data"}

        now = datetime.utcnow()
        s3_key = (
            f"clean-data/"
            f"year={now.strftime('%Y')}/"
            f"month={now.strftime('%m')}/"
            f"day={now.strftime('%d')}/"
            f"{now.strftime('%H-%M-%S')}-readings.json"
        )

        payload = {
            "pipeline_version": "1.0",
            "upload_timestamp": now.isoformat(),
            "record_count": len(data),
            "records": data
        }

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=json.dumps(payload, indent=2, default=str),
                ContentType="application/json",
                Metadata={
                    "record-count": str(len(data)),
                    "upload-timestamp": now.isoformat(),
                    "pipeline": "iot-realtime-data-pipeline"
                }
            )

            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"✅ Uploaded {len(data)} records to {s3_uri}")

            return {
                "status": "success",
                "s3_key": s3_key,
                "s3_uri": s3_uri,
                "record_count": len(data),
                "timestamp": now.isoformat()
            }

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"S3 upload failed | Code: {error_code} | Key: {s3_key}")
            raise
        except BotoCoreError as e:
            logger.error(f"AWS SDK error during upload: {str(e)}")
            raise
