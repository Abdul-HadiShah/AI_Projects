import streamlit as st
import pymongo
from bson import ObjectId
import openai
import requests

# Set up OpenAI API key
openai.api_key = ''

# MongoDB connection setup
client = pymongo.MongoClient(
    "",
    tls=True  # Correctly using TLS (SSL)
)
db = client[""]  # Database name
collection = db[""]  # Collection name

# Function to get user data from MongoDB by user_id
def get_user_data(user_id):
    user_data = collection.find_one({"_id": ObjectId(user_id)})
    return user_data

# Function to call OpenAI model for vacation recommendations
def get_vacation_recommendations(user_data):
    # city = user_data.get("destination", "Unknown City")
    # temperature = user_data.get("preferred_temperature", 25)  # Assuming a default value if not found
    # climate = user_data.get("preferred_climate", "Temperate")
    # budget = user_data.get("budget", "$2000-$5000")

    prompt = f"""
    Recommend a vacation destination based on the users previous experience which he has recorded as follows
    {user_data}

    Provide hotel, flight, and destination recommendations that fit these preferences.
    """
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # or "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=300  # Adjusted token limit for longer response
    )
    
    return response['choices'][0]['message']['content'].strip()

# Streamlit UI for input
def main():
    st.title("Vacation Planner")

    # Input for user ID
    user_id = st.text_input("Enter your User ID:")

    if st.button("Get Vacation Recommendations"):
        if user_id:
            # Query MongoDB for user data based on the input user ID
            user_data = get_user_data(user_id)
            
            if user_data:
                #st.write(f"### User Data: {user_data}")
                
                # Use the user data to get vacation recommendations from OpenAI
                recommendations = get_vacation_recommendations(user_data)
                st.write("### Vacation Recommendations from AI:")
                st.write(recommendations)

                # Optional: You can call APIs to show real-time data (e.g., flights, hotels)

                # Example: Get flight information from Skyscanner (This is a simplified example)
                flight_api_key = 'YOUR_SKYSCANNER_API_KEY'  # Replace with your Skyscanner API key
                flight_url = f"https://partners.api.skyscanner.net/apiservices/browsequotes/v1.0/US/USD/en-US/{user_data['destination']}/anywhere/anytime?apiKey={flight_api_key}"
                flight_response = requests.get(flight_url)
                
                if flight_response.status_code == 200:
                    flight_data = flight_response.json()
                    st.write("### Flights:")
                    for flight in flight_data['Quotes']:
                        st.write(f"Flight: {flight['MinPrice']} USD")
                else:
                    st.write("Unable to fetch flight data.")

                # Example: Get hotel information from Booking.com (This is a simplified example)
                hotel_api_key = 'YOUR_BOOKING_API_KEY'  # Replace with your Booking.com API key
                hotel_url = f"https://api.booking.com/v1/hotels?location={user_data['destination']}&checkin_date=2025-02-01&checkout_date=2025-02-07&apiKey={hotel_api_key}"
                hotel_response = requests.get(hotel_url)

                if hotel_response.status_code == 200:
                    hotel_data = hotel_response.json()
                    st.write("### Hotels:")
                    for hotel in hotel_data['results']:
                        st.write(f"Hotel: {hotel['name']} - Price: {hotel['price']} USD")
                else:
                    st.write("Unable to fetch hotel data.")
            else:
                st.write(f"No user found with ID {user_id}. Please check your ID and try again.")
        else:
            st.write("Please enter a User ID to get recommendations.")

if __name__ == "__main__":
    main()
