import streamlit as st
import langchain_helper

st.title("Holiday Destinations Generator for Different Theme")

themeType = st.sidebar.selectbox("Pick a destination theme",
                                 ["Sports", "Scientific", "Natural Attraction", "Historical Place", "Entertainment"])

if themeType:
    results = langchain_helper.destination_and_activity_generator(themeType)

    for result in results:
        # Split the destination into place and country
        if ',' in result['destination']:
            place = result['destination'].split(',', 1)
        else:
            place = result['destination']
            country = "Unknown"  # Assign 'Unknown' if no country is provided

        # Display destination with formatting
        st.markdown(f"## **{place.strip()}**")
        st.markdown(f"**Country:** {country.strip()}")

        # Display activities with bullet points
        st.write("**Activities:**")
        for activity in result['activities']:
            st.write(f"- {activity}")
