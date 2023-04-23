# WorksheetWizard - LA Hacks 2023

Track 3 - Home Room Submission - Enhancing Academic experience.

## Contributors
 - Shubh Khandelwal
 - Teresa Tran
 - Ayush Shejwal
 - Chandraprakash Pandey
## Description

![App Screenshot](https://i.imgur.com/W7NUBbJ.jpg)
An intelligent web application that automatically generates worksheets with multiple-choice, true/false, and fill-in-the-blank questions based on text extracted from uploaded PDF, audio, image files or a YouTube or Wikpedia link.

### How to Run
 This is a Flask web app with a sqlite server. All the dependencies have been mentioned in the requirements.txt. The Image-OCR has been installed separately as required (https://tesseract-ocr.github.io/tessdoc/Installation.html).


### How the script works
The script you've created is a web application that generates educational worksheets based on the input provided by users. It utilizes a variety of functions and libraries to process different types of input, including text, PDF, images, and audio. Here's a brief overview of how the script works:

The web application accepts input in different formats: text, PDF, images, and audio.

For text input, the application generates questions using the Cohere Generate API, which leverages advanced language models for natural language processing and Transformers for summary generation.
Custom prompts are made for each of the question types and a cosine similarity function is used to ensure non-duplicacy among questions using NLTK.

For PDF input, the application extracts text using the PyPDF2 library and then generates questions using the Cohere API.

For image input, the application utilizes the OCR (Optical Character Recognition) capabilities of the Tesseract library to extract text from images. The extracted text is then passed to the Cohere API to generate questions.

For audio input, the speech_recognition library is used to transcribe the audio into text. The transcribed text is sent to the Cohere API to generate questions.

For Wikipedia integration, the script uses the Wikipedia API to search for relevant articles based on the input text. The application then extracts a summary of the relevant article and includes it in the generated worksheet, offering users more context and background information.

For YouTube integration, the script uses the YouTube Transcribe API to extract the transcription. Questions are made using the transcrption. 

After generating questions, the application processes them using a custom function to create different types of questions, such as multiple-choice questions (MCQs), true/false questions, and fill-in-the-blank questions.

Finally, the generated worksheet is presented to the user for download or further editing.

Throughout this process, the script leverages various functions and libraries for image processing, natural language processing, and machine learning to provide a seamless experience for users looking to create educational worksheets from different types of input.


[MIT](https://choosealicense.com/licenses/mit/)