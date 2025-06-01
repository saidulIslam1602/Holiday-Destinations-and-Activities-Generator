#!/usr/bin/env python3
"""
Command-line script for managing fine-tuning operations.
Allows for fine-tuning management outside of the web interface.

Usage:
    python scripts/fine_tune_model.py --action create
    python scripts/fine_tune_model.py --action monitor --job-id ftjob-xxxxx
    python scripts/fine_tune_model.py --action list
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core import configure_logging, get_logger, FineTuningManager
from src.config import settings


def setup_logging():
    """Setup logging for the script."""
    configure_logging()
    return get_logger("fine_tune_script")


async def create_fine_tuned_model(base_model: str = "gpt-3.5-turbo"):
    """Create a new fine-tuned model."""
    logger = setup_logging()
    logger.info("Starting fine-tuning process", base_model=base_model)
    
    manager = FineTuningManager()
    
    try:
        model_id = await asyncio.get_event_loop().run_in_executor(
            None, 
            manager.full_fine_tuning_pipeline,
            base_model
        )
        
        if model_id:
            logger.info("Fine-tuning completed successfully", model_id=model_id)
            print(f"✅ Fine-tuning completed! Model ID: {model_id}")
            print(f"To use this model, set: FINE_TUNED_MODEL_ID={model_id}")
            print(f"And set: USE_FINE_TUNED_MODEL=true")
            return model_id
        else:
            logger.error("Fine-tuning failed")
            print("❌ Fine-tuning failed. Check logs for details.")
            return None
            
    except Exception as e:
        logger.error("Fine-tuning process failed", error=str(e), exc_info=True)
        print(f"❌ Fine-tuning failed: {str(e)}")
        return None


async def monitor_job(job_id: str):
    """Monitor a fine-tuning job."""
    logger = setup_logging()
    logger.info("Monitoring fine-tuning job", job_id=job_id)
    
    manager = FineTuningManager()
    
    try:
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            manager.monitor_fine_tuning_job,
            job_id
        )
        
        if result["status"] == "completed":
            model_id = result["model_id"]
            print(f"✅ Fine-tuning completed! Model ID: {model_id}")
            print(f"To use this model, set: FINE_TUNED_MODEL_ID={model_id}")
            print(f"And set: USE_FINE_TUNED_MODEL=true")
        elif result["status"] == "failed":
            print(f"❌ Fine-tuning failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"🔄 Job status: {result['status']}")
            
    except Exception as e:
        logger.error("Failed to monitor job", job_id=job_id, error=str(e))
        print(f"❌ Failed to monitor job: {str(e)}")


async def list_models():
    """List available fine-tuned models."""
    logger = setup_logging()
    logger.info("Listing fine-tuned models")
    
    manager = FineTuningManager()
    
    try:
        models = await asyncio.get_event_loop().run_in_executor(
            None,
            manager.list_fine_tuned_models
        )
        
        if models:
            print("📋 Available Fine-tuned Models:")
            print("-" * 60)
            for model in models:
                print(f"ID: {model['id']}")
                print(f"Created: {model['created']}")
                print(f"Owner: {model['owned_by']}")
                print("-" * 60)
        else:
            print("📭 No fine-tuned models available.")
            
    except Exception as e:
        logger.error("Failed to list models", error=str(e))
        print(f"❌ Failed to list models: {str(e)}")


async def generate_training_data():
    """Generate training data without fine-tuning."""
    logger = setup_logging()
    logger.info("Generating training data")
    
    manager = FineTuningManager()
    
    try:
        training_file = await asyncio.get_event_loop().run_in_executor(
            None,
            manager.generate_training_data
        )
        
        print(f"✅ Training data generated: {training_file}")
        print(f"📁 File location: {training_file}")
        
    except Exception as e:
        logger.error("Failed to generate training data", error=str(e))
        print(f"❌ Failed to generate training data: {str(e)}")


async def upload_training_file(file_path: str):
    """Upload training file to OpenAI."""
    logger = setup_logging()
    logger.info("Uploading training file", file_path=file_path)
    
    manager = FineTuningManager()
    
    try:
        file_id = await asyncio.get_event_loop().run_in_executor(
            None,
            manager.prepare_training_file,
            file_path
        )
        
        print(f"✅ Training file uploaded! File ID: {file_id}")
        print(f"To create a fine-tuning job, use: --action create-job --file-id {file_id}")
        
    except Exception as e:
        logger.error("Failed to upload training file", error=str(e))
        print(f"❌ Failed to upload training file: {str(e)}")


async def create_job(file_id: str, base_model: str = "gpt-3.5-turbo"):
    """Create a fine-tuning job with uploaded file."""
    logger = setup_logging()
    logger.info("Creating fine-tuning job", file_id=file_id, base_model=base_model)
    
    manager = FineTuningManager()
    
    try:
        job_id = await asyncio.get_event_loop().run_in_executor(
            None,
            manager.create_fine_tuned_model,
            file_id,
            base_model
        )
        
        print(f"✅ Fine-tuning job created! Job ID: {job_id}")
        print(f"To monitor progress, use: --action monitor --job-id {job_id}")
        
    except Exception as e:
        logger.error("Failed to create fine-tuning job", error=str(e))
        print(f"❌ Failed to create fine-tuning job: {str(e)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fine-tuning management for Holiday Destinations Generator"
    )
    
    parser.add_argument(
        "--action",
        choices=[
            "create", "monitor", "list", "generate-data", 
            "upload-file", "create-job"
        ],
        required=True,
        help="Action to perform"
    )
    
    parser.add_argument(
        "--base-model",
        default="gpt-3.5-turbo",
        help="Base model for fine-tuning (default: gpt-3.5-turbo)"
    )
    
    parser.add_argument(
        "--job-id",
        help="Fine-tuning job ID (for monitoring)"
    )
    
    parser.add_argument(
        "--file-path",
        help="Path to training file (for uploading)"
    )
    
    parser.add_argument(
        "--file-id",
        help="OpenAI file ID (for creating job)"
    )
    
    args = parser.parse_args()
    
    # Validate OpenAI API key
    if not settings.openai_api_key:
        print("❌ OpenAI API key not found. Please set OPENAI_API_KEY or create api_key.txt")
        sys.exit(1)
    
    print(f"🚀 Holiday Destinations Generator - Fine-tuning Manager")
    print(f"📊 Action: {args.action}")
    print(f"🤖 Base Model: {args.base_model}")
    print(f"🔑 API Key: {settings.openai_api_key[:10]}...")
    print("-" * 60)
    
    try:
        if args.action == "create":
            asyncio.run(create_fine_tuned_model(args.base_model))
            
        elif args.action == "monitor":
            if not args.job_id:
                print("❌ Job ID required for monitoring. Use --job-id")
                sys.exit(1)
            asyncio.run(monitor_job(args.job_id))
            
        elif args.action == "list":
            asyncio.run(list_models())
            
        elif args.action == "generate-data":
            asyncio.run(generate_training_data())
            
        elif args.action == "upload-file":
            if not args.file_path:
                print("❌ File path required for uploading. Use --file-path")
                sys.exit(1)
            asyncio.run(upload_training_file(args.file_path))
            
        elif args.action == "create-job":
            if not args.file_id:
                print("❌ File ID required for creating job. Use --file-id")
                sys.exit(1)
            asyncio.run(create_job(args.file_id, args.base_model))
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 