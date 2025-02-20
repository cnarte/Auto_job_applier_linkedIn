from config.secrets import *
from config.settings import showAiErrorAlerts
from config.personals import ethnicity, gender, disability_status, veteran_status
from config.questions import *
from config.search import security_clearance, did_masters

from modules.helpers import print_lg, critical_error_log, convert_to_json
from modules.ai.prompts import *

from pyautogui import confirm
from openai import OpenAI
from openai.types.model import Model
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from typing import Iterator, Literal
from selenium.webdriver.common.by import By


apiCheckInstructions = """

1. Make sure your AI API connection details like url, key, model names, etc are correct.
2. If you're using an local LLM, please check if the server is running.
3. Check if appropriate LLM and Embedding models are loaded and running.

Open `secret.py` in `/config` folder to configure your AI API connections.

ERROR:
"""

# Function to show an AI error alert
def ai_error_alert(message: str, stackTrace: str, title: str = "AI Connection Error") -> None:
    """
    Function to show an AI error alert and log it.
    """
    global showAiErrorAlerts
    if showAiErrorAlerts:
        if "Pause AI error alerts" == confirm(f"{message}{stackTrace}\n", title, ["Pause AI error alerts", "Okay Continue"]):
            showAiErrorAlerts = False
    critical_error_log(message, stackTrace)


# Function to check if an error occurred
def ai_check_error(response: ChatCompletion | ChatCompletionChunk) -> None:
    """
    Function to check if an error occurred.
    * Takes in `response` of type `ChatCompletion` or `ChatCompletionChunk`
    * Raises a `ValueError` if an error is found
    """
    if response.model_extra.get("error"):
        raise ValueError(
            f'Error occurred with API: "{response.model_extra.get("error")}"'
        )


# Function to create an OpenAI client
def ai_create_openai_client() -> OpenAI:
    """
    Function to create an OpenAI client.
    * Takes no arguments
    * Returns an `OpenAI` object
    """
    try:
        print_lg("Creating OpenAI client...")
        if not use_AI:
            raise ValueError("AI is not enabled! Please enable it by setting `use_AI = True` in `secrets.py` in `config` folder.")
        
        client = OpenAI(base_url=llm_api_url, api_key=llm_api_key)

        # models = ai_get_models_list(client)
        # if "error" in models:
        #     raise ValueError(models[1])
        # if len(models) == 0:
        #     raise ValueError("No models are available!")
        # if llm_model not in [model.id for model in models]:
        #     raise ValueError(f"Model `{llm_model}` is not found!")
        
        print_lg("---- SUCCESSFULLY CREATED OPENAI CLIENT! ----")
        print_lg(f"Using API URL: {llm_api_url}")
        print_lg(f"Using Model: {llm_model}")
        print_lg("Check './config/secrets.py' for more details.\n")
        print_lg("---------------------------------------------")

        return client
    except Exception as e:
        ai_error_alert(f"Error occurred while creating OpenAI client. {apiCheckInstructions}", e)


# Function to close an OpenAI client
def ai_close_openai_client(client: OpenAI) -> None:
    """
    Function to close an OpenAI client.
    * Takes in `client` of type `OpenAI`
    * Returns no value
    """
    try:
        if client:
            print_lg("Closing OpenAI client...")
            client.close()
    except Exception as e:
        ai_error_alert("Error occurred while closing OpenAI client.", e)



# # Function to get list of models available in OpenAI API
# def ai_get_models_list(client: OpenAI) -> list[ Model | str]:
#     """
#     Function to get list of models available in OpenAI API.
#     * Takes in `client` of type `OpenAI`
#     * Returns a `list` object
#     """
#     try:
#         print_lg("Getting AI models list...")
#         if not client: raise ValueError("Client is not available!")
#         models = client.models.list()
#         ai_check_error(models)
#         print_lg("Available models:")
#         print_lg(models.data, pretty=True)
#         return models.data
#     except Exception as e:
#         critical_error_log("Error occurred while getting models list!", e)
#         return ["error", e]



# Function to get chat completion from OpenAI API
def ai_completion(client: OpenAI, messages: list[dict], response_format: dict = None, temperature: float = 0, stream: bool = stream_output) -> dict | ValueError:
    """
    Function that completes a chat and prints and formats the results of the OpenAI API calls.
    * Takes in `client` of type `OpenAI`
    * Takes in `messages` of type `list[dict]`. Example: `[{"role": "user", "content": "Hello"}]`
    * Takes in `response_format` of type `dict` for JSON representation, default is `None`
    * Takes in `temperature` of type `float` for temperature, default is `0`
    * Takes in `stream` of type `bool` to indicate if it's a streaming call or not
    * Returns a `dict` object representing JSON response, will try to convert to JSON if `response_format` is given
    """
    if not client: raise ValueError("Client is not available!")

    # Select appropriate client
    completion: ChatCompletion | Iterator[ChatCompletionChunk]
    if response_format and llm_spec in ["openai", "openai-like"]:
        completion = client.chat.completions.create(
                model=llm_model,
                messages=messages,
                temperature=temperature,
                stream=stream,
                response_format=response_format
            )
    else:
        completion = client.chat.completions.create(
                model=llm_model,
                messages=messages,
                temperature=temperature,
                stream=stream
            )

    result = ""
    
    # Log response
    if stream:
        print_lg("--STREAMING STARTED")
        for chunk in completion:
            ai_check_error(chunk)
            chunkMessage = chunk.choices[0].delta.content
            if chunkMessage != None:
                result += chunkMessage
            print_lg(chunkMessage, end="", flush=True)
        print_lg("\n--STREAMING COMPLETE")
    else:
        ai_check_error(completion)
        result = completion.choices[0].message.content
    
    if response_format:
        result = convert_to_json(result)
    
    print_lg("\nSKILLS FOUND:\n")
    print_lg(result, pretty=response_format)
    return result


def ai_extract_skills(client: OpenAI, job_description: str, stream: bool = stream_output) -> dict | ValueError:
    """
    Function to extract skills from job description using OpenAI API.
    * Takes in `client` of type `OpenAI`
    * Takes in `job_description` of type `str`
    * Takes in `stream` of type `bool` to indicate if it's a streaming call
    * Returns a `dict` object representing JSON response
    """
    print_lg("-- EXTRACTING SKILLS FROM JOB DESCRIPTION")
    try:        
        prompt = extract_skills_prompt.format(job_description)

        messages = [{"role": "user", "content": extract_skills_prompt}]

        return ai_completion(client, messages, response_format=extract_skills_response_format, stream=stream)
    except Exception as e:
        ai_error_alert(f"Error occurred while extracting skills from job description. {apiCheckInstructions}", e)



def ai_answer_question(
    client: OpenAI, 
    question: str, 
    user_info: str,
    question_type: str = 'text',
    input_requirements: dict = None,
    options: list[str] | None = None, 
    job_description: str = None, 
    about_company: str = None,
    stream: bool = stream_output
) -> str | ValueError:
    """
    Function to get AI answer for application questions.
    Returns a clean string answer based on input requirements.
    """
    print_lg("-- ANSWERING QUESTION")
    try:
        # Build prompt based on input requirements
        prompt_additions = []
        if input_requirements:
            if input_requirements["type"] == "numeric":
                prompt_additions.append(f"Provide a numeric answer")
                if input_requirements["min"] is not None:
                    prompt_additions.append(f"minimum: {input_requirements['min']}")
                if input_requirements["max"] is not None:
                    prompt_additions.append(f"maximum: {input_requirements['max']}")
            elif input_requirements["type"] == "phone":
                prompt_additions.append("Provide a valid phone number")
            elif input_requirements["type"] == "email":
                prompt_additions.append("Provide a valid email address")
            elif input_requirements["type"] == "url":
                prompt_additions.append("Provide a valid URL")
            elif input_requirements["type"] == "currency":
                prompt_additions.append("Provide a numeric amount")
            elif input_requirements["type"] == "date":
                prompt_additions.append("Provide a date in YYYY-MM-DD format")
            elif input_requirements["type"] == "select" and input_requirements["options"]:
                prompt_additions.append(f"Choose one of these options: {', '.join(input_requirements['options'])}")
            
            if input_requirements["pattern"]:
                prompt_additions.append(f"Answer must match pattern: {input_requirements['pattern']}")
            
            if input_requirements["required"]:
                prompt_additions.append("This field is required")
        
        requirements_str = " (" + "; ".join(prompt_additions) + ")" if prompt_additions else ""
        prompt = text_questions_prompt.format(question + requirements_str, user_info)
        print(" ########   Promt_used ######### \n")
        print_lg(prompt)
        messages = [{"role": "user", "content": prompt}]
        raw_response = ai_completion(client, messages, stream=False)
        print(" ########   Raw Output ######### \n")
        print_lg(raw_response)
        
        if isinstance(raw_response, str):
            try:
                # Extract answer between tags
                # Try both formats for start and end tags since the AI might use either format
                start_tag = "</start>" if "</start>" in raw_response else "<start>"
                end_tag = "</end>" if "</end>" in raw_response else "<end>"
                
                start_idx = raw_response.find(start_tag)
                end_idx = raw_response.find(end_tag)
                
                if start_idx != -1 and end_idx != -1:
                    # Add length of start tag to get position after the tag
                    answer = raw_response[start_idx + len(start_tag):end_idx].strip()
                    
                    # Validate and format answer based on type
                    if input_requirements:
                        if input_requirements["type"] == "numeric":
                            # Only apply numeric validation if type is explicitly numeric
                            answer = ''.join(filter(str.isdigit, answer)) or "0"
                            if input_requirements["min"] and int(answer) < int(input_requirements["min"]):
                                answer = input_requirements["min"]
                            if input_requirements["max"] and int(answer) > int(input_requirements["max"]):
                                answer = input_requirements["max"]
                        elif input_requirements["type"] == "currency":
                            # For currency, strip non-digits but don't validate as decimal
                            answer = ''.join(filter(str.isdigit, answer)) or "0"
                        elif input_requirements["type"] == "select" and input_requirements["options"]:
                            # Find closest matching option
                            answer = find_closest_match(answer, input_requirements["options"])
                        elif input_requirements["type"] == "phone":
                            answer = ''.join(filter(str.isdigit, answer))
                        # For text type, no validation needed - keep original answer
                    
                    print_lg(f"Formatted AI Answer: {answer}")
                    return answer
                else:
                    raise ValueError("Could not find answer between </start> and </end> tags")
            except Exception as e:
                print_lg(f"Error parsing AI response: {e}")
                print_lg(f"Raw response: {raw_response}")
                raise e
            
        raise ValueError(f"Unexpected response format from AI: {type(raw_response)}")
    except Exception as e:
        ai_error_alert(f"Error occurred while answering question. {apiCheckInstructions}", e)
        return str(e)

def find_closest_match(answer: str, options: list[str]) -> str:
    """Helper function to find closest matching option"""
    answer_lower = answer.lower()
    for option in options:
        if answer_lower == option.lower():
            return option
    # If no exact match, return first option as fallback
    return options[0] if options else answer



def ai_gen_experience(
    client: OpenAI, 
    job_description: str, about_company: str, 
    required_skills: dict, user_experience: dict,
    stream: bool = stream_output
) -> dict | ValueError:
    pass



def ai_generate_resume(
    client: OpenAI, 
    job_description: str, about_company: str, required_skills: dict,
    stream: bool = stream_output
) -> dict | ValueError:
    '''
    Function to generate resume. Takes in user experience and template info from config.
    '''
    pass



def ai_generate_coverletter(
    client: OpenAI, 
    job_description: str, about_company: str, required_skills: dict,
    stream: bool = stream_output
) -> dict | ValueError:
    '''
    Function to generate resume. Takes in user experience and template info from config.
    '''
    pass



##< Evaluation Agents
def ai_evaluate_resume(
    client: OpenAI, 
    job_description: str, about_company: str, required_skills: dict,
    resume: str,
    stream: bool = stream_output
) -> dict | ValueError:
    pass



def ai_check_job_relevance(
    client: OpenAI, 
    job_description: str, about_company: str,
    stream: bool = stream_output
) -> dict:
    pass
#>