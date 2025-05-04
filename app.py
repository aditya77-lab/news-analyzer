import streamlit as st
import pandas as pd
import google.generativeai as genai
import os
import time

def initialize_gemini():
    genai.configure(api_key="AIzaSyDlcMA_ozPywPhthEPTbQDKBQRAA97jH7Y")  # Replace with your actual API key

    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        system_instruction=(
            "I will give you news articles. Summarize each article so an average human being "
            "can read it in under 60 seconds. In a new line print - "
            "trust score (numerical value), source if available, sentiment analysis (positive, neutral, or negative), "
            "and political alignment (left, center, or right)."
        ),
    )

    chat_session = model.start_chat(history=[])
    
    return chat_session

def get_gemini_response(chat_session, description, retries=3):
    try:
        response = chat_session.send_message(description)
        return response
    except Exception as e:
        st.write(f"Error: {str(e)}")
        if retries > 0:
            st.write("Retrying request after 5 seconds...")
            time.sleep(5)
            return get_gemini_response(chat_session, description, retries - 1)
        else:
            st.write("Max retries reached. Skipping this request.")
            return None

def load_data():
    news_data = pd.read_csv('data_with_topics.csv').head(500)
    news_data['topics'] = news_data['topics'].apply(lambda x: [topic.strip().lower().capitalize() for topic in x.split(',')])
    return news_data

def aggregate_topics(news_data):
    exploded_data = news_data.explode('topics')
    top_6_topics = exploded_data['topics'].value_counts().head(6).index.tolist()
    return exploded_data, top_6_topics

def main():
    st.markdown("<h1 style='text-align: center;'>Briefly</h1>", unsafe_allow_html=True)

    news_data = load_data()

    exploded_data, top_6_topics = aggregate_topics(news_data)

    num_topics = len(top_6_topics)
    cols = st.columns(num_topics)

    selected_topic = None
    for i, col in enumerate(cols):
        if col.button(top_6_topics[i], key=f"{top_6_topics[i]}_{i}"):
            selected_topic = top_6_topics[i]

    if not selected_topic:
        selected_topic = top_6_topics[0]

    filtered_news_data = exploded_data[exploded_data['topics'] == selected_topic]

    articles_to_display = st.session_state.get('articles_to_display', 5)

    articles_to_show = filtered_news_data.head(articles_to_display)

    chat_session = initialize_gemini()

    requests_made = 0
    total_articles = len(articles_to_show)

    for _, row in articles_to_show.iterrows():
        gemini_response = get_gemini_response(chat_session, row['content'])

        card_content = f"""
            <div style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); margin-bottom: 20px; color: black;">
                <h3 style="color: black;">{row['title']}</h3>
                <p style="color: black;">{gemini_response.text if gemini_response else "No response available"}</p>
                <p style="color: black; font-style: italic;">Read more: <a href="{row['link']}" target="_blank">{row['link']}</a></p>
            </div>
        """

        st.markdown(card_content, unsafe_allow_html=True)

        requests_made += 1

    if len(filtered_news_data) > articles_to_display:
        st.markdown('<div style="text-align: center;">', unsafe_allow_html=True)
        if st.button('Load More'):
            st.session_state['articles_to_display'] = articles_to_display + 5
        st.markdown('</div>', unsafe_allow_html=True)

    if requests_made >= 15:
        st.write("Processed 15 articles. Waiting for 60 seconds before continuing...")
        time.sleep(60)
        requests_made = 0

if __name__ == "__main__":
    main()
