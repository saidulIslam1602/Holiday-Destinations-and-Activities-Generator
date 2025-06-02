"""
Enterprise destination generation service.
Handles business logic for generating holiday destinations and activities.
"""

import asyncio
import time
from typing import List, Optional, Dict, Any
from datetime import datetime

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
try:
    from langchain_community.chat_models import ChatOpenAI
except ImportError:
    from langchain.llms import OpenAI as ChatOpenAI
import httpx

from src.config import settings
from src.core import LoggerMixin, cached
from src.core.fine_tuning import FineTuningManager
from src.models import (
    Activity,
    ActivityType,
    Destination,
    GenerationRequest,
    GenerationResponse,
    ThemeType
)


class DestinationGenerationError(Exception):
    """Custom exception for destination generation errors."""
    pass


class DestinationService(LoggerMixin):
    """Service for generating holiday destinations and activities."""
    
    def __init__(self):
        # Use fine-tuned model if available, otherwise use base model
        model_name = settings.effective_openai_model
        
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model=model_name,
            temperature=settings.openai_temperature,
            request_timeout=settings.api_timeout,
            max_retries=settings.max_retries,
        )
        
        self.fine_tuning_manager = FineTuningManager()
        self._setup_chains()
        
        self.logger.info(
            "DestinationService initialized",
            model=model_name,
            fine_tuned=settings.use_fine_tuned_model,
            temperature=settings.openai_temperature
        )
    
    def _setup_chains(self) -> None:
        """Setup LangChain chains for destination and activity generation."""
        
        # Enhanced destination prompt for fine-tuned models
        if settings.use_fine_tuned_model:
            # Specialized prompts for fine-tuned models
            self.destination_prompt = PromptTemplate(
                input_variables=["theme", "count"],
                template="""Generate {count} unique {theme} travel destinations around the world.

For each destination, provide comprehensive details including:
- Specific location (Place, Country)
- Detailed description highlighting {theme} features
- Best time to visit with seasonal considerations
- Accurate GPS coordinates
- Rating out of 5 stars based on {theme} excellence
- Rich contextual information about why it's ideal for {theme}

Ensure destinations are:
- Globally diverse and culturally varied
- Specifically chosen for exceptional {theme} experiences
- Real, accessible locations with verified information
- Ranked by their {theme} reputation and offerings

Return the response in valid JSON format with the structure:
{{
    "destinations": [
        {{
            "place": "Location Name",
            "country": "Country Name",
            "description": "Detailed description emphasizing {theme} aspects",
            "best_time_to_visit": "Optimal seasons/months",
            "coordinates": {{"lat": latitude, "lng": longitude}},
            "rating": rating_float
        }}
    ]
}}"""
            )
        else:
            # Standard prompts for base models
            self.destination_prompt = PromptTemplate(
                input_variables=["theme", "count"],
                template="""You are a specialized travel expert. Generate {count} unique {theme} travel destinations around the world.

For each destination, provide:
1. Place name and country in format "Place, Country"
2. Brief description (1-2 sentences)
3. Best time to visit
4. Approximate coordinates (latitude, longitude)
5. Rating out of 5 stars

Return the response in the following JSON format:
{{
    "destinations": [
        {{
            "place": "Place Name",
            "country": "Country Name",
            "description": "Brief description",
            "best_time_to_visit": "Best time period",
            "coordinates": {{"lat": latitude, "lng": longitude}},
            "rating": rating_float
        }}
    ]
}}

Ensure all destinations are real, diverse, and well-suited for {theme} activities."""
            )
        
        self.destination_chain = LLMChain(
            llm=self.llm,
            prompt=self.destination_prompt,
            output_key="destinations"
        )
        
        # Enhanced activity prompt
        if settings.use_fine_tuned_model:
            self.activity_prompt = PromptTemplate(
                input_variables=["destination", "theme"],
                template="""For the {theme} destination "{destination}", provide comprehensive activity recommendations.

Generate 5-7 specific activities that showcase the best {theme} experiences available at this location.

For each activity, include:
- Specific activity name and location details
- Rich description explaining the experience
- Activity category (Outdoor/Indoor/Cultural/Adventure/Relaxation/Educational)
- Realistic duration in hours
- Difficulty level (1-5 scale with 1=easy, 5=expert)
- Cost estimate with price range
- Best time of day/season if relevant
- Any special requirements or considerations

Focus on:
- Authentic, location-specific {theme} experiences
- Activities that locals and experts recommend
- Varied difficulty levels and time commitments
- Practical information for planning

Return response in JSON format:
{{
    "activities": [
        {{
            "name": "Specific Activity Name",
            "description": "Detailed description of the experience",
            "activity_type": "Category",
            "duration_hours": duration_float,
            "difficulty_level": difficulty_int,
            "cost_estimate": "Detailed cost information"
        }}
    ]
}}

IMPORTANT: Ensure the JSON is valid and complete. Do not truncate the response."""
            )
        else:
            self.activity_prompt = PromptTemplate(
                input_variables=["destination", "theme"],
                template="""For the {theme} destination "{destination}", suggest specific activities.

Provide exactly 5 activities with details:
1. Activity name
2. Brief description
3. Activity type (Outdoor/Indoor/Cultural/Adventure/Relaxation/Educational)
4. Estimated duration in hours
5. Difficulty level (1-5)
6. Approximate cost estimate

Return the response in valid JSON format:
{{
    "activities": [
        {{
            "name": "Activity Name",
            "description": "Activity description",
            "activity_type": "Activity Type",
            "duration_hours": duration_float,
            "difficulty_level": difficulty_int,
            "cost_estimate": "Cost range"
        }}
    ]
}}

IMPORTANT: Return only valid JSON. Ensure all quotes are properly escaped and the response is complete."""
            )
        
        self.activity_chain = LLMChain(
            llm=self.llm,
            prompt=self.activity_prompt,
            output_key="activities"
        )
    
    async def _safe_api_request(
        self,
        chain: LLMChain,
        inputs: Dict[str, Any],
        context: str = "API request"
    ) -> Dict[str, Any]:
        """Make a safe API request with retry logic and error handling."""
        
        for attempt in range(settings.max_retries):
            try:
                self.logger.info(
                    f"Making {context}",
                    attempt=attempt + 1,
                    max_retries=settings.max_retries,
                    inputs=inputs,
                    model=settings.effective_openai_model
                )
                
                start_time = time.time()
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: chain(inputs)
                )
                execution_time = time.time() - start_time
                
                self.logger.info(
                    f"{context} completed successfully",
                    execution_time=execution_time,
                    attempt=attempt + 1,
                    model=settings.effective_openai_model
                )
                
                return response
                
            except Exception as e:
                error_message = str(e).lower()
                
                # Check if it's a rate limit error
                if "rate limit" in error_message or "quota" in error_message:
                    wait_time = settings.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Rate limit exceeded for {context}",
                        attempt=attempt + 1,
                        wait_time=wait_time,
                        error=str(e)
                    )
                    
                    if attempt < settings.max_retries - 1:
                        await asyncio.sleep(wait_time)
                    else:
                        raise DestinationGenerationError(
                            f"Rate limit exceeded after {settings.max_retries} attempts"
                        )
                
                # Check if it's an API error
                elif "api" in error_message or "authentication" in error_message:
                    self.logger.error(
                        f"API error during {context}",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    
                    if attempt < settings.max_retries - 1:
                        await asyncio.sleep(settings.retry_delay)
                    else:
                        raise DestinationGenerationError(f"API error: {str(e)}")
                
                # Generic error handling
                else:
                    self.logger.error(
                        f"Unexpected error during {context}",
                        attempt=attempt + 1,
                        error=str(e),
                        exc_info=True
                    )
                    
                    if attempt < settings.max_retries - 1:
                        await asyncio.sleep(settings.retry_delay)
                    else:
                        raise DestinationGenerationError(f"Unexpected error: {str(e)}")
        
        raise DestinationGenerationError(f"Failed {context} after all retries")
    
    def _parse_json_response(self, response: str, context: str) -> Dict[str, Any]:
        """Parse JSON response with error handling."""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse JSON response for {context}",
                response=response[:200],
                error=str(e)
            )
            # Fallback to basic parsing
            return self._fallback_parse(response, context)
    
    def _fallback_parse(self, response: str, context: str) -> Dict[str, Any]:
        """Fallback parsing when JSON parsing fails."""
        self.logger.warning(f"Using fallback parsing for {context}")
        
        if "destination" in context.lower():
            # Simple destination parsing
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            destinations = []
            
            for line in lines[:5]:  # Limit to 5 destinations
                if ',' in line and not line.startswith('{') and not line.startswith('"'):
                    parts = line.split(',', 1)
                    destinations.append({
                        "place": parts[0].strip(),
                        "country": parts[1].strip(),
                        "description": "Generated destination",
                        "best_time_to_visit": "Year-round",
                        "coordinates": {"lat": 0.0, "lng": 0.0},
                        "rating": 4.0
                    })
            
            return {"destinations": destinations}
        
        else:
            # Improved activity parsing - avoid JSON fragments
            lines = [line.strip().lstrip('- ') for line in response.split('\n') if line.strip()]
            activities = []
            
            # Filter out JSON syntax and extract meaningful activity names
            for line in lines[:20]:  # Look at more lines to find actual activities
                # Skip JSON syntax lines
                if any(skip in line for skip in ['{', '}', '"activities":', '"name":', '"description":', '"activity_type":', 
                                               '"duration_hours":', '"difficulty_level":', '"cost_estimate":', '[', ']']):
                    continue
                
                # Extract activity names from quoted strings
                if '"' in line and ':' not in line:
                    # This might be a quoted activity name
                    activity_name = line.strip('"').strip(',').strip()
                    if activity_name and len(activity_name) > 2:
                        activities.append({
                            "name": activity_name,
                            "description": f"Enjoy {activity_name.lower()} at this destination",
                            "activity_type": "Outdoor",
                            "duration_hours": 2.0,
                            "difficulty_level": 3,
                            "cost_estimate": "Moderate"
                        })
                elif line and len(line) > 3 and not line.startswith('"') and ':' not in line:
                    # Plain text activity
                    activities.append({
                        "name": line,
                        "description": f"Enjoy {line.lower()} at this destination",
                        "activity_type": "Outdoor",
                        "duration_hours": 2.0,
                        "difficulty_level": 3,
                        "cost_estimate": "Moderate"
                    })
                
                if len(activities) >= 5:  # Limit to 5 activities
                    break
            
            # If no activities found, create some default ones
            if not activities:
                activities = [
                    {
                        "name": "Explore the area",
                        "description": "Take time to explore this amazing destination",
                        "activity_type": "Outdoor",
                        "duration_hours": 3.0,
                        "difficulty_level": 2,
                        "cost_estimate": "Low"
                    },
                    {
                        "name": "Local sightseeing",
                        "description": "Discover the local attractions and landmarks",
                        "activity_type": "Cultural",
                        "duration_hours": 4.0,
                        "difficulty_level": 1,
                        "cost_estimate": "Moderate"
                    }
                ]
            
            return {"activities": activities}
    
    @cached(prefix="destinations", ttl=3600)
    async def generate_destinations(
        self,
        request: GenerationRequest
    ) -> GenerationResponse:
        """Generate destinations based on theme with comprehensive error handling."""
        
        start_time = time.time()
        
        # Safe theme handling - works with both string and enum
        theme_str = request.theme.value if hasattr(request.theme, 'value') else str(request.theme)
        cache_key = f"{theme_str}_{request.count}_{request.include_activities}"
        
        self.logger.info(
            "Starting destination generation",
            theme=request.theme,
            count=request.count,
            include_activities=request.include_activities,
            model=settings.effective_openai_model,
            cache_key=cache_key
        )
        
        try:
            # Generate destinations
            destination_inputs = {
                "theme": theme_str,
                "count": request.count
            }
            
            destination_response = await self._safe_api_request(
                self.destination_chain,
                destination_inputs,
                "destination generation"
            )
            
            destination_data = self._parse_json_response(
                destination_response["destinations"],
                "destination generation"
            )
            
            destinations = []
            
            # Process each destination
            for dest_info in destination_data.get("destinations", []):
                try:
                    destination = Destination(
                        place=dest_info.get("place", "Unknown Place"),
                        country=dest_info.get("country", "Unknown Country"),
                        description=dest_info.get("description"),
                        best_time_to_visit=dest_info.get("best_time_to_visit"),
                        coordinates=dest_info.get("coordinates"),
                        rating=dest_info.get("rating"),
                        theme=request.theme,
                        activities=[]
                    )
                    
                    # Generate activities for this destination if requested
                    if request.include_activities:
                        activities = await self._generate_activities_for_destination(
                            destination,
                            request.theme
                        )
                        destination.activities = activities
                    
                    destinations.append(destination)
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to process destination",
                        destination_info=dest_info,
                        error=str(e)
                    )
                    continue
            
            generation_time = time.time() - start_time
            
            response = GenerationResponse(
                destinations=destinations,
                theme=request.theme,
                generation_time_seconds=generation_time
            )
            
            self.logger.info(
                "Destination generation completed successfully",
                theme=request.theme,
                destinations_count=len(destinations),
                generation_time=generation_time,
                model=settings.effective_openai_model
            )
            
            return response
            
        except Exception as e:
            self.logger.error(
                "Destination generation failed",
                theme=request.theme,
                error=str(e),
                exc_info=True
            )
            raise DestinationGenerationError(f"Failed to generate destinations: {str(e)}")
    
    async def _generate_activities_for_destination(
        self,
        destination: Destination,
        theme: ThemeType
    ) -> List[Activity]:
        """Generate activities for a specific destination."""
        
        try:
            # Safe theme handling - works with both string and enum
            theme_str = theme.value if hasattr(theme, 'value') else str(theme)
            
            activity_inputs = {
                "destination": destination.full_name,
                "theme": theme_str
            }
            
            activity_response = await self._safe_api_request(
                self.activity_chain,
                activity_inputs,
                f"activity generation for {destination.full_name}"
            )
            
            activity_data = self._parse_json_response(
                activity_response["activities"],
                "activity generation"
            )
            
            activities = []
            
            for act_info in activity_data.get("activities", []):
                try:
                    # Handle activity type parsing with fallback for combined types
                    activity_type_str = act_info.get("activity_type", "Outdoor")
                    
                    # Map combined activity types to valid enum values
                    activity_type_mapping = {
                        "Cultural/Educational": "Cultural",
                        "Educational/Cultural": "Educational", 
                        "Outdoor/Adventure": "Outdoor",
                        "Adventure/Outdoor": "Adventure",
                        "Indoor/Cultural": "Indoor",
                        "Cultural/Indoor": "Cultural",
                        "Relaxation/Indoor": "Relaxation",
                        "Indoor/Relaxation": "Indoor"
                    }
                    
                    # Use mapping if available, otherwise try the original value
                    if activity_type_str in activity_type_mapping:
                        activity_type_str = activity_type_mapping[activity_type_str]
                    
                    # Try to create ActivityType, with fallback to "Outdoor"
                    try:
                        activity_type = ActivityType(activity_type_str)
                    except ValueError:
                        # If still invalid, try to extract the first valid part
                        for valid_type in ActivityType:
                            if valid_type.value.lower() in activity_type_str.lower():
                                activity_type = valid_type
                                break
                        else:
                            # Ultimate fallback
                            activity_type = ActivityType.OUTDOOR
                    
                    activity = Activity(
                        name=act_info.get("name", "Unknown Activity"),
                        description=act_info.get("description"),
                        activity_type=activity_type,
                        duration_hours=act_info.get("duration_hours"),
                        difficulty_level=act_info.get("difficulty_level"),
                        cost_estimate=act_info.get("cost_estimate")
                    )
                    activities.append(activity)
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to process activity",
                        activity_info=act_info,
                        destination=destination.full_name,
                        error=str(e)
                    )
                    continue
            
            return activities
            
        except Exception as e:
            self.logger.error(
                "Failed to generate activities",
                destination=destination.full_name,
                error=str(e)
            )
            return []
    
    async def initiate_fine_tuning(self, base_model: str = "gpt-3.5-turbo") -> Optional[str]:
        """Initiate the fine-tuning process for better domain-specific responses."""
        
        self.logger.info(
            "Initiating fine-tuning process",
            base_model=base_model
        )
        
        try:
            model_id = await asyncio.get_event_loop().run_in_executor(
                None,
                self.fine_tuning_manager.full_fine_tuning_pipeline,
                base_model
            )
            
            if model_id:
                self.logger.info(
                    "Fine-tuning completed successfully",
                    model_id=model_id
                )
                
                # Update configuration to use the new model
                settings.fine_tuned_model_id = model_id
                settings.use_fine_tuned_model = True
                
                # Reinitialize with new model
                self.__init__()
                
                return model_id
            else:
                self.logger.error("Fine-tuning failed")
                return None
                
        except Exception as e:
            self.logger.error(
                "Fine-tuning process failed",
                error=str(e),
                exc_info=True
            )
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the service."""
        try:
            # Test a simple API call
            test_request = GenerationRequest(
                theme=ThemeType.ENTERTAINMENT,
                count=1,
                include_activities=False
            )
            
            start_time = time.time()
            await self.generate_destinations(test_request)
            response_time = time.time() - start_time
            
            # Get model information
            model_info = {
                "current_model": settings.effective_openai_model,
                "base_model": settings.openai_model,
                "fine_tuned": settings.use_fine_tuned_model,
                "fine_tuned_model_id": settings.fine_tuned_model_id
            }
            
            return {
                "status": "healthy",
                "response_time_seconds": response_time,
                "openai_connection": "ok",
                "model_info": model_info
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "openai_connection": "failed",
                "model_info": {
                    "current_model": settings.effective_openai_model,
                    "fine_tuned": settings.use_fine_tuned_model
                }
            } 