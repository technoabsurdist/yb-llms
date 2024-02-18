
def summary_prompt(text):
    return f"""
    Please provide a concise and comprehensive summary of the following text. 
    The summary should capture the main points and key details accurately, 
    presenting the author's intended meaning. Ensure the summary is well-organized, 
    easy to read, and includes clear main points without unnecessary information. 
    Aim for brevity while maintaining completeness.
    \nText: '{text}'\n\n\n
    """

def format_prompt(text):
    return f"""
    The following text is the transcription of a YouTube video.
    It's currently missing all sorts of punctuation and paragraph separation.  
    Your task is to return the exact same text with the added punctuation and paragraph separation.
    Take your most rational guesses as to where those would be. 
    Here is the text: \n\n{text}\n\n
    """

def bps_prompt(text):
    return f"""
    Please summarize the following text into 5 bullet points. 
    Each bullet point should capture a key aspect or main point of the text, 
    ensuring a comprehensive overview of the content. 
    The bullet points should be concise, directly to the point, and organized in a logical order. 

    Here is the text: \n\n{text}\n\n
    """
