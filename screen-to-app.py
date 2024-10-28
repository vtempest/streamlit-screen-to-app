import streamlit as st
import subprocess
import sys
import base64
import webbrowser
from pathlib import Path
import time
from groq import Groq
import os
from typing import List, Tuple
from PIL import Image
import io
import json

class LLMAppGenerator:
    def __init__(self, api_key: str):
        self.client = Groq(api_key="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")
        self.app_file = "generated_app.py"
        self.streamlit_process = None
        self.apikey = "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"
        self.model = "llama-3.1-8b-instant"  # Using llama2 model with 4K context
        self.max_tokens = 4048  # Reduced token limit for safety

    def compress_image(self, image_path: str, max_size=(800, 800)) -> str:
        """Compress and encode image to base64 string."""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Resize if larger than max_size
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save compressed image to bytes
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=70, optimize=True)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def generate_prompt(self, screenshots: List[str]) -> List[str]:
        """Generate prompts broken down into smaller chunks."""
        base_prompt = """Generate a Streamlit application with these features:
        - SQLite database for storage
        - Issue creation and listing functionality
        - Clean UI and error handling
        - Form validation
        
        Return only the Python code, no explanations."""

        # Process screenshots in chunks
        prompts = []
        for i, screenshot in enumerate(screenshots, 1):
            compressed_image = self.compress_image(screenshot)
            prompt = f"{base_prompt}\n\nAnalyze this screenshot and incorporate its UI elements:\n<image>{compressed_image}</image>"
            prompts.append(prompt)

        return prompts

    def generate_app(self, screenshots: List[str]) -> str:
        """Generate the Streamlit application code using multiple prompts."""
        prompts = self.generate_prompt(screenshots)
        generated_codes = []

        for i, prompt in enumerate(prompts, 1):
            st.write(f"Processing screenshot {i}/{len(prompts)}...")
            
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.7,
                max_tokens=self.max_tokens,
            )
            
            code = self._extract_code(completion.choices[0].message.content)
            generated_codes.append(code)

        # Combine the generated codes
        if len(generated_codes) > 1:
            # Send another prompt to combine the codes
            combine_prompt = f"""Combine these code segments into a single coherent Streamlit application:

{json.dumps(generated_codes, indent=2)}

Return only the final combined Python code."""

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": combine_prompt
                }],
                temperature=0.7,
                max_tokens=self.max_tokens,
            )
            
            final_code = self._extract_code(completion.choices[0].message.content)
        else:
            final_code = generated_codes[0]

        return final_code

    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM's response."""
        # Remove any markdown code blocks
        if "```python" in response:
            code = response.split("```python")[1].split("```")[0]
        elif "```" in response:
            code = response.split("```")[1].split("```")[0]
        else:
            code = response
        return code.strip()

    def save_app(self, code: str) -> None:
        """Save the generated code to a file."""
        with open(self.app_file, "w") as f:
            f.write(code)

    def update_app(self, user_changes: str) -> None:
        """Update the application based on user feedback."""
        with open(self.app_file, "r") as f:
            current_code = f.read()

        # Break down the update into smaller chunks
        update_prompt = f"""Current code needs these changes:
            {user_changes}

            Focus on implementing these specific changes while maintaining the app's core functionality.
            Return only the modified Python code."""

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": update_prompt
            }],
            temperature=0.7,
            max_tokens=self.max_tokens,
        )

        updated_code = self._extract_code(completion.choices[0].message.content)
        self.save_app(updated_code)

    def cleanup(self) -> None:
        """Clean up resources."""
        if self.streamlit_process:
            self.streamlit_process.terminate()

def main():
    st.set_page_config(page_title="LLM App Generator", page_icon="🤖")
    
    st.title("LLM-Powered App Generator")
    st.caption("Using Llama 2 70B model")
    
    # Get API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter your Groq API key:", type="password")
        if not api_key:
            st.warning("Please provide a Groq API key to continue")
            return

    # Initialize generator
    generator = LLMAppGenerator(api_key)

    # File uploader with size limit
    st.info("Please upload screenshots (max 5MB each)")
    uploaded_files = st.file_uploader(
        "Upload screenshots of the application you want to replicate",
        accept_multiple_files=True,
        type=['png', 'jpg', 'jpeg']
    )

    if uploaded_files:
        # Validate file sizes
        total_size = sum(file.size for file in uploaded_files)
        if total_size > 15 * 1024 * 1024:  # 15MB total limit
            st.error("Total file size exceeds 15MB limit")
            return

        # Save uploaded files temporarily
        screenshot_paths = []
        for uploaded_file in uploaded_files:
            # Create a temporary file
            temp_path = f"temp_{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            screenshot_paths.append(temp_path)

        if st.button("Generate Application"):
            with st.spinner("Generating application..."):
                try:
                    # Progress bar
                    progress_bar = st.progress(0)
                    
                    # Generate initial app
                    code = generator.generate_app(screenshot_paths)
                    generator.save_app(code)
                    
                    progress_bar.progress(100)
                    st.success("Application generated successfully!")
                    
                    # Show the generated code with syntax highlighting
                    st.code(code, language="python")
                    
                    # Download button
                    with open(generator.app_file, "rb") as file:
                        st.download_button(
                            label="📥 Download generated app",
                            data=file,
                            file_name="generated_app.py",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Error generating application: {str(e)}")
                finally:
                    # Cleanup temporary files
                    for path in screenshot_paths:
                        try:
                            os.remove(path)
                        except:
                            pass

        # User feedback section
        st.divider()
        st.subheader("Request Changes")
        user_changes = st.text_area(
            "Describe the changes you want to make:",
            help="Be specific about what you want to change in the generated app."
        )
        
        if st.button("Update Application") and user_changes:
            with st.spinner("Updating application..."):
                try:
                    generator.update_app(user_changes)
                    st.success("Application updated successfully!")
                    
                    # Show updated code
                    with open(generator.app_file, "r") as f:
                        updated_code = f.read()
                    st.code(updated_code, language="python")
                    
                    # Download button for updated code
                    with open(generator.app_file, "rb") as file:
                        st.download_button(
                            label="📥 Download updated app",
                            data=file,
                            file_name="generated_app.py",
                            mime="text/plain"
                        )
                except Exception as e:
                    st.error(f"Error updating application: {str(e)}")


if __name__ == "__main__":
    main()