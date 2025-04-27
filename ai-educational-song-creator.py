import openai
import requests
import streamlit as st
from PIL import Image
import pytesseract
import time

# Set up OpenAI API key
openai.api_key = ""  # Replace this with your actual OpenAI API key

# Function to generate a response based on the topic or passage
def get_appropriate_detail(input_text, difficulty_level=None):
    prompt = f"Based on the following passage or topic, how much detail is appropriate for a {difficulty_level} level student? Provide a brief summary with the key points:\n{input_text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.7
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        return f"An error occurred: {e}"

# Function to get appropriate length for the song
def get_appropriate_length(word_length_range=None):
    min_words, max_words = 0, 0
    if word_length_range == "150-200 words":
        min_words, max_words = 150, 200
    elif word_length_range == "200-400 words":
        min_words, max_words = 200, 400
    elif word_length_range == "400-600 words":
        min_words, max_words = 400, 600

    return min_words, max_words

# Function to generate song lyrics based on input data and difficulty level
def generate_song(topic, summary, min_words, max_words, keywords=None, difficulty_level=None, custom_prompt=None):
    prompt = f"Create a song for a {difficulty_level} level student based on the following summary:\n{summary}\nThe song should be between {min_words} and {max_words} words."
    
    if keywords:
        prompt += f"\nUse the following keywords: {', '.join(keywords)}"
    
    if custom_prompt:
        prompt += f"\nThe song should have the following mood/genre: {custom_prompt}"
    
    try:
        while True:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            song_lyrics = response['choices'][0]['message']['content'].strip()
            word_count = len(song_lyrics.split())
            if min_words <= word_count <= max_words:
                break

        return song_lyrics, word_count
    except Exception as e:
        return f"An error occurred: {e}", 0

# Function for OCR (Extracting text from an image)
def extract_text_from_image(image):
    text = pytesseract.image_to_string(image)
    return text

# Function to generate song from TopMediai API
def generate_song_from_api(is_auto, prompt, lyrics, title, instrumental, model_version):
    url = "https://api.topmediai.com/v2/submit"
    headers = {"Content-Type": "application/json", "x-api-key": ""}  # Replace with your actual API key
    
    payload = {
        "is_auto": is_auto,
        "prompt": prompt,
        "lyrics": lyrics if is_auto == 0 else "",
        "title": title,
        "instrumental": instrumental,
        "model_version": model_version,
        "continue_at": 0,
        "continue_song_id": ""
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        print("API Response Status Code:", response.status_code)  # Log the response status code
        if response.status_code == 200:
            data = response.json()
            print("API Response Data:", data)  # Log the full response data
            # Update here: Get the audio URL from 'audio' key
            song_url = data['data'][0].get('audio', None)
            if song_url:
                return song_url
            else:
                return "Error: No audio URL in response."
        else:
            return f"Failed to generate song: {response.text}"
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit Frontend
def main():
    # Title and Welcome Message
    st.title("Educational Song Generator")
    st.markdown("Welcome! This tool helps you create an educational song for students based on a topic, passage, or keywords.")

    # Dropdown to select whether it's a topic, passage, or keywords
    input_type = st.selectbox("Select Input Type:", ["Keywords/Passage", "Topic", "Upload Image for OCR"])
    
    input_text = None  # Initialize input_text variable
    
    if input_type == "Topic":
        input_text = st.text_area("Enter the Topic.")
        difficulty_level = st.selectbox("Select difficulty level:", ["Beginner", "Intermediate", "Advanced/Professional"])
        keywords = None
        if not difficulty_level:
            st.error("Please select a difficulty level.")
            return  # Stop execution if difficulty level is not selected
            
    elif input_type == "Keywords/Passage":
        input_text = st.text_area("Enter the keywords or passage. If using keywords, separate them by commas:")
        keywords_input = input_text
        keywords = [kw.strip() for kw in keywords_input.split(',')] if keywords_input else None
        difficulty_level = None  # No difficulty level required for keywords/passage
        
    elif input_type == "Upload Image for OCR":
        uploaded_image = st.file_uploader("Upload an image for OCR", type=["jpg", "png", "jpeg"])
        if uploaded_image is not None:
            image = Image.open(uploaded_image)
            input_text = extract_text_from_image(image)  # Extract text using OCR
            st.image(image, caption="Uploaded Image.", use_column_width=True)
            st.text_area("Extracted Text from Image", input_text)
            keywords = None  # No keywords are needed when using OCR
            difficulty_level = None  # No difficulty level needed for image-based input

    # Ensure input_text is provided
    if not input_text:
        st.error("Please enter the topic, passage, keywords, or upload an image.")
        return

    # Allow the user to provide a custom prompt (e.g., "happy", "sad", "motivational", etc.)
    custom_prompt = st.text_input("Enter the desired mood or theme of the song (e.g., happy, sad, motivational):")

    # Dropdown to select the word length range for the song lyrics
    word_length_range = st.selectbox(
        "Select the word length range for the song lyrics:",
        ["150-200 words", "200-400 words", "400-600 words"]
    )
    
    # Button to generate the song
    if st.button("Generate Song"):
        # Get the appropriate detail for the song based on difficulty level and passage/topic
        summary = get_appropriate_detail(input_text, difficulty_level)
        
        # Get the appropriate length bounds based on user's word length preference
        min_words, max_words = get_appropriate_length(word_length_range)
        
        # Generate the song lyrics based on the above inputs
        song_lyrics, word_count = generate_song(input_text, summary, min_words, max_words, keywords, difficulty_level, custom_prompt)

        # Display the output song lyrics
        st.subheader("Generated Song Lyrics:")
        st.write(song_lyrics)
        
        # Display the word count of the generated song
        st.subheader("Total Word Count:")
        st.write(word_count)

        # Choose whether the song will be instrumental or have vocals
        instrumental = st.radio("Do you want an instrumental version?", ("Vocals", "Instrumental"))
        instrumental = 1 if instrumental == "Instrumental" else 0

        # Choose the model version based on the song length
        model_version = "v3.5" if word_count > 200 else "v3.0"

        # Generate the song from the TopMediai API
        song_url = generate_song_from_api(is_auto=0, prompt="Educational song", lyrics=song_lyrics, title="Educational Song", instrumental=instrumental, model_version=model_version)

        if song_url and song_url.startswith('http'):
            st.subheader("Download Your Song:")
            st.markdown(f"[Download the song]({song_url})")
            st.audio(song_url)
        else:
            st.error(f"Failed to generate a valid audio file URL. Response: {song_url}")

if __name__ == "__main__":
    main()
