<div align="center">
  <br />
  <br />
  <h2>Youtube <> LLMs</h2>
  <h4>Extendable and customizable API to transcript Youtube videos along with LLM-powered summaries, chapters, and analysis.</h4>
</div>


## Overview
<br /> 
<br />

## Setup and Installation

```
pip install -r requirements.txt
```

**Prerequisites**


**Installation**


## Individual Features

* Summary Generation: Condenses the video transcript into a short, comprehensive summary.
* Bullet Points Generation: Extracts key points from the transcript and presents them in bullet-point format.
* Transcription Formatting: Improves the readability of the raw transcript by adding punctuation and paragraph breaks.

**Starting the Server**


## API Endpoint
POST `/submit` - Submit a link for transcription and title retrieval. <br />
Body: `{ "link": "URL" }` <br /> 
Output: `{ text, summary, title, tags, chapters }`







