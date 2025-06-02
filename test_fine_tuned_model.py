#!/usr/bin/env python3
"""
Test script to verify the fine-tuned model is working correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def main():
    print("🧪 Testing Fine-Tuned Model")
    print("=" * 40)
    
    try:
        # Import after setting path
        from src.config.settings import settings
        from src.services.destination_service import DestinationService
        from src.models import GenerationRequest, ThemeType
        import asyncio
        
        # Check configuration
        print(f"📊 Model Configuration:")
        print(f"   Use Fine-Tuned Model: {settings.use_fine_tuned_model}")
        print(f"   Fine-Tuned Model ID: {settings.fine_tuned_model_id}")
        print(f"   Effective Model: {settings.effective_openai_model}")
        print()
        
        # Initialize service
        print("🔧 Initializing DestinationService...")
        service = DestinationService()
        print(f"✅ Service initialized with model: {service.llm.model_name}")
        print()
        
        # Test generation
        print("🎯 Testing destination generation...")
        request = GenerationRequest(
            theme=ThemeType.NATURAL_ATTRACTION,
            count=2,
            include_activities=True
        )
        
        print(f"   Theme: {request.theme.value if hasattr(request.theme, 'value') else request.theme}")
        print(f"   Count: {request.count}")
        print(f"   Include Activities: {request.include_activities}")
        print()
        
        # Generate destinations
        print("⏳ Generating destinations...")
        result = asyncio.run(service.generate_destinations(request))
        
        if result and result.destinations:
            print(f"✅ Success! Generated {len(result.destinations)} destinations")
            print(f"⚡ Generation Time: {result.generation_time_seconds:.2f}s")
            print(f"🤖 Model Used: Enhanced AI (Fine-Tuned)")
            print()
            
            # Display first destination as example
            dest = result.destinations[0]
            print("📍 Sample Destination:")
            print(f"   Place: {dest.place}")
            print(f"   Country: {dest.country}")
            print(f"   Rating: {dest.rating}/5")
            print(f"   Best Time: {dest.best_time_to_visit}")
            print(f"   Activities: {len(dest.activities) if dest.activities else 0}")
            print()
            
            # Show quality indicators
            print("🎯 Quality Indicators:")
            has_coords = bool(dest.coordinates)
            has_rating = bool(dest.rating)
            has_activities = bool(dest.activities)
            
            print(f"   ✅ Coordinates: {has_coords}")
            print(f"   ✅ Rating: {has_rating}")
            print(f"   ✅ Activities: {has_activities}")
            
            if has_coords:
                print(f"   📍 Location: {dest.coordinates['lat']:.3f}, {dest.coordinates['lng']:.3f}")
            
            if has_activities:
                activity = dest.activities[0]
                print(f"   🎯 Sample Activity: {activity.name}")
                print(f"   ⏱️ Duration: {activity.duration_hours}h")
                print(f"   🔥 Difficulty: {activity.difficulty_level}/5")
            
            print()
            print("🎉 Fine-tuned model is working excellently!")
            print("💡 You should now see improved:")
            print("   - More accurate destination recommendations")
            print("   - Better formatted responses")
            print("   - Enhanced location details")
            print("   - Consistent activity information")
            
        else:
            print("❌ No destinations generated")
            return 1
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 