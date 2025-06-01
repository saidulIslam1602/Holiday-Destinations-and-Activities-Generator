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
            ThemeType.SPORTS: {
                "examples": [
                    {
                        "input": "Generate 3 Sports destinations around the world",
                        "destinations": [
                            {
                                "place": "Queenstown",
                                "country": "New Zealand", 
                                "description": "Adventure sports capital with bungee jumping, skydiving, and extreme sports in stunning alpine scenery.",
                                "best_time_to_visit": "October to April",
                                "coordinates": {"lat": -45.0312, "lng": 168.6626},
                                "rating": 4.8,
                                "activities": [
                                    {
                                        "name": "Bungee Jumping from Kawarau Gorge",
                                        "description": "Experience the world's first commercial bungee jump site with a 43-meter drop over the historic Kawarau River.",
                                        "activity_type": "Adventure",
                                        "duration_hours": 2.0,
                                        "difficulty_level": 4,
                                        "cost_estimate": "High ($200-300)"
                                    },
                                    {
                                        "name": "Jet Boating on Lake Wakatipu",
                                        "description": "High-speed boat ride through narrow canyon walls with famous 360-degree spins.",
                                        "activity_type": "Adventure",
                                        "duration_hours": 1.5,
                                        "difficulty_level": 2,
                                        "cost_estimate": "Moderate ($100-150)"
                                    }
                                ]
                            },
                            {
                                "place": "Chamonix",
                                "country": "France",
                                "description": "World-renowned ski resort and mountaineering hub in the French Alps, home to extreme skiing and climbing.",
                                "best_time_to_visit": "December to April (skiing), June to September (climbing)",
                                "coordinates": {"lat": 45.9237, "lng": 6.8694},
                                "rating": 4.7,
                                "activities": [
                                    {
                                        "name": "Off-piste skiing on Vallée Blanche",
                                        "description": "Legendary off-piste ski route with breathtaking glacier views and challenging terrain.",
                                        "activity_type": "Adventure",
                                        "duration_hours": 6.0,
                                        "difficulty_level": 5,
                                        "cost_estimate": "High ($300-400)"
                                    }
                                ]
                            }
                        ]
                    }
                ],
                "keywords": ["adventure sports", "skiing", "mountaineering", "extreme sports", "athletics", "outdoor activities"]
            },
            
            ThemeType.HISTORICAL_PLACE: {
                "examples": [
                    {
                        "input": "Generate 3 Historical Place destinations around the world",
                        "destinations": [
                            {
                                "place": "Angkor Wat",
                                "country": "Cambodia",
                                "description": "Magnificent 12th-century temple complex and UNESCO World Heritage site, representing the pinnacle of Khmer architecture.",
                                "best_time_to_visit": "November to March",
                                "coordinates": {"lat": 13.4125, "lng": 103.8670},
                                "rating": 4.9,
                                "activities": [
                                    {
                                        "name": "Sunrise tour of Angkor Wat",
                                        "description": "Witness the iconic temple silhouetted against the dawn sky in this magical early morning experience.",
                                        "activity_type": "Cultural",
                                        "duration_hours": 4.0,
                                        "difficulty_level": 2,
                                        "cost_estimate": "Moderate ($50-80)"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            
            ThemeType.NATURAL_ATTRACTION: {
                "examples": [
                    {
                        "input": "Generate 3 Natural Attraction destinations around the world",
                        "destinations": [
                            {
                                "place": "Torres del Paine",
                                "country": "Chile",
                                "description": "Spectacular national park in Patagonia featuring dramatic granite towers, glacial lakes, and diverse wildlife.",
                                "best_time_to_visit": "October to April",
                                "coordinates": {"lat": -51.0, "lng": -73.0},
                                "rating": 4.8,
                                "activities": [
                                    {
                                        "name": "W Trek",
                                        "description": "Multi-day hiking circuit showcasing the park's most iconic viewpoints and natural features.",
                                        "activity_type": "Outdoor",
                                        "duration_hours": 120.0,
                                        "difficulty_level": 4,
                                        "cost_estimate": "High ($500-800)"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            
            ThemeType.SCIENTIFIC: {
                "examples": [
                    {
                        "input": "Generate 3 Scientific destinations around the world",
                        "destinations": [
                            {
                                "place": "Atacama Desert",
                                "country": "Chile",
                                "description": "World's driest non-polar desert, ideal for astronomical observations with numerous world-class observatories.",
                                "best_time_to_visit": "March to May, September to November",
                                "coordinates": {"lat": -24.5, "lng": -69.25},
                                "rating": 4.6,
                                "activities": [
                                    {
                                        "name": "ALMA Observatory tour",
                                        "description": "Visit the world's largest radio telescope array and learn about cutting-edge astronomical research.",
                                        "activity_type": "Educational",
                                        "duration_hours": 8.0,
                                        "difficulty_level": 2,
                                        "cost_estimate": "Free (advance booking required)"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            
            ThemeType.ENTERTAINMENT: {
                "examples": [
                    {
                        "input": "Generate 3 Entertainment destinations around the world",
                        "destinations": [
                            {
                                "place": "Las Vegas",
                                "country": "United States",
                                "description": "Entertainment capital featuring world-class shows, casinos, dining, and nightlife in the Nevada desert.",
                                "best_time_to_visit": "March to May, October to November",
                                "coordinates": {"lat": 36.1699, "lng": -115.1398},
                                "rating": 4.2,
                                "activities": [
                                    {
                                        "name": "Cirque du Soleil show",
                                        "description": "Experience world-renowned acrobatic performances combining artistry, music, and theatrical spectacle.",
                                        "activity_type": "Entertainment",
                                        "duration_hours": 2.5,
                                        "difficulty_level": 1,
                                        "cost_estimate": "High ($100-300)"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        # Generate training examples in OpenAI fine-tuning format
        for theme, data in training_data.items():
            for example in data["examples"]:
                # System message defining the model's role
                system_message = f"""You are a specialized travel expert focusing on {theme.value.lower()} destinations. 
Provide detailed, accurate information about destinations that excel in {theme.value.lower()} experiences. 
Include specific activities, practical information, and authentic local insights. 
Always return responses in valid JSON format with comprehensive destination and activity details."""

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
            response = self.client.fine_tuning.jobs.create(
                training_file=training_file_id,
                model=model,
                suffix=suffix,
                hyperparameters={
                    "n_epochs": 3,  # Adjust based on your data size
                }
            )
            
            job_id = response.id
            self.logger.info(
                "Fine-tuning job created",
                job_id=job_id,
                status=response.status
            )
            
            return job_id
            
        except Exception as e:
            self.logger.error(
                "Failed to create fine-tuning job",
                training_file_id=training_file_id,
                error=str(e)
            )
            raise
    
    def monitor_fine_tuning_job(self, job_id: str) -> Dict[str, Any]:
        """Monitor fine-tuning job progress."""
        
        self.logger.info("Monitoring fine-tuning job", job_id=job_id)
        
        while True:
            try:
                job = self.client.fine_tuning.jobs.retrieve(job_id)
                status = job.status
                
                self.logger.info(
                    "Fine-tuning job status",
                    job_id=job_id,
                    status=status
                )
                
                if status == "succeeded":
                    model_id = job.fine_tuned_model
                    self.logger.info(
                        "Fine-tuning completed successfully",
                        job_id=job_id,
                        model_id=model_id
                    )
                    
                    # Save model information
                    self._save_model_info(job_id, model_id, job)
                    
                    return {
                        "status": "completed",
                        "model_id": model_id,
                        "job_details": job
                    }
                
                elif status == "failed":
                    self.logger.error(
                        "Fine-tuning job failed",
                        job_id=job_id,
                        error=getattr(job, 'error', 'Unknown error')
                    )
                    
                    return {
                        "status": "failed",
                        "error": getattr(job, 'error', 'Unknown error')
                    }
                
                elif status in ["validating_files", "queued", "running"]:
                    self.logger.info(
                        "Fine-tuning job in progress",
                        job_id=job_id,
                        status=status
                    )
                    time.sleep(60)  # Check every minute
                
                else:
                    self.logger.warning(
                        "Unknown fine-tuning status",
                        job_id=job_id,
                        status=status
                    )
                    time.sleep(30)
                    
            except Exception as e:
                self.logger.error(
                    "Error monitoring fine-tuning job",
                    job_id=job_id,
                    error=str(e)
                )
                time.sleep(60)
    
    def _save_model_info(self, job_id: str, model_id: str, job_details: Any):
        """Save fine-tuned model information."""
        
        model_info = {
            "model_id": model_id,
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "base_model": job_details.model,
            "status": job_details.status,
            "training_file": job_details.training_file,
            "hyperparameters": getattr(job_details, 'hyperparameters', {}),
            "usage": getattr(job_details, 'usage', {})
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_file = self.model_artifacts_dir / f"model_info_{timestamp}.json"
        
        with open(model_file, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        self.logger.info(
            "Model information saved",
            model_id=model_id,
            info_file=str(model_file)
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