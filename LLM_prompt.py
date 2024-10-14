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