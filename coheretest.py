from cohere import Client
import json
from sscore import similarity_score
# Set up Cohere API key
api_key = 'OJSt94oO9pxwQUlJ16DAnOcsi0AYQyXwXa4s0PQq'
# Initialize Cohere client
co = Client(api_key=api_key)

def parse_question_response(obj):
    try:
        response = json.loads(obj)
        # print(response)
        if (
            "question" in response
            and "correct_answer" in response
            and "incorrect_answers" in response
        ):
            if len(response['incorrect_answers'])>=3:
                response['incorrect_answers'] = response['incorrect_answers'][:3]
                return response
        else:
            return None

    except json.JSONDecodeError:
        return None
    
def parse_tf_response(obj):
    try:
        response = json.loads(obj)
        if "question" in response and "correct_answer" in response:
            if isinstance(response["correct_answer"], bool):
                return response
        else:
            return None
    except json.JSONDecodeError:
        return None
def parse_fib_response(obj):
    try:
        response = json.loads(obj)
        if "question" in response and "correct_answer" in response:
            return response
        else:
            return None
    except json.JSONDecodeError:
        return None


def genPrompt(qtype, text):
    if qtype=="mcq":
        mcq_prompt = 'Given an input text about a topic:\n '+text+' \n\nIn Summary:\nGenerate a Multiple Choice test question from the above text. \nEach question object must have a correct_answer and exactly 3 incorrect_answers\nFormat the generated output as follows:\n{\n    \"question\": \"Your generated question here\",\n    \"correct_answer\": \"Correct answer\",\n    \"incorrect_answers\": [\"Incorrect answer 1\", \"Incorrect answer 2\", \"Incorrect answer 3\"]\n}'
        return mcq_prompt
    elif qtype=="tf":
        tf_prompt = 'Given an input text about a topic:\n '+text+' \n\nIn Summary:\nGenerate a True/False question from the above text. \nFormat the generated output as follows:\n{\n    \"question\": \"Your generated statement here\",\n    \"correct_answer\": true/false\n}'
        return tf_prompt
    elif qtype=="fib":
        fib_prompt = 'Given an input text about a topic:\n '+text+' \n\nIn Summary:\nGenerate a short answer style question from the above text. \nFormat the generated output as follows:\n{\n    \"question\": \"Your generated statement here\",\n    \"correct_answer\": "Correct answer"\n}'
        return fib_prompt
    else:
        print('err')
        return None
    
def generate_questions_with_cohere(text, qtype):
    # Use Cohere to generate questions based on the input text
    response = None
    while response is None:
        response =  response = co.generate(
            model='command-xlarge-nightly',
            num_generations=5,
            prompt=genPrompt(qtype=qtype, text=text),
            max_tokens=1203,
            temperature=0.5,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE')
    return (response.generations)

# trial_text="""
# The Indian independence movement was a series of historic events with the ultimate aim of ending British rule in India. It lasted from 1857 to 1947.

# The first nationalistic revolutionary movement for Indian independence emerged from Bengal. It later took root in the newly formed Indian National Congress with prominent moderate leaders seeking the right to appear for Indian Civil Service examinations in British India, as well as more economic rights for natives. The first half of the 20th century saw a more radical approach towards self-rule by the Lal Bal Pal triumvirate, Aurobindo Ghosh and V. O. Chidambaram Pillai.

# The final stages of the independence struggle in the 1920s were characterized by Congress' adoption of Mahatma Gandhi's policy of non-violence and civil disobedience. Some of the leading followers of Gandhi's ideology were Jawaharlal Nehru, Vallabhbhai Patel, Abdul Ghaffar Khan, Maulana Azad, and others. Intellectuals such as Rabindranath Tagore, Subramania Bharati, and Bankim Chandra Chattopadhyay spread patriotic awareness. Female leaders like Sarojini Naidu, Vijaya Lakshmi Pandit, Pritilata Waddedar, and Kasturba Gandhi promoted the emancipation of Indian women and their participation in the freedom struggle.

# Few leaders followed a more violent approach. This became especially popular after the Rowlatt Act, which permitted indefinite detention. The Act sparked protests across India, especially in the Punjab province, where they were violently suppressed in the Jallianwala Bagh massacre.

# The Indian independence movement was in constant ideological evolution. Essentially anti-colonial, it was supplemented by visions of independent, economic development with a secular, democratic, republican, and civil-libertarian political structure. After the 1930s, the movement took on a strong socialist orientation. It culminated in the Indian Independence Act 1947, which ended Crown suzerainty and partitioned British Raj into Dominion of India and Dominion of Pakistan.

# India remained a Crown Dominion until 26 January 1950, when the Constitution of India established the Republic of India. Pakistan remained a dominion until 1956 when it adopted its first constitution. In 1971, East Pakistan declared its own independence as Bangladesh.[1]"""

def gen_mcqs(text, num_gen):
    qlist = []
    while len(qlist) < num_gen:
        for r in (generate_questions_with_cohere(text, qtype='mcq')):
            curr = parse_question_response(r.text)
            if curr is not None:
                is_similar = False
                for q in qlist:
                    # print(json.dumps(q),"\n", " AND ","\n", json.dumps(curr))
                    score = similarity_score(json.dumps(curr), json.dumps(q))
                    # print("S Score: ", score)
                    # print("------------------------------------")
                    if score > 0.6:
                        is_similar = True
                        break

                if not is_similar:
                    qlist.append(curr)

            if len(qlist) == num_gen:
                break

    return qlist
    

def gen_tf(text, num_gen):
    qlist = []
    while len(qlist) < num_gen:
        for r in (generate_questions_with_cohere(text, qtype='tf')):
            curr = parse_tf_response(r.text)
            if curr is not None:
                is_similar = False
                for q in qlist:
                    # print(json.dumps(q),"\n", " AND ","\n", json.dumps(curr))
                    score = similarity_score(json.dumps(curr['question']), json.dumps(q['question']))
                    # print("S Score: ", score)
                    # print("------------------------------------")
                    if score > 0.6:
                        is_similar = True
                        break

                if not is_similar:
                    qlist.append(curr)

            if len(qlist) == num_gen:
                break

    return qlist

def gen_fib(text, num_gen):
    qlist = []
    while len(qlist) < num_gen:
        for r in (generate_questions_with_cohere(text, qtype='fib')):
            # print(r.text)
            curr = parse_fib_response(r.text)
            if curr is not None:
                is_similar = False
                for q in qlist:
                    # print(json.dumps(q),"\n", " AND ","\n", json.dumps(curr))
                    score = similarity_score(json.dumps(curr), json.dumps(q))
                    # print("S Score: ", score)
                    # print("------------------------------------")
                    if score > 0.6:
                        is_similar = True
                        break

                if not is_similar:
                    qlist.append(curr)

            if len(qlist) == num_gen:
                break

    return qlist

# print((generate_questions_with_cohere(trial_text, qtype='tf')))
# print((gen_fib(trial_text, 6)))
