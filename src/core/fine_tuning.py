"""
Fine-tuning module for domain-specific travel destination generation.
Handles training data preparation, model fine-tuning, and deployment.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

import openai

from src.config import settings
from src.core.logging import LoggerMixin
from src.models import ThemeType


class FineTuningManager(LoggerMixin):
    """Manages fine-tuning operations for travel destination models."""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.training_data_dir = Path("training_data")
        self.model_artifacts_dir = Path("fine_tuned_models")
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        self.training_data_dir.mkdir(exist_ok=True)
        self.model_artifacts_dir.mkdir(exist_ok=True)
    
    def generate_training_data(self, num_samples_per_theme: int = 50) -> str:
        """Generate comprehensive training data for each theme."""
        
        training_examples = []
        
        # Define comprehensive training data for each theme
        training_data = {
            ThemeType.SPORTS: [
                {
                    "input": "Generate 3 Sports destinations around the world",
                    "destinations": [
                        {
                            "place": "Whistler",
                            "country": "Canada",
                            "description": "World-renowned ski resort and host of 2010 Winter Olympics, offering exceptional winter sports and mountain biking.",
                            "best_time_to_visit": "December to April for skiing, June to September for summer activities",
                            "coordinates": {"lat": 50.1163, "lng": -122.9574},
                            "rating": 4.7
                        },
                        {
                            "place": "Chamonix",
                            "country": "France",
                            "description": "World-renowned ski resort and mountaineering hub in the French Alps, home to extreme skiing and climbing.",
                            "best_time_to_visit": "December to April (skiing), June to September (climbing)",
                            "coordinates": {"lat": 45.9237, "lng": 6.8694},
                            "rating": 4.7
                        },
                        {
                            "place": "Wanaka",
                            "country": "New Zealand",
                            "description": "Adventure sports capital offering skydiving, bungee jumping, skiing, and extreme sports in stunning alpine setting.",
                            "best_time_to_visit": "December to March (summer), June to August (skiing)",
                            "coordinates": {"lat": -44.7, "lng": 169.1},
                            "rating": 4.6
                        }
                    ]
                },
                {
                    "input": "Generate 2 Sports destinations for water activities",
                    "destinations": [
                        {
                            "place": "Gold Coast",
                            "country": "Australia", 
                            "description": "Premier surfing destination with perfect waves, beautiful beaches, and excellent water sports facilities.",
                            "best_time_to_visit": "April to October",
                            "coordinates": {"lat": -28.0167, "lng": 153.4000},
                            "rating": 4.5
                        },
                        {
                            "place": "Maui",
                            "country": "United States",
                            "description": "World-class windsurfing and kitesurfing destination with consistent trade winds and perfect conditions.",
                            "best_time_to_visit": "April to October",
                            "coordinates": {"lat": 20.7984, "lng": -156.3319},
                            "rating": 4.8
                        }
                    ]
                }
            ],
            
            ThemeType.HISTORICAL_PLACE: [
                {
                    "input": "Generate 3 Historical Place destinations around the world",
                    "destinations": [
                        {
                            "place": "Angkor Wat",
                            "country": "Cambodia",
                            "description": "Magnificent 12th-century temple complex and UNESCO World Heritage site, representing the pinnacle of Khmer architecture.",
                            "best_time_to_visit": "November to March",
                            "coordinates": {"lat": 13.4125, "lng": 103.8670},
                            "rating": 4.9
                        },
                        {
                            "place": "Petra",
                            "country": "Jordan",
                            "description": "Ancient Nabataean city carved into rose-red sandstone cliffs, one of the New Seven Wonders of the World.",
                            "best_time_to_visit": "March to May, September to November",
                            "coordinates": {"lat": 30.3285, "lng": 35.4444},
                            "rating": 4.8
                        },
                        {
                            "place": "Machu Picchu",
                            "country": "Peru",
                            "description": "Mysterious Inca citadel perched high in the Andes, showcasing remarkable ancient engineering and architecture.",
                            "best_time_to_visit": "May to September",
                            "coordinates": {"lat": -13.1631, "lng": -72.5450},
                            "rating": 4.9
                        }
                    ]
                },
                {
                    "input": "Generate 2 Historical Place destinations in Europe",
                    "destinations": [
                        {
                            "place": "Stonehenge",
                            "country": "United Kingdom",
                            "description": "Mysterious prehistoric monument dating back 5,000 years, one of the world's most famous ancient sites.",
                            "best_time_to_visit": "May to September",
                            "coordinates": {"lat": 51.1789, "lng": -1.8262},
                            "rating": 4.3
                        },
                        {
                            "place": "Acropolis",
                            "country": "Greece",
                            "description": "Ancient citadel overlooking Athens, featuring the iconic Parthenon and representing the birthplace of democracy.",
                            "best_time_to_visit": "April to June, September to October",
                            "coordinates": {"lat": 37.9715, "lng": 23.7267},
                            "rating": 4.6
                        }
                    ]
                }
            ],
            
            ThemeType.NATURAL_ATTRACTION: [
                {
                    "input": "Generate 3 Natural Attraction destinations around the world",
                    "destinations": [
                        {
                            "place": "Torres del Paine",
                            "country": "Chile",
                            "description": "Spectacular national park in Patagonia featuring dramatic granite towers, glacial lakes, and diverse wildlife.",
                            "best_time_to_visit": "October to April",
                            "coordinates": {"lat": -51.0, "lng": -73.0},
                            "rating": 4.8
                        },
                        {
                            "place": "Banff National Park",
                            "country": "Canada",
                            "description": "Pristine wilderness in the Canadian Rockies with turquoise lakes, snow-capped peaks, and abundant wildlife.",
                            "best_time_to_visit": "June to August",
                            "coordinates": {"lat": 51.4968, "lng": -115.9281},
                            "rating": 4.7
                        },
                        {
                            "place": "Serengeti",
                            "country": "Tanzania",
                            "description": "Vast savanna ecosystem famous for the Great Migration and exceptional wildlife viewing opportunities.",
                            "best_time_to_visit": "June to October",
                            "coordinates": {"lat": -2.3333, "lng": 34.8333},
                            "rating": 4.9
                        }
                    ]
                },
                {
                    "input": "Generate 2 Natural Attraction destinations with waterfalls",
                    "destinations": [
                        {
                            "place": "Iguazu Falls",
                            "country": "Argentina/Brazil",
                            "description": "Spectacular waterfall system with 275 individual falls, considered one of the New Seven Wonders of Nature.",
                            "best_time_to_visit": "March to May, August to November",
                            "coordinates": {"lat": -25.6953, "lng": -54.4367},
                            "rating": 4.9
                        },
                        {
                            "place": "Victoria Falls",
                            "country": "Zambia/Zimbabwe",
                            "description": "Massive waterfall on the Zambezi River, known as 'The Smoke That Thunders' with incredible power and beauty.",
                            "best_time_to_visit": "April to October",
                            "coordinates": {"lat": -17.9243, "lng": 25.8572},
                            "rating": 4.8
                        }
                    ]
                }
            ],
            
            ThemeType.SCIENTIFIC: [
                {
                    "input": "Generate 3 Scientific destinations around the world",
                    "destinations": [
                        {
                            "place": "Atacama Desert",
                            "country": "Chile",
                            "description": "World's driest non-polar desert, ideal for astronomical observations with numerous world-class observatories.",
                            "best_time_to_visit": "March to May, September to November",
                            "coordinates": {"lat": -24.5, "lng": -69.25},
                            "rating": 4.6
                        },
                        {
                            "place": "CERN",
                            "country": "Switzerland",
                            "description": "European research organization operating the world's largest particle physics laboratory and the Large Hadron Collider.",
                            "best_time_to_visit": "Year-round",
                            "coordinates": {"lat": 46.2333, "lng": 6.0500},
                            "rating": 4.7
                        },
                        {
                            "place": "Galápagos Islands",
                            "country": "Ecuador",
                            "description": "Living laboratory of evolution where Darwin developed his theory, featuring unique endemic species and ecosystems.",
                            "best_time_to_visit": "December to May",
                            "coordinates": {"lat": -0.9538, "lng": -91.0},
                            "rating": 4.9
                        }
                    ]
                },
                {
                    "input": "Generate 2 Scientific destinations for space exploration",
                    "destinations": [
                        {
                            "place": "Kennedy Space Center",
                            "country": "United States",
                            "description": "America's spaceport with historic launch sites, Space Shuttle exhibits, and active rocket launches.",
                            "best_time_to_visit": "October to April",
                            "coordinates": {"lat": 28.5721, "lng": -80.6480},
                            "rating": 4.7
                        },
                        {
                            "place": "Baikonur Cosmodrome",
                            "country": "Kazakhstan",
                            "description": "World's first and largest operational space launch facility, launching point for all crewed Soyuz missions.",
                            "best_time_to_visit": "April to October",
                            "coordinates": {"lat": 45.6, "lng": 63.3},
                            "rating": 4.5
                        }
                    ]
                }
            ],
            
            ThemeType.ENTERTAINMENT: [
                {
                    "input": "Generate 3 Entertainment destinations around the world",
                    "destinations": [
                        {
                            "place": "Las Vegas",
                            "country": "United States",
                            "description": "Entertainment capital featuring world-class shows, casinos, dining, and nightlife in the Nevada desert.",
                            "best_time_to_visit": "March to May, October to November",
                            "coordinates": {"lat": 36.1699, "lng": -115.1398},
                            "rating": 4.2
                        },
                        {
                            "place": "Tokyo",
                            "country": "Japan",
                            "description": "Vibrant metropolis blending traditional culture with cutting-edge entertainment, gaming arcades, and pop culture.",
                            "best_time_to_visit": "March to May, October to November",
                            "coordinates": {"lat": 35.6762, "lng": 139.6503},
                            "rating": 4.6
                        },
                        {
                            "place": "Rio de Janeiro",
                            "country": "Brazil",
                            "description": "Carnival capital with vibrant nightlife, samba culture, beautiful beaches, and world-famous entertainment.",
                            "best_time_to_visit": "December to March",
                            "coordinates": {"lat": -22.9068, "lng": -43.1729},
                            "rating": 4.4
                        }
                    ]
                },
                {
                    "input": "Generate 2 Entertainment destinations for nightlife",
                    "destinations": [
                        {
                            "place": "Ibiza",
                            "country": "Spain",
                            "description": "World-famous party island with legendary nightclubs, beautiful beaches, and vibrant electronic music scene.",
                            "best_time_to_visit": "May to October",
                            "coordinates": {"lat": 38.9067, "lng": 1.4206},
                            "rating": 4.4
                        },
                        {
                            "place": "Berlin",
                            "country": "Germany",
                            "description": "Underground culture capital with world-renowned techno clubs, alternative entertainment, and vibrant nightlife.",
                            "best_time_to_visit": "May to September",
                            "coordinates": {"lat": 52.5200, "lng": 13.4050},
                            "rating": 4.3
                        }
                    ]
                }
            ]
        }
        
        # Generate training examples in OpenAI fine-tuning format
        for theme, examples in training_data.items():
            for example in examples:
                # System message defining the model's role
                system_message = f"""You are a specialized travel expert focusing on {theme.value.lower()} destinations. 
Provide detailed, accurate information about destinations that excel in {theme.value.lower()} experiences. 
Include specific location details, practical travel information, and authentic insights. 
Always return responses in valid JSON format with comprehensive destination details."""

                # User message with the request
                user_message = example["input"]
                
                # Assistant response with the structured destination data
                assistant_response = json.dumps({
                    "destinations": example["destinations"]
                }, indent=2)
                
                training_example = {
                    "messages": [
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message},
                        {"role": "assistant", "content": assistant_response}
                    ]
                }
                
                training_examples.append(training_example)
        
        # Save training data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        training_file = self.training_data_dir / f"travel_destinations_training_{timestamp}.jsonl"
        
        with open(training_file, 'w') as f:
            for example in training_examples:
                f.write(json.dumps(example) + '\n')
        
        self.logger.info(
            "Training data generated",
            file_path=str(training_file),
            num_examples=len(training_examples),
            themes_covered=list(training_data.keys())
        )
        
        return str(training_file)
    
    def prepare_training_file(self, training_file_path: str) -> str:
        """Upload training file to OpenAI and return file ID."""
        
        self.logger.info("Uploading training file to OpenAI", file_path=training_file_path)
        
        try:
            with open(training_file_path, 'rb') as f:
                response = self.client.files.create(
                    file=f,
                    purpose='fine-tune'
                )
            
            file_id = response.id
            self.logger.info(
                "Training file uploaded successfully",
                file_id=file_id,
                file_path=training_file_path
            )
            
            return file_id
            
        except Exception as e:
            self.logger.error(
                "Failed to upload training file",
                file_path=training_file_path,
                error=str(e)
            )
            raise
    
    def create_fine_tuned_model(
        self, 
        training_file_id: str, 
        model: str = "gpt-3.5-turbo",
        suffix: Optional[str] = None
    ) -> str:
        """Create a fine-tuned model and return the job ID."""
        
        if not suffix:
            suffix = f"travel-destinations-{datetime.now().strftime('%Y%m%d')}"
        
        self.logger.info(
            "Creating fine-tuned model",
            base_model=model,
            training_file_id=training_file_id,
            suffix=suffix
        )
        
        try:
            # Check if the file is ready for training
            file_info = self.client.files.retrieve(training_file_id)
            self.logger.info(
                "Training file status",
                file_id=training_file_id,
                status=file_info.status,
                purpose=file_info.purpose,
                bytes=file_info.bytes
            )
            
            if file_info.status != "processed":
                self.logger.warning(
                    "Training file not ready",
                    file_id=training_file_id,
                    status=file_info.status
                )
                # Wait a bit for file processing
                time.sleep(10)
            
            # Create fine-tuning job with appropriate hyperparameters
            job_params = {
                "training_file": training_file_id,
                "model": model,
                "suffix": suffix
            }
            
            # Only add hyperparameters for supported models
            if model in ["gpt-3.5-turbo", "gpt-4"]:
                job_params["hyperparameters"] = {
                    "n_epochs": 3,  # Conservative number for small dataset
                }
            
            response = self.client.fine_tuning.jobs.create(**job_params)
            
            job_id = response.id
            self.logger.info(
                "Fine-tuning job created successfully",
                job_id=job_id,
                status=response.status,
                model=response.model,
                training_file=response.training_file
            )
            
            return job_id
            
        except Exception as e:
            self.logger.error(
                "Failed to create fine-tuning job",
                training_file_id=training_file_id,
                model=model,
                error=str(e),
                error_type=type(e).__name__
            )
            
            # Try to get more detailed error information
            if hasattr(e, 'response'):
                try:
                    error_detail = e.response.json() if hasattr(e.response, 'json') else str(e.response.content)
                    self.logger.error("OpenAI API error details", error_detail=error_detail)
                except:
                    pass
            
            raise
    
    def monitor_fine_tuning_job(self, job_id: str, max_wait_time: int = 3600) -> Dict[str, Any]:
        """Monitor fine-tuning job progress with improved error handling."""
        
        self.logger.info("Starting fine-tuning job monitoring", job_id=job_id, max_wait_time=max_wait_time)
        
        start_time = time.time()
        last_status = None
        
        while True:
            try:
                # Check if we've exceeded maximum wait time
                elapsed_time = time.time() - start_time
                if elapsed_time > max_wait_time:
                    self.logger.error(
                        "Fine-tuning job monitoring timeout",
                        job_id=job_id,
                        elapsed_time=elapsed_time,
                        max_wait_time=max_wait_time
                    )
                    return {
                        "status": "timeout",
                        "error": f"Monitoring timeout after {max_wait_time} seconds"
                    }
                
                job = self.client.fine_tuning.jobs.retrieve(job_id)
                status = job.status
                
                # Log status changes
                if status != last_status:
                    self.logger.info(
                        "Fine-tuning job status change",
                        job_id=job_id,
                        status=status,
                        elapsed_time=elapsed_time,
                        model=getattr(job, 'model', 'unknown'),
                        fine_tuned_model=getattr(job, 'fine_tuned_model', None)
                    )
                    last_status = status
                
                if status == "succeeded":
                    model_id = job.fine_tuned_model
                    self.logger.info(
                        "Fine-tuning completed successfully",
                        job_id=job_id,
                        model_id=model_id,
                        elapsed_time=elapsed_time
                    )
                    
                    # Save model information
                    self._save_model_info(job_id, model_id, job)
                    
                    return {
                        "status": "completed",
                        "model_id": model_id,
                        "job_details": job,
                        "elapsed_time": elapsed_time
                    }
                
                elif status == "failed":
                    error_info = getattr(job, 'error', 'Unknown error')
                    self.logger.error(
                        "Fine-tuning job failed",
                        job_id=job_id,
                        error=error_info,
                        elapsed_time=elapsed_time
                    )
                    
                    return {
                        "status": "failed",
                        "error": error_info,
                        "job_details": job,
                        "elapsed_time": elapsed_time
                    }
                
                elif status == "cancelled":
                    self.logger.warning(
                        "Fine-tuning job was cancelled",
                        job_id=job_id,
                        elapsed_time=elapsed_time
                    )
                    
                    return {
                        "status": "cancelled",
                        "job_details": job,
                        "elapsed_time": elapsed_time
                    }
                
                elif status in ["validating_files", "queued", "running"]:
                    # Job is in progress
                    progress_info = {
                        "status": status,
                        "elapsed_time": elapsed_time
                    }
                    
                    # Add training progress if available
                    if hasattr(job, 'trained_tokens') and job.trained_tokens:
                        progress_info["trained_tokens"] = job.trained_tokens
                    
                    self.logger.debug(
                        "Fine-tuning job in progress",
                        job_id=job_id,
                        **progress_info
                    )
                    
                    # Wait before next check (shorter intervals for active jobs)
                    wait_time = 30 if status == "running" else 60
                    time.sleep(wait_time)
                
                else:
                    self.logger.warning(
                        "Unknown fine-tuning status",
                        job_id=job_id,
                        status=status,
                        elapsed_time=elapsed_time
                    )
                    time.sleep(30)
                    
            except Exception as e:
                self.logger.error(
                    "Error monitoring fine-tuning job",
                    job_id=job_id,
                    error=str(e),
                    error_type=type(e).__name__,
                    elapsed_time=time.time() - start_time
                )
                
                # Don't fail immediately on API errors, retry after a delay
                time.sleep(60)
                
                # But fail if we've been retrying for too long
                if time.time() - start_time > max_wait_time:
                    return {
                        "status": "monitoring_failed",
                        "error": f"Monitoring failed: {str(e)}"
                    }
    
    def _save_model_info(self, job_id: str, model_id: str, job_details: Any):
        """Save fine-tuned model information."""
        
        # Safely extract hyperparameters and usage information
        hyperparameters = {}
        if hasattr(job_details, 'hyperparameters') and job_details.hyperparameters:
            hp = job_details.hyperparameters
            hyperparameters = {
                "n_epochs": getattr(hp, 'n_epochs', None),
                "batch_size": getattr(hp, 'batch_size', None),
                "learning_rate_multiplier": getattr(hp, 'learning_rate_multiplier', None)
            }
        
        usage = {}
        if hasattr(job_details, 'usage') and job_details.usage:
            usage_obj = job_details.usage
            usage = {
                "training_tokens": getattr(usage_obj, 'training_tokens', None),
                "validation_tokens": getattr(usage_obj, 'validation_tokens', None),
                "total_tokens": getattr(usage_obj, 'total_tokens', None)
            }
        
        model_info = {
            "model_id": model_id,
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "base_model": getattr(job_details, 'model', None),
            "status": getattr(job_details, 'status', None),
            "training_file": getattr(job_details, 'training_file', None),
            "hyperparameters": hyperparameters,
            "usage": usage
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.model_artifacts_dir / f"model_info_{timestamp}.json"
        
        try:
            with open(model_file, 'w') as f:
                json.dump(model_info, f, indent=2)
            
            self.logger.info(
                "Model information saved",
                model_id=model_id,
                info_file=str(model_file)
            )
        except Exception as e:
            self.logger.error(
                "Failed to save model information",
                model_id=model_id,
                error=str(e)
            )
    
    def list_fine_tuned_models(self) -> List[Dict[str, Any]]:
        """List all available fine-tuned models."""
        
        try:
            models = self.client.models.list()
            fine_tuned_models = [
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": model.owned_by
                }
                for model in models.data 
                if model.id.startswith("ft:")
            ]
            
            self.logger.info(
                "Retrieved fine-tuned models",
                count=len(fine_tuned_models)
            )
            
            return fine_tuned_models
            
        except Exception as e:
            self.logger.error(
                "Failed to list fine-tuned models",
                error=str(e)
            )
            return []
    
    def full_fine_tuning_pipeline(
        self, 
        base_model: str = "gpt-3.5-turbo"
    ) -> Optional[str]:
        """Execute the complete fine-tuning pipeline."""
        
        self.logger.info(
            "Starting full fine-tuning pipeline",
            base_model=base_model
        )
        
        try:
            # Step 1: Generate training data
            training_file_path = self.generate_training_data()
            
            # Step 2: Upload training file
            training_file_id = self.prepare_training_file(training_file_path)
            
            # Step 3: Create fine-tuning job
            job_id = self.create_fine_tuned_model(training_file_id, base_model)
            
            # Step 4: Monitor job completion
            result = self.monitor_fine_tuning_job(job_id)
            
            if result["status"] == "completed":
                model_id = result["model_id"]
                
                self.logger.info(
                    "Fine-tuning pipeline completed successfully",
                    model_id=model_id
                )
                
                return model_id
            else:
                self.logger.error(
                    "Fine-tuning pipeline failed",
                    result=result
                )
                return None
                
        except Exception as e:
            self.logger.error(
                "Fine-tuning pipeline failed",
                error=str(e),
                exc_info=True
            )
            return None 