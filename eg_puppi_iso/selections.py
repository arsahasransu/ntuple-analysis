from python.selections import Selection

# Select for events with prompt gen electrons
gen_prompt_el_sel = [Selection('GenPromptE', 'isPrompt', lambda array: array.prompt == 2),
                     Selection('GenPromptTauToE', 'PromptTauToE', lambda array: array.prompt == 1)]