
**Instructions: Retrieve a List of Sun Temples using Google Generative AI on Vertex AI**

Follow these steps to set up your environment and run a Python script that uses Google's Generative AI models via Vertex AI to list Sun temples.

**1. Install the Google Generative AI SDK**

Open your terminal and run the following command to install or upgrade the necessary Python library:

```bash
pip install --upgrade google-genai
```

*Note: If you manage Python environments, ensure you install this in the correct one.*

**2. Install the Google Cloud CLI (gcloud)**

If you don't have the gcloud CLI installed, follow the steps for your Linux distribution:

* **For Debian or Ubuntu-based systems:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y apt-transport-https ca-certificates gnupg curl

    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
      sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | \
      sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

    sudo apt-get update
    sudo apt-get install google-cloud-sdk
    ```

* **For CentOS, Fedora, or RHEL-based systems:**
    ```bash
    sudo tee /etc/yum.repos.d/google-cloud-sdk.repo <<EOF
    [google-cloud-sdk]
    name=Google Cloud SDK
    baseurl=https://packages.cloud.google.com/yum/repos/cloud-sdk-el$(rpm -E %{rhel})-x86_64
    enabled=1
    gpgcheck=1
    repo_gpgcheck=0
    gpgkey=https://packages.cloud.google.com/yum/doc/yum-key.gpg https://packages.cloud.google.com/yum/doc/rpm-gpg-key-el$(rpm -E %{rhel})-x86_64
    EOF

    # Use dnf if available (RHEL/CentOS 8+, Fedora), otherwise use yum
    if command -v dnf &> /dev/null; then
      sudo dnf install google-cloud-sdk
    else
      sudo yum install google-cloud-sdk
    fi
    ```

**3. Authenticate and Set Project for Application Default Credentials (Required)**

This single command authenticates your environment using Application Default Credentials (ADC) and specifies the Google Cloud project to use for billing and API access associated with these credentials.

**Run the following command, replacing `YOUR_PROJECT_ID` with your actual Google Cloud Project ID:**

```bash
gcloud auth application-default login --project=YOUR_PROJECT_ID
```

Follow the on-screen instructions, which will likely open a web browser for authorization. Make sure you replace `YOUR_PROJECT_ID` with the correct project ID before running the command.

**4. Create the Python Script**

Use the following command to create a file named `google_ai.py` containing the exact Python code you provided. Run this in the directory where you want the script saved.

```bash
cat << 'EOF' > google_ai.py
from google import genai
from google.genai import types
# import base64 # Note: base64 was imported but not used, commented out.

def generate():
  # --- USER CONFIGURATION REQUIRED ---
  # IMPORTANT: Replace "prj-abx-xyz-69900" with your actual Google Cloud Project ID.
  #            This should match the project ID used during authentication.
  # IMPORTANT: Verify/replace "europe-west4" with your desired Google Cloud region.
  # ---
  client = genai.Client(
      vertexai=True,
      project="prj-abx-xyz-69900",
      location="europe-west4",
  )

  # IMPORTANT: Verify this model name ("gemini-2.0-flash-001").
  #            Ensure it exists and is available in your project/region.
  #            Standard Vertex AI model names often follow patterns like 'gemini-1.5-flash-preview-0514'.
  model = "gemini-2.0-flash-001"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text="""Give me list of Sun temples ? just the name:city""")
      ]
    ),
  ]

  # --- SAFETY SETTINGS & CONFIG ---
  # WARNING: The safety settings below disable all content safety filters (threshold="OFF").
  # This is generally NOT recommended due to the risk of generating harmful content.
  # Consider using default protections or adjusting thresholds responsibly (e.g., threshold="BLOCK_MEDIUM_AND_ABOVE").
  # The SDK might expect an enum like types.HarmBlockThreshold.BLOCK_NONE instead of the string "OFF".
  #
  # NOTE: The parameter name 'config' below might need to be 'generation_config'
  #       depending on the SDK version and method used. If the script errors, try changing 'config'
  #       to 'generation_config'.
  # ---
  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 0.95,
    max_output_tokens = 8192,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
  )

  print(f"Attempting to generate content using model '{model}'...")
  try:
    # Using the streaming method as provided in your code.
    for chunk in client.models.generate_content_stream(
      model = model,
      contents = contents,
      config = generate_content_config, # Potential issue: should this be 'generation_config'?
      ):
      print(chunk.text, end="")
    print() # Add a final newline after streaming completes.

  except Exception as e:
      print(f"\n\n--- ERROR ---")
      print(f"An error occurred during content generation: {e}")
      print("Troubleshooting suggestions:")
      print("- Verify the project ID and location are correct.")
      print("- Ensure you authenticated with 'gcloud auth application-default login --project=YOUR_PROJECT_ID'.")
      print("- Double-check the model name ('{model}') is correct and available in project/region.")
      print("- Ensure the Vertex AI API is enabled in your Google Cloud project.")
      print("- Check if the parameter 'config' should be 'generation_config' in the call to generate_content_stream.")
      print("---------------")

generate()
EOF
```

**Important Notes Recap:**
* **Replace Project ID**: You MUST edit the `google_ai.py` file and replace `"prj-abx-xyz-69900"` with your specific Google Cloud Project ID.
* **Verify Location**: Check if `"europe-west4"` is the correct region for your project and the model.
* **Verify Model Name**: Double-check if `"gemini-2.0-flash-001"` is the correct and available model identifier for your setup.
* **Safety Settings**: Be aware of the `WARNING` regarding `safety_settings` being turned `OFF`. This disables critical safety filters. Review and adjust as needed. Also, note the potential issue with using the string `"OFF"` instead of an SDK enum.
* **`config` vs `generation_config`**: Be aware of the potential parameter name issue mentioned in the code comments. If the script fails with an error related to unexpected keyword arguments, try changing `config = generate_content_config` to `generation_config = generate_content_config`.
* **API Enablement**: Ensure the "Vertex AI API" is enabled in your Google Cloud project.

**5. Run the Script**

Navigate to the directory where you saved `google_ai.py` in your terminal and run the script using Python 3:

```bash
python3 google_ai.py
```

**6. Expected Output (Example)**

If the configuration is correct and the API call succeeds, you should see streaming output similar to this (the exact list and details may vary), followed by a newline:

```
Attempting to generate content using model 'gemini-2.0-flash-001'...
Konark Sun Temple: Konark
Modhera Sun Temple: Modhera
Martand Sun Temple: Anantnag
Suryanar Kovil: Kumbakonam
Arasavalli Suryanarayana Temple: Arasavalli

```
If an error occurs, check the error message printed by the script and the troubleshooting suggestions.

---