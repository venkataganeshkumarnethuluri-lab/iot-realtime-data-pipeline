"""
=============================================================
main.py - IoT Real-Time Data Pipeline Entry Point
Author: Venkata Ganesh Kumar Nethuluri
=============================================================
"""

import argparse
import logging
import sys
import time
from datetime import datetime

from ingestion.api_client import IoTApiClient
from ingestion.data_validator import DataValidator
from ingestion.batch_processor import BatchProcessor
from anomaly.detector import AnomalyDetector
from anomaly.alert_handler import AlertHandler
from storage.s3_uploader import S3Uploader
from monitoring.pipeline_monitor import PipelineMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"logs/pipeline_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)
logger = logging.getLogger(__name__)


def run_realtime_pipeline():
    """Run the pipeline in real-time streaming mode."""
    logger.info("=" * 60)
    logger.info("🚀 Starting IoT Real-Time Data Pipeline")
    logger.info("=" * 60)

    api_client     = IoTApiClient()
    validator      = DataValidator()
    detector       = AnomalyDetector()
    alert_handler  = AlertHandler()
    s3_uploader    = S3Uploader()
    monitor        = PipelineMonitor()

    POLL_INTERVAL = 30  # seconds

    while True:
        cycle_start = time.time()
        monitor.record_cycle_start()

        try:
            # Step 1: Fetch data from IoT sensors via REST API
            logger.info("📡 Fetching sensor data from IoT API...")
            raw_data = api_client.fetch_latest_readings()
            logger.info(f"   Fetched {len(raw_data)} sensor records")

            # Step 2: Validate data schema and quality
            logger.info("🔍 Validating data...")
            valid_data, invalid_records = validator.validate(raw_data)
            
            if invalid_records:
                logger.warning(f"   ⚠️  {len(invalid_records)} invalid records found and excluded")
                monitor.record_validation_failures(len(invalid_records))

            logger.info(f"   ✅ {len(valid_data)} records passed validation")

            # Step 3: Run anomaly detection
            logger.info("🔎 Running anomaly detection...")
            clean_data, anomalies = detector.detect(valid_data)

            if anomalies:
                logger.warning(f"   ⚠️  {len(anomalies)} anomalies detected!")
                alert_handler.send_alerts(anomalies)
                monitor.record_anomalies(len(anomalies))

            logger.info(f"   ✅ {len(clean_data)} clean records")

            # Step 4: Upload clean data to S3
            logger.info("☁️  Uploading clean data to S3...")
            upload_result = s3_uploader.upload(clean_data)
            logger.info(f"   ✅ Uploaded: {upload_result['s3_key']}")

            # Step 5: Record pipeline metrics
            cycle_duration = time.time() - cycle_start
            monitor.record_cycle_success(
                records_processed=len(raw_data),
                records_clean=len(clean_data),
                anomaly_count=len(anomalies) if anomalies else 0,
                duration_seconds=cycle_duration
            )

            logger.info(f"✅ Cycle complete in {cycle_duration:.2f}s | Sleeping {POLL_INTERVAL}s...")

        except KeyboardInterrupt:
            logger.info("🛑 Pipeline stopped by user")
            break
        except Exception as e:
            logger.error(f"❌ Pipeline error: {str(e)}", exc_info=True)
            monitor.record_cycle_failure(str(e))

        time.sleep(POLL_INTERVAL)


def run_batch_pipeline(batch_date: str):
    """Run the pipeline in batch mode for a specific date."""
    logger.info(f"📦 Starting batch pipeline for date: {batch_date}")
    
    processor = BatchProcessor()
    processor.process_date(batch_date)
    
    logger.info("✅ Batch processing complete!")


def main():
    parser = argparse.ArgumentParser(description="IoT Real-Time Data Pipeline")
    parser.add_argument(
        "--mode",
        choices=["realtime", "batch"],
        default="realtime",
        help="Pipeline mode: realtime or batch"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date for batch mode (format: YYYY-MM-DD)"
    )
    args = parser.parse_args()

    if args.mode == "realtime":
        run_realtime_pipeline()
    elif args.mode == "batch":
        if not args.date:
            logger.error("--date required for batch mode")
            sys.exit(1)
        run_batch_pipeline(args.date)


if __name__ == "__main__":
    main()
