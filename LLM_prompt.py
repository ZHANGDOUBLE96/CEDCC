# prompt for constructing coreference chains for targeted entity
def generate_prompt_for_Building_Coreference_Chains_withGivenEntity(sentence):
    msg = [
        {
        "role":"system",
        "content":"\nYou are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2021-09\nCurrent model: gpt-4\nLatex inline: \\(x^2\\) \nLatex block: $$e=mc^2$$\n\n"
        },
    {
    "role":"user",
    "content":f"""
        ### Task:
        You are provided with a sentence where some entities are marked with special tags ("</BEGIN>" and "<END/>"), while others are unmarked. Your task is to construct coreference chains for the entities of this sentence, based solely on the context provided within the sentence. Finally, output the coreference chains that include the marked entities.
        
        
        ### Output Requirements:
        Output the chains in JSON format, where each key represents a distinct coreference chain containing the related entities.
        
        

        ### Example 1
        **Input:**
        Sentence: "</BEGIN>Sarah<END/> visited the museum. She enjoyed the exhibits. Later, Sarah and her sister attended a workshop."
        
        **Output:**
        {{
        "Chain1": ["</BEGIN>Sarah<END/>", "She", "Sarah"]
        }}
        
        
        ### Example 2
        **Input:**
        Sentence: "The teacher said that </BEGIN>he<END/> would handle </BEGIN>it<END/> ."
        
        **Output:**
        {{
        "Chain1": ["The teacher","</BEGIN>he<END/>"],
        "Chain2": ["</BEGIN>it<END/>"],
        }}
        
        Now, please analyze the following sentence and output the result:\n
        SENTENCE: {sentence} \n\n
        
        """
        }
        ]
    return msg



# Our three stage Complete prompt 
def generate_prompt_for_Complete_step_by_step_step1(sentence,context_bdoy):
    msg = [
        {
        "role":"system",
        "content":"\nYou are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2021-09\nCurrent model: gpt-4\nLatex inline: \\(x^2\\) \nLatex block: $$e=mc^2$$\n\n"
        },
        {
        "role":"user",
        "content":f"""
        ### Task:
        You will receive a sentence with certain phrases surrounded by special markers "</BEGIN>" and "<END/>", along with the surrounding context of that sentence. For each marked phrase, you task is as follows:
        (1) Identify the context related to the marked phrase.
        (2) output the related context
        
        
        ### Output Requirements:
        (1) Only the related context are output, without any explanatory or introductory content!!!

        ### Example 1
        **Input:**
        Sentence: In the meeting, </BEGIN>he<END/> mentioned that the project was on schedule.
        Context: Today is a good day, Tom attended the meeting on time. In the meeting, he mentioned that the project was on schedule.
        **Output:**
        [Tom attended the meeting on time. In the meeting, he mentioned that the project was on schedule.]
        
        
        Now, please analyze the following sentence and its Context, and output the result:\n
        Sentence: {sentence} \n\n
        CONTEXT: {context_bdoy}
        """
        }
        ]
    return msg

# Our three stage Complete prompt 
def generate_prompt_for_Complete_step_by_step_step2(sentence,context_bdoy):
    msg = [
         {
        "role":"system",
        "content":"\nYou are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2021-09\nCurrent model: gpt-4\nLatex inline: \\(x^2\\) \nLatex block: $$e=mc^2$$\n\n"
        },
        {
        "role":"user",
        "content":f"""
            ### Task:
            You will receive a sentence with certain phrases surrounded by special markers “</BEGIN>” and “<END/>”, along with the surrounding context of that sentence. For each marked phrase, please provide a detailed explanation of what it refers to, using as much of the original wording from the context as possible.
            
            
            ### Output Requirements:
            (1) The output of each marked phrase should be in dict format, with each specially marked phrase and its corresponding entity (the corresponding keys are "NP" and "Value" respectively). The dictionaries corresponding to all phrases are placed in a list in the order in which they appear in the sentence.
            (2) Only the judgments are output, without any explanatory or introductory content!!!

            ### Example 1
            **Input:**
            Sentence: In the meeting, </BEGIN>he<END/> mentioned that the project was on schedule.
            Context: Tom attended the meeting on time. In the meeting, he mentioned that the project was on schedule.
            **Output:**
            [{{"NP": "he", "Value": "a person named Tom"}}]
            
            Now, please analyze the following sentence and its Context, and output the result:\n
            Sentence: {sentence} \n\n
            CONTEXT: {context_bdoy}
            """
            }
           ]
    return msg




#prompt for LLM_baseline
def generate_prompt_for_Predicting_and_Complete_with_direct_commands_OneGo(sentence,context_bdoy):
    msg = [
        {
        "role":"system",
        "content":"\nYou are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2021-09\nCurrent model: gpt-4\nLatex inline: \\(x^2\\) \nLatex block: $$e=mc^2$$\n\n"
        },
    {
    "role":"user",
    "content":
        f"""
        ### Task:
        You will receive a sentence and the context in which it is located. You first need to limit yourself to this sentence without considering its context, and find the phrases in this sentence that meet the following conditions: the object it refers to is not explicitly described in the sentence. 
        
        Then, you need to give a detailed explanation of the referents of these phrases based on the context of the sentence. 
        
        ### Output:
        (1) The output of each phrase and its referent should be in dict format (the corresponding keys are "NP" and "Value" respectively). The dictionaries corresponding to all phrases are placed in a list in the order in which they appear in the sentence.
        (2) Only the judgments are output, without any explanatory or introductory content!!!

        ### Example 1
        **Input:**
        Sentence: In the meeting, he mentioned that the project was on schedule.
        Context: Tom attended the meeting on time. In the meeting, he mentioned that the project was on schedule.
        **Output:**
        [{{"NP": "he", "Value": "a person named Tom"}}]
        
        Now, this is the Input: 
            Sentence: {sentence},
            Context: {context_bdoy},        
        """
        }
        ]
    return msg