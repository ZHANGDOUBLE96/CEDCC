from bs4 import BeautifulSoup
import html
import re
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
import copy
import time
import openai
import json
def clean_jupyter_markup(text):
    input_lines = []
    in_input_block = False  
    in_python_prompt = False  
    is_interactive = False 

    
    in_multiline_comment = False
    
    
    for line in text.split('\n'):
        if re.match(r"In\s*\[\d*\]:", line):
            in_input_block = True  
            in_python_prompt = False  
            is_interactive = True  
            try:
                code_part = line.split(':', 1)[1].strip()  
                input_lines.append(code_part)
            except IndexError:
                continue
            
        elif re.match(r"Out\s*\[\d*\]:", line):
            in_input_block = False  
        elif in_input_block:  
            if re.match(r"^\s*>>>", line):
                in_input_block = False  
                code_part = re.sub(r"^\s*>>>", "", line).strip()  
                input_lines.append(code_part)
                in_python_prompt = True  
            else:
                input_lines.append(line.strip())
        
        elif re.match(r"^\s*>>>", line):  
            code_part = re.sub(r"^\s*>>>", "", line).strip()  
            input_lines.append(code_part)
            in_python_prompt = True  
            is_interactive = True  
        elif in_python_prompt:  
            if re.match(r"^\s*\.\.\.", line): 
                code_part = re.sub(r"^\s*\.\.\.", "", line).strip()
                input_lines.append(code_part)
            else:
                in_python_prompt = False  
        
        elif not is_interactive:
            line = re.split(r'\s*#', line)[0].rstrip()
            
            if not re.match(r"^\s*\.\.\.", line) and line:
                input_lines.append(line)
    input_lines = [line for line in input_lines if line]

    return '\n'.join(input_lines)

def Extract_Codes_and_Data_From_XML(input_text):
    decoded_text = html.unescape(input_text)
    
    
    decoded_text_str = decoded_text.encode("utf-8").strip()
    extracted_codes = []
    
    soup = BeautifulSoup(decoded_text_str, "lxml")
    
    code_blocks = soup.find_all('code')

    for code in code_blocks:
        parent_tag = code.parent.name
        code_text = code.get_text()
        if parent_tag == 'pre':
            extracted_codes.append(code_text)
    return extracted_codes


def extract_identifiers(node):
    identifiers_list = []
    
    if node.type == 'identifier':
        identifiers_list.append(node.text.decode('utf8'))
    
    for child in node.children:
        identifiers_list.extend(extract_identifiers(child))
    
    identifiers_list = [item for item in identifiers_list if item]
    return identifiers_list   

def extract_subscript_variable_from_assignment(node, code_bytes):
    subscript_var_list = []
    if node.type == 'subscript':
        for child in node.children:
            if child.type == 'identifier':  
                start_byte = child.start_byte
                end_byte = child.end_byte
                variable_name = code_bytes[start_byte:end_byte].decode("utf8")
                subscript_var_list.append(variable_name)
    subscript_var_list = [item for item in subscript_var_list if item]
    return subscript_var_list

def extract_assigned_variables(node,code_bytes):
    assigned_variables = []
    if node.type == 'assignment':
        variable_node = node.child_by_field_name('left')
        if variable_node:
            assigned_variables.append(variable_node.text.decode('utf8'))
        
        assigned_variables.extend(extract_subscript_variable_from_assignment(variable_node, code_bytes))
        
    for child in node.children:
        assigned_variables.extend(extract_assigned_variables(child,code_bytes))
    return assigned_variables

def extract_function_parameters(node):
    function_parameters = []
    if node.type == 'function_definition':
        parameters_node = node.child_by_field_name('parameters')
        if parameters_node:
            for param in parameters_node.children:
                if param.type == 'identifier':
                    function_parameters.append(param.text.decode('utf8'))
    for child in node.children:
        function_parameters.extend(extract_function_parameters(child))
    
    function_parameters = [item for item in function_parameters if item]
    return function_parameters


def extract_target_variables(for_node):
    target_variables = []
    for child in for_node.children:
        if child.type == 'pattern_list':  
            for target in child.children:
                if target.type == 'identifier':  
                    target_variables.append(target.text.decode('utf8'))
    return target_variables

def collect_targets(root_node):
    target_identifier_in_for_statement = []  
    def find_for_statements(node):
        if node.type == 'for_statement':
            targets = extract_target_variables(node)
            target_identifier_in_for_statement.extend(targets)  
        for child in node.children:
            find_for_statements(child)

    find_for_statements(root_node)
    return target_identifier_in_for_statement  


def check_if_codes(snippet):
    python_keywords = [
        'def', 'class', 'for', 'while', 'if', 'elif', 'else', 'try', 'except', 
        'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'lambda',
        'and', 'or', 'not', 'is', 'in', '=', '==', '!=',  
        'pass', 'break', 'continue', 'global', 'nonlocal', 'assert', 'raise', 
        'del', 'print', 'input'
    ]
    

    pattern = r'\b(' + '|'.join(re.escape(keyword) for keyword in python_keywords) + r')\b'
    
 
    matches = re.findall(pattern, snippet)
    

    if matches:
        return True
    else:
        return False


def process_data_snippet(snippet):
    tokens = re.split(r'\s+|\n+', snippet)
    
    tokens = [token for token in tokens if token]
    
    def is_number_or_date(token):
        if re.match(r'^\d+(\.\d+)?$', token):
            return True
        if re.match(r'^\d{4}-\d{2}-\d{2}$', token):
            return True
        return False
    
    filtered_tokens = [token for token in tokens if not is_number_or_date(token)]
    
    unique_tokens = list(set(filtered_tokens))
    
    return unique_tokens

def contains_demonstrative(noun_phrase,demonstratives_list):
    return any(token.text.lower() in demonstratives_list for token in noun_phrase)


def filter_strings(strings):
    pattern = re.compile(r'^[a-zA-Z0-9_]+$')
    
    def is_valid_string(s):
        if pattern.match(s) and not re.match(r'^\d+$', s):
            return True
        return False
    
    filtered_strings = [s for s in strings if is_valid_string(s)]
    
    return filtered_strings


def output_identifiers_from_Codes(source_code="""def foo():
        if bar:
            baz()"""):
    identifiers_list = []
    assigned_variables = []
    function_parameters = []
    target_var_in_For_statement = []
    
    python_keywords = [
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 'break',
    'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'finally', 
    'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'nonlocal', 
    'not', 'or', 'pass', 'raise', 'return', 'try', 'while', 'with', 'yield'
    ]
    python_builtin_funcs = [
    'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes', 'callable', 'chr', 
    'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 'enumerate', 'eval', 
    'exec', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr', 'hash', 'help', 
    'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len', 'list', 'locals', 
    'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 
    'print', 'property', 'range', 'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 
    'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip', '__import__'
    ]
    
    
    
    PY_LANGUAGE = Language(tspython.language())

    parser = Parser(PY_LANGUAGE)

    code_bytes = bytes(source_code, "utf8")
    
    tree = parser.parse(code_bytes)

    root_node = tree.root_node
    
    
    if(root_node.has_error and not check_if_codes(source_code)):
        identifiers_list = process_data_snippet(source_code) 
        assigned_variables = copy.copy(identifiers_list)
    else:
        

        identifiers_list.extend(extract_identifiers(root_node))

        assigned_variables.extend(extract_assigned_variables(root_node,code_bytes))
        function_parameters.extend(extract_function_parameters(root_node))
        target_var_in_For_statement.extend(collect_targets(root_node))
        
        
        identifiers_list = [item.strip() for sublist in identifiers_list for item in sublist.split(",")]
        assigned_variables = [item.strip() for sublist in assigned_variables for item in sublist.split(",")]
        function_parameters = [item.strip() for sublist in function_parameters for item in sublist.split(",")]
    

        identifiers_list = [item for item in identifiers_list if item not in python_builtin_funcs]
        assigned_variables = [item for item in assigned_variables if item not in python_builtin_funcs]
        function_parameters = [item for item in function_parameters if item not in python_builtin_funcs]
        
        identifiers_list = [item for item in identifiers_list if item not in python_keywords]
        assigned_variables = [item for item in assigned_variables if item not in python_keywords]
        function_parameters = [item for item in function_parameters if item not in python_keywords]
        
        
        identifiers_list = [item for item in identifiers_list if item not in target_var_in_For_statement]
    
    identifiers_list = filter_strings(list(set(identifiers_list))) 
    assigned_variables = filter_strings(list(set(assigned_variables)))
    function_parameters = filter_strings(list(set(function_parameters)))
    
    
    return identifiers_list, assigned_variables, function_parameters

def process_string_by_adding_special_markers(input_string, index_list):
    filtered_list = []
    for i in range(len(index_list)):
        start_i, end_i = index_list[i]
        is_nested = False
        for j in range(len(index_list)):
            start_j, end_j = index_list[j]
            if i != j and start_j <= start_i and end_i <= end_j:
                is_nested = True
                break
        if not is_nested:
            filtered_list.append((start_i, end_i))
    
    filtered_list.sort(key=lambda x: x[0], reverse=True)

    for start, end in filtered_list:
        input_string = input_string[:start] + "</BEGIN>" + input_string[start:end] + "<END/>" + input_string[end:]
    
    return input_string


def gpt_api_recognize(message,api_key,api_url,model_type="gpt-4"):
    openai.api_key = api_key
    openai.api_base = api_url
    response = openai.ChatCompletion.create(
    model = "{}".format(model_type),
    messages=message,
    temperature=0.5,
    max_tokens=1000,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    )
    if(isinstance(response,str)):
        response = json.loads(response)
    return response

def send_request_with_retry(msg, api_key,api_url,model_type,max_retries=30, retry_interval=60):
    retries = 0
    while retries < max_retries:
        try:
            response = gpt_api_recognize(message=msg,api_key=api_key,api_url=api_url,model_type=model_type)
            return response
        except openai.error.RateLimitError:
            print(f"Rate limit exceeded. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
            retries += 1
        except openai.error.APIConnectionError:
            print(f"API connection error. Retrying in {retry_interval} seconds...")
            time.sleep(retry_interval)
            retries += 1
        except openai.error.OpenAIError as e:
            if '502 Bad Gateway' in str(e):
                print(f"Bad Gateway. Retrying in {retry_interval/2} seconds...")
                time.sleep(retry_interval/2)
                retries += 1
            else:
                print(f"An error occurred: {e}")
                break
    print("Max retries exceeded.")
    return None

def extract_json_from_LLM(sample_predict_result):
    try:
        if(isinstance(sample_predict_result,str)):
            if(sample_predict_result.find("```json")!=-1):
                start_index = sample_predict_result.find("```json")
                sample_predict_result = sample_predict_result[start_index:sample_predict_result.find("```",start_index+len("```json"))]
            sample_predict_result = sample_predict_result.replace("```json", "").replace("```", "").strip()
            sample_predict_result = json.loads(sample_predict_result)
        if(isinstance(sample_predict_result,list) or isinstance(sample_predict_result,dict)):
            return sample_predict_result
        else:
            return "error"
    except json.JSONDecodeError as e:
        return "error"

def extract_complete_context_from_LLM(sample_predict_result):
    try:
        if(isinstance(sample_predict_result,str)):
            if(sample_predict_result.find("```json")!=-1):
                start_index = sample_predict_result.find("```json")
                sample_predict_result = sample_predict_result[start_index:sample_predict_result.find("```",start_index+len("```json"))]
            sample_predict_result = sample_predict_result.replace("```json", "").replace("```", "").strip()

            start = sample_predict_result.find('[')
            end = sample_predict_result.rfind(']')
            

            if start != -1 and end != -1 and end > start:
                sample_predict_result =  sample_predict_result[start:end+1]
                sample_predict_result = json.loads(sample_predict_result)  
            else:
                return "error"

        if(isinstance(sample_predict_result,list) or isinstance(sample_predict_result,dict)):
            return sample_predict_result
        else:
            return "error"
    except json.JSONDecodeError as e:
        return "error"
