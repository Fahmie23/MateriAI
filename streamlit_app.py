import streamlit as st
import openai
import pandas as pd
from collections import OrderedDict
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_image_from_dalle(description):
    """Generate an image based on the description using DALL·E."""
    try:
        response = openai.Image.create(
            model="image-alpha-001",
            prompt=description,
            n=1,
            size="256x256",
            response_format="url"
        )
        return response['data'][0]['url']
    except Exception as e:
        st.warning(f"Error generating image for '{description}': {e}")
        return None

def display_table(output):
    """Display material suggestions in a tabular format."""
    paragraphs = output.strip().split('\n\n')[1:-1]
    if not paragraphs:
        return pd.DataFrame()

    materials = []
    for material_info in paragraphs:
        material_info = material_info.strip()
        if material_info:
            lines = material_info.split("\n")
            if len(lines) > 2:
                material_name = re.sub(r"^\d+\.\s*|\:$", "", lines[0]).strip()
                properties = lines[1].replace("Properties: ", "").lstrip('- ').strip()
                pros = lines[2].replace("Pros: ", "").lstrip('- ').strip()
                cons = lines[3].replace("Cons: ", "").lstrip('- ').strip() if len(lines) > 3 else ""
                material = OrderedDict({
                    "Material": material_name,
                    "Properties": properties,
                    "Pros": pros,
                    "Cons": cons
                })

                image_url = get_image_from_dalle(material_name)
                if image_url:
                    material["Image"] = image_url
                else:
                    material["Image"] = "No Image"
                materials.append(material)

    df = pd.DataFrame(materials)
    df.reset_index(drop=True, inplace=True)
    return df

def fetch_brief_material_suggestions(summarized_input):
    """Fetch brief explanations highlighting key points regarding the materials."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"{summarized_input}. Please provide the main key points regarding the materials' properties, pros, and cons."
                }
            ],
            max_tokens=1000,
            temperature=0.4
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        return None

def fetch_detailed_material_suggestions(summarized_input):
    """Fetch detailed explanations regarding the materials."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": f"{summarized_input}. Please provide detailed explanations regarding the materials' properties, pros, and cons."
                }
            ],
            max_tokens=1000,
            temperature=0.4
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
        return None

def summarize_input(input_text):
    """Summarize the user input into a single sentence using GPT-3.5-turbo."""
    try:
        response = openai.Completion.create(
        model = "text-davinci-003",
        prompt = f"""
        Generate a one sentence, descriptive and concise prompt for the user input: {input_text}
        The output must be in one sentence.
        """,
        temperature = 0.2,
        max_tokens = 100
    )

        cover_prompt = response.choices[0].text
        return(cover_prompt)
    
    except Exception as e:
        st.error(f"❌ An error occurred during summarization: {e}")
        return None

def main():
    st.set_page_config(
        page_title="MateriAI",
        page_icon=":wrench:",
        layout="centered",
        initial_sidebar_state="auto"
    )

    st.markdown("""
    <style>
        .reportview-container {
            padding: 2rem 2rem;
            background-color: #f4f4f8;
        }
        h1, h2 {
            color: #1f77b4;
        }
        .custom-title {
            font-size: 4em;        /* Increase the font size */
            text-align: center;      /* Center the title */
            font-weight: bold;       /* Make it bold */
            color: #1f77b4;          /* Set the title color */
        }
        .stButton>button {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

    st.markdown('<div class="custom-title">MateriAI 🛠️</div>', unsafe_allow_html=True)
    st.markdown('Your one-stop solution for **Material Suggestions**!')
    st.markdown("---")

    st.markdown("**How to describe your project:**")
    st.markdown("""
        - Be specific about what you are trying to achieve.
        - Indicate the type of material properties you're interested in.
        - Example: 'I'm developing an electric car and need lightweight and durable materials for the chassis.'
    """, unsafe_allow_html=True)

    user_input = st.text_area(
        "📝 Describe your project:",
        help="Provide a clear and specific description for best results.",
        height=100
    )

    explanation_type = st.radio("Select explanation type:", ("Brief", "Detailed"))

    if st.button('🔍 Get Material Suggestions'):
        if not user_input.strip():
            st.warning('⚠️ Please enter a valid project description.')
        else:
            # Summarize the user input
            summarized_input = summarize_input(user_input)
            if not summarized_input:
                st.error("Failed to summarize the input. Please try again.")
                return

            # Inform the user of the summarized sentence
            st.markdown(f"**Summarized Project Description:** {summarized_input}")

            with st.spinner('🔄 Fetching material suggestions...'):
                if explanation_type == "Brief":
                    output = fetch_brief_material_suggestions(summarized_input)
                else:
                    output = fetch_detailed_material_suggestions(summarized_input)

                if output:
                    df = display_table(output)

                    # Displaying table with images
                    for _, row in df.iterrows():
                        material_name = row["Material"]
                        st.markdown(f"### {material_name}")
                        if row["Image"] != "No Image":
                            st.image(row["Image"], caption=material_name, use_column_width=True)
                        st.markdown(f"**Properties:** {row['Properties']}")
                        st.markdown(f"**Pros:** {row['Pros']}")
                        st.markdown(f"**Cons:** {row['Cons']}")
                        st.write("---")

                    st.success("🎉 Material suggestions fetched successfully!")

                    if st.button('💾 Save Output'):
                        filename = 'material_suggestions.csv'
                        df.drop(columns=['Image'], inplace=True)  # Remove Image URL before saving to CSV
                        df.to_csv(filename, index=False)
                        st.markdown(f'🔗 [Download Material Suggestions]({filename})')
                        st.success("Output saved successfully!")

if __name__ == '__main__':
    main()
