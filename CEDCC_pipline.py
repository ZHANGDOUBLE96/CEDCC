
import spacy
from spacy.tokenizer import Tokenizer
from utils import Extract_Codes_and_Data_From_XML,clean_jupyter_markup,output_identifiers_from_Codes
from utils import contains_demonstrative
import json
from LLM_prompt import generate_prompt_for_Building_Coreference_Chains_withGivenEntity
from utils import process_string_by_adding_special_markers
from utils import send_request_with_retry
from utils import extract_json_from_LLM

def load_spacy_processor():
    
    nlp = spacy.load("en_core_web_sm")
    
    nlp.tokenizer = Tokenizer(nlp.vocab, token_match=None)
    return nlp


def candidate_entity_selection(sample_sentence,context_body):
    key_words_list = ['he', 'she', 'it', 'they', 'him', 'her', 'them','this', 'that', 'these', 'those','my', 'your', 'his', 'her', 'its', 'our', 'their', 'mine', 'yours','what','such','above','below']
    
    context_code_body = context_body['question'] + context_body['accpeted_answer'] + context_body['other_answers'] + context_body['comments']
    
    all_code_Identifier_list = []
    all_code_Assigned_variables_list = []
    all_code_Function_parameters_list = []
    for cur_so_post in context_code_body:
        extracted_codes = Extract_Codes_and_Data_From_XML(cur_so_post)
        for cur_code_block in extracted_codes:
            cur_code_block = clean_jupyter_markup(cur_code_block)
            cur_code_identifiers,cur_code_assign_vars,cur_code_func_params = output_identifiers_from_Codes(source_code=cur_code_block)
            all_code_Identifier_list.extend(cur_code_identifiers)
            all_code_Assigned_variables_list.extend(cur_code_assign_vars)
            all_code_Function_parameters_list.extend(cur_code_func_params)
    related_code_Identifier_list = list(set(all_code_Identifier_list))
    related_code_Assigned_variables_list = list(set(all_code_Assigned_variables_list))
    related_code_function_parameters_list = list(set(all_code_Function_parameters_list))
    
    
    with open('API_elements.json', 'r') as file:
        loaded_API_elements_list = json.load(file)
    
    filtered_code_Assigned_variables_list = [item for item in related_code_Assigned_variables_list if item not in loaded_API_elements_list]
    
    candidate_entity_list = []
    nlp = load_spacy_processor()
    doc = nlp(sample_sentence)
    for noun_phrase in doc.noun_chunks:
        
        if(contains_demonstrative(noun_phrase,key_words_list)):
            candidate_entity_list.append([noun_phrase.text, (noun_phrase.start_char,noun_phrase.end_char)])
        core_word = noun_phrase.root
        core_word_lemma = core_word.text
        if('=' in core_word_lemma):
            core_word_lemma = core_word_lemma.split('=')[0].strip()
        if('[' in core_word_lemma):
            core_word_lemma = core_word_lemma.split('[')[0].strip()
        if(core_word_lemma in filtered_code_Assigned_variables_list):
            candidate_entity_list.append([noun_phrase.text, (noun_phrase.start_char,noun_phrase.end_char)])
    return candidate_entity_list

def predict_unclear_tokens_with_CorefChain_after_given_entity(sample_process_sentence,to_be_replace_for_predict_tokens):
    
    to_prompt_sentence = process_string_by_adding_special_markers(sample_process_sentence,to_be_replace_for_predict_tokens)
    msg = generate_prompt_for_Building_Coreference_Chains_withGivenEntity(to_prompt_sentence)
    
    response = send_request_with_retry(msg, api_key="",api_url="https://api.openai.com/v1",model_type="gpt-4-0613",max_retries=5, retry_interval=60)
    annotation_result = response["choices"][0]["message"]["content"]
    return annotation_result



if __name__=='__main__':
    sample_sentence = "We can use pd.melt to make the hour columns into one column with that value"
    post_id =  15433426
    accept_answer_body =  ["""
                            <p>I'm not the best at date manipulations, but maybe something like this:</p>

                        <pre><code>import pandas as pd
                        from datetime import timedelta

                        df = pd.read_csv("hourmelt.csv", sep=r"\s+")

                        df = pd.melt(df, id_vars=["Date"])
                        df = df.rename(columns={'variable': 'hour'})
                        df['hour'] = df['hour'].apply(lambda x: int(x.lstrip('h'))-1)

                        combined = df.apply(lambda x: 
                                            pd.to_datetime(x['Date'], dayfirst=True) + 
                                            timedelta(hours=int(x['hour'])), axis=1)

                        df['Date'] = combined
                        del df['hour']

                        df = df.sort("Date")
                        </code></pre>

                        <hr>

                        <p>Some explanation follows. </p>

                        <p>Starting from</p>

                        <pre><code>&
                        &
                        &
                        &
                        &
                                Date  h1  h2  h3  h4  h24
                        0  14.03.2013  60  50  52  49   73
                        1  14.04.2013   5   6   7   8    9
                        </code></pre>

                        <p>We can use <code>pd.melt</code> to make the hour columns into one column with that value:</p>

                        <pre><code>&
                        &
                        &
                                Date hour  value
                        0  14.03.2013   h1     60
                        1  14.04.2013   h1      5
                        2  14.03.2013   h2     50
                        3  14.04.2013   h2      6
                        4  14.03.2013   h3     52
                        5  14.04.2013   h3      7
                        6  14.03.2013   h4     49
                        7  14.04.2013   h4      8
                        8  14.03.2013  h24     73
                        9  14.04.2013  h24      9
                        </code></pre>

                        <p>Get rid of those <code>h</code>s:</p>

                        <pre><code>&
                        &
                                Date  hour  value
                        0  14.03.2013     0     60
                        1  14.04.2013     0      5
                        2  14.03.2013     1     50
                        3  14.04.2013     1      6
                        4  14.03.2013     2     52
                        5  14.04.2013     2      7
                        6  14.03.2013     3     49
                        7  14.04.2013     3      8
                        8  14.03.2013    23     73
                        9  14.04.2013    23      9
                        </code></pre>

                        <p>Combine the two columns as a date:</p>

                        <pre><code>&
                        &
                        0    2013-03-14 00:00:00
                        1    2013-04-14 00:00:00
                        2    2013-03-14 01:00:00
                        3    2013-04-14 01:00:00
                        4    2013-03-14 02:00:00
                        5    2013-04-14 02:00:00
                        6    2013-03-14 03:00:00
                        7    2013-04-14 03:00:00
                        8    2013-03-14 23:00:00
                        9    2013-04-14 23:00:00
                        </code></pre>

                        <p>Reassemble and clean up:</p>

                        <pre><code>&
                        &
                        &
                        &
                                        Date  value
                        0 2013-03-14 00:00:00     60
                        2 2013-03-14 01:00:00     50
                        4 2013-03-14 02:00:00     52
                        6 2013-03-14 03:00:00     49
                        8 2013-03-14 23:00:00     73
                        1 2013-04-14 00:00:00      5
                        3 2013-04-14 01:00:00      6
                        5 2013-04-14 02:00:00      7
                        7 2013-04-14 03:00:00      8
                        9 2013-04-14 23:00:00      9
                        </code></pre>

    """]
    question_body = ["""
                    <p>I have the following dataframe read in from a .csv file with the "Date" column being the index. The days are in the rows and the columns show the values for the hours that day.</p>

                <pre><code>&
                &
                </code></pre>

                <p>I would like to arrange it like this, so that there is one index column with the date/time and one column with the values in a sequence</p>

                <pre><code>&
                &
                &
                &
                &
                &
                &
                &
                &
                </code></pre>

                <p>I was trying it by using two loops to go through the dataframe.
                Is there an easier way to do this in pandas?</p>

    """]
    
    other_answer_body_list = ["""
                              <p>You could always grab the hourly data_array and flatten it. You would generate a new DatetimeIndex with hourly freq. </p>

                            <pre><code>df = df.asfreq('D')
                            hourly_data = df.values[:, :]
                            new_ind = pd.date_range(start=df.index[0], freq="H", periods=len(df) * 24)
                            
                            s = pd.Series(hourly_data.flatten(), index=new_ind)
                            </code></pre>

                            <p>I'm assuming that read_csv is parsing the 'Date' column and making it the index. We change to frequency of 'D' so that the <code>new_ind</code> lines up correctly if you have missing days. The missing days will be filled with <code>np.nan</code> which you can drop with <code>s.dropna()</code>.</p>

                            <p><a href="http://nbviewer.ipython.org/5183385" rel="nofollow">notebook link</a></p>
                              """]
    comment_body_list = ["""
                         Nice solution! You could combine the `df['hour'].apply(...)` and `combined = ...` lines into `df['Date'] += df['hour'].apply(lambda x: timedelta(hours=int(x.lstrip('h'))-1))`.
                         """,
                         """
                         Great solution. Thanks a lot. I have just set Date as the index and it works perfectly.                                                >df = df.set_index('Date')
                         """]
    
    context_body = {
        'question':question_body,
        'accpeted_answer':accept_answer_body,
        'other_answers':other_answer_body_list,
        'comments':comment_body_list
    }
    candidate_entity_list = candidate_entity_selection(sample_sentence,context_body)
    if(len(candidate_entity_list)>0):
        raw_CorefChain_result = predict_unclear_tokens_with_CorefChain_after_given_entity(sample_sentence,[element[1] for element in candidate_entity_list])
        CorefChain_result = extract_json_from_LLM(raw_CorefChain_result)
    
    
    candidate_entity_tokens = ["</BEGIN>{}<END/>".format(element[0]) for element in candidate_entity_list]
    unclear_tokens_indices_list = [] 
    for ref_entity in candidate_entity_list:
        ref_entity_token = "</BEGIN>{}<END/>".format(ref_entity[0])
        found_in_chain = False
        all_in_list = True
        for chain_index,chain_value in CorefChain_result.items():
            if ref_entity_token in chain_value:
                found_in_chain = True
                for element in chain_value:
                    if element not in candidate_entity_tokens:
                        all_in_list = False
                        break
                if all_in_list:
                    break
        if all_in_list:
            unclear_tokens_indices_list.append(ref_entity)
    
    
    print(unclear_tokens_indices_list)