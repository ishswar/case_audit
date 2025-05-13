
**Steps to Retrieve a List of Sun Temples using Google Generative AI:**

1.  **Install the Google Generative AI SDK:**
    Open your terminal or command prompt and execute the following command to install or upgrade the necessary Python library:
    ```bash
    pip install --upgrade google-genai
    ```
    *Note: The correct package name is `google-genai`.*

2.  **Authenticate with Google Cloud:**
    Ensure you are authenticated with your Google Cloud account. If you have the Google Cloud CLI installed, run:
    ```bash
    gcloud auth application-default login
    ```
    Follow the on-screen instructions in your web browser to authorize your application.

3.  **Create the Python Script:**
    You will need to create a Python file. You can do this using a text editor or by using the terminal command below. This command will create a file named `google_ai.py` and paste the following Python code into it:

    ```bash
    cat << 'EOF' > google_ai.py
    from google import genai
    from google.genai import types
    import base64

    def generate():
      client = genai.Client(
          vertexai=True,
          project="prj-asg-dev-60350",
          location="us-central1",
      )

      model = "gemini-2.5-pro-preview-05-06"
      contents = [
        types.Content(
          role="user",
          parts=[
            types.Part.from_text(text="Provide a list of Sun temples, formatted as 'name:city'.")
          ]
        ),
      ]

      generate_content_config = types.GenerateContentConfig(
        temperature=1,
        top_p=0.95,
        seed=0,
        max_output_tokens=8192,
        response_modalities=["TEXT"],
        safety_settings=[
          types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
          types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
          types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
          types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF")
        ],
      )

      for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
      ):
        print(chunk.text, end="")

    generate()
    EOF
    ```
    *To manually create the file, open a text editor, paste the code above, and save the file as `google_ai.py` in your desired directory.*

4.  **Run the Script:**
    Navigate to the directory where you saved the `google_ai.py` file in your terminal and execute the script using the Python interpreter:
    ```bash
    python google_ai.py
    ```

5.  **Expected Output (Example):**
    After the script runs successfully, you should see output similar to the following in your terminal:

    ```
    Konark Sun Temple: Konark
    Modhera Sun Temple: Modhera
    Martand Sun Temple: Anantnag
    Suryanar Kovil: Kumbakonam
    Arasavalli Suryanarayana Temple: Arasavalli
    Dakshinaarka Temple: Gaya
    Katarmal Sun Temple: Almora
    Surya Pahar Temple: Goalpara
    Biranchinarayan Temple: Buguda
    ```
