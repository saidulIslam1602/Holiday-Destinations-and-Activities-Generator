import time
from langchain.chains import LLMChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from requests.exceptions import HTTPError
import key_

llm = OpenAI(temperature=0.6)

def safe_request(request_function, *args, **kwargs):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            return request_function(*args, **kwargs)
        except HTTPError as e:
            if e.response.status_code == 429:  # Rate limit exceeded
                print(f"Rate limit exceeded. Retrying in 20 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(20)
            else:
                raise e
        except Exception as e:
            raise e


def destination_and_activity_generator(holiday):
    # Chain 1: Destination Theme
    prompt_template_name = PromptTemplate(
        input_variables=["holiday"],
        template=(
            "I want to travel to {holiday} destinations around the world. "
            "Suggest a few destinations in the format 'Place, Country', separated by commas."
        )
    )
    theme_chain = LLMChain(llm=llm, prompt=prompt_template_name, output_key="destinations")

    # Chain 2: Activity Chain
    prompt_template_items = PromptTemplate(
        input_variables=['destination'],
        template=(
            "For the destination {destination}, suggest what to do there. "
            "Return the activities as a comma-separated string."
        )
    )
    activity_chain = LLMChain(llm=llm, prompt=prompt_template_items, output_key="activities")

    # Generate destinations
    response = safe_request(theme_chain, {'holiday': holiday})
    destinations = response['destinations'].strip().split(",")

    # Generate activities for each destination
    results = []
    for destination in destinations:
        destination = destination.strip()
        if destination:
            try:
                # Attempt to split the destination into place and country
                if ',' in destination:
                    place, country = [part.strip() for part in destination.split(',', 1)]
                else:
                    # If there is no comma, default the whole string as place and country as unknown
                    place = destination
                    country = "Unknown"

            except ValueError:
                place = destination
                country = "Unknown"

            activities_response = safe_request(activity_chain, {'destination': destination})
            activities = activities_response['activities'].strip().split(",")

            results.append({
                'destination': f"{place}, {country}",
                'activities': [activity.strip() for activity in activities if activity.strip()]
            })

    return results
